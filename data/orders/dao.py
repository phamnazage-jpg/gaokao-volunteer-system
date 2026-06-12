"""订单 DAO 数据访问层 (T4.2)

提供订单表的 CRUD、事务、加密字段透明处理、6 态状态机守护的转换写入。

设计原则
--------

1. **加密透明化**：API 入口接收 ``Order`` dataclass（明文 PII），
   DAO 负责落盘前加密、读取后解密，调用方无需关心 ``*_enc`` 字段。
2. **状态机守护**：所有状态转换走 ``transition_status()``，单事务内
   写 ``orders.status`` + ``order_status_history``；非法转换抛
   :class:`InvalidStateTransition` 并回滚。
3. **事务显式**：默认每方法一次 ``commit``；批量操作走 ``transaction()``
   上下文管理器（异常时统一 ``rollback``）。
4. **行工厂统一**：DAO 内部强制 ``sqlite3.Row`` 工厂，调用方传入的
   ``row_factory`` 不会被污染（使用前保存 / 使用后恢复）。
5. **去重路径**：``(source, external_id)`` 唯一索引上的 ``upsert_by_external_id()``
   接管 :mod:`data.channel_sync.dao_extension` 的同名函数（向下兼容）。

依赖
----

- :class:`data.orders.models.Order`
- :func:`data.orders.schema.apply_schema`
- :mod:`data.orders.state_machine`
- :func:`data.orders.crypto.encrypt` / :func:`decrypt`

替代与回滚
----------

- :class:`data.channel_sync.dao_extension.UpsertResult` 与
  :func:`data.channel_sync.dao_extension.upsert_by_external_id` 由本模块的
  :class:`UpsertResult` / :meth:`OrdersDAO.upsert_by_external_id` 取代。
  T8.1 现存调用迁移到本 DAO 后即可删除 dao_extension.py。
"""

from __future__ import annotations

import contextlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, List, Optional, Union

from .models import Order, utc_now_iso
from .schema import apply_schema
from .state_machine import (
    InvalidStateTransition,
    assert_valid_transition,
    is_known_status,
)


# ---------------------------------------------------------------------------
# 异常与结果类型
# ---------------------------------------------------------------------------


class OrderNotFound(LookupError):
    """按主键或唯一键查询订单时未命中。"""


class DuplicateOrder(ValueError):
    """尝试插入违反唯一约束的订单（手机号 hash 或 external_id 冲突）。"""


@dataclass
class UpsertResult:
    """upsert_by_external_id 的返回结构。

    字段含义:
    - ``action='inserted'``：原 DB 不存在该 ``(source, external_id)``，已新建。
    - ``action='updated'``：已存在且状态可推进，已更新 status / status_updated_at
      并写入一条 status_history。
    - ``action='unchanged'``：已存在且状态未变，未写入。
    - ``action='illegal_transition'``：已存在但状态转换非法（未写入），
      调用方应降级为 ``decision='rejected'``。
    """

    order_id: str
    action: str  # 'inserted' | 'updated' | 'unchanged' | 'illegal_transition'
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    error: Optional[str] = None


@dataclass
class StatusChange:
    """状态历史记录（来自 order_status_history 表）。"""

    id: int
    order_id: str
    from_status: Optional[str]
    to_status: str
    actor: Optional[str]
    reason: Optional[str]
    changed_at: str


# ---------------------------------------------------------------------------
# 内部常量
# ---------------------------------------------------------------------------

# 与 schema.py 对齐的 orders 表可写列清单。
# 加密字段：customer_phone_enc / candidate_id_card_enc 来自 Order.to_db_row()。
_WRITABLE_COLUMNS: tuple[str, ...] = (
    "id",
    "source",
    "external_id",
    "service_version",
    "amount_cents",
    "status",
    "status_updated_at",
    "customer_name",
    "customer_phone_enc",
    "customer_phone_hash",
    "customer_wechat",
    "candidate_name",
    "candidate_id_card_enc",
    "candidate_province",
    "candidate_score",
    "candidate_rank",
    "candidate_subjects",
    "candidate_interests",
    "candidate_strong_subjects",
    "candidate_weak_subjects",
    "candidate_family",
    "assigned_consultant",
    "plan_file",
    "audit_report",
    "pdf_path",
    "created_at",
    "paid_at",
    "started_at",
    "delivered_at",
    "completed_at",
    "notes",
    "tags",
    "upgrade_from",
)

# 历史阶段字段映射：状态进入时自动置位的 timestamp 字段。
# 状态 → timestamp 字段名（COALESCE 写入：已有则保留）。
_STATUS_TIMESTAMP: dict[str, str] = {
    "paid": "paid_at",
    "serving": "started_at",
    "delivered": "delivered_at",
    "completed": "completed_at",
}


# ---------------------------------------------------------------------------
# DAO 主类
# ---------------------------------------------------------------------------


class OrdersDAO:
    """订单表 DAO。

    两种初始化方式：

    1. 接管已建立的连接::

         conn = apply_schema("/path/orders.db")
         dao = OrdersDAO(conn)

       DAO 不会关闭 conn，调用方负责。

    2. 接管数据库路径::

         with OrdersDAO.connect("/path/orders.db") as dao:
             dao.create(order)

       退出上下文时自动 commit/close。
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._tx_depth = 0  # 嵌套事务深度（0 = 顶层）
        # DAO 假设 conn 已启用 foreign_keys；不强制重设（调用方控制）。

    # ------------------------------------------------------------------
    # 构造/连接管理
    # ------------------------------------------------------------------

    @classmethod
    def connect(
        cls,
        db_path: Union[str, Path],
        *,
        row_factory: bool = True,
    ) -> "OrdersDAO":
        """按路径建立连接并应用 schema（幂等），返回 DAO。

        ``row_factory=True`` 时强制设为 ``sqlite3.Row``，便于 ``dict(row)``。

        用法::

            with OrdersDAO.connect("data/orders.db") as dao:
                dao.create(order)
        """
        conn = apply_schema(db_path)
        if row_factory:
            conn.row_factory = sqlite3.Row
        return cls(conn)

    @property
    def conn(self) -> sqlite3.Connection:
        """暴露底层连接（只读引用，调用方不应自行 commit/close）。"""
        return self._conn

    def close(self) -> None:
        """关闭底层连接。"""
        self._conn.close()

    @contextlib.contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """事务上下文。

        进入时自动 ``BEGIN``，异常时 ``ROLLBACK`` 并重新抛出；
        正常退出时 ``COMMIT``。

        嵌套语义: 内部 ``create()`` / ``update()`` / ``transition_status()``
        自身会再调 ``transaction()``。当外层已在事务中时,内层不再开新事务,
        直接复用外层 — 任何一层的异常都会触发外层回滚。这是经典的 SAVEPOINT
        简化版(无部分回滚),适合本 DAO 的写多读少场景。

        用法::

            with dao.transaction() as conn:
                conn.execute(...)
                conn.execute(...)  # 同事务
        """
        self._tx_depth += 1
        try:
            if self._tx_depth == 1:
                # 顶层：依赖 sqlite3 的隐式 BEGIN，由 commit/rollback 终止
                yield self._conn
                self._conn.commit()
            else:
                # 嵌套：复用外层事务，不 commit/rollback
                yield self._conn
        except Exception:
            if self._tx_depth == 1:
                self._conn.rollback()
            raise
        finally:
            self._tx_depth -= 1

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    @contextlib.contextmanager
    def _row_factory_ctx(self) -> Iterator[None]:
        """临时把 conn.row_factory 设为 sqlite3.Row，退出时恢复。"""
        prior = self._conn.row_factory
        self._conn.row_factory = sqlite3.Row
        try:
            yield
        finally:
            self._conn.row_factory = prior

    @staticmethod
    def _coerce_for_db(key: str, value: Any) -> Any:
        """保证 tags / candidate_subjects 落盘为 JSON 字符串。"""
        if key in ("tags", "candidate_subjects") and isinstance(value, (list, tuple)):
            return json.dumps(list(value), ensure_ascii=False)
        return value

    def _row_to_order(self, row: sqlite3.Row) -> Order:
        """sqlite3.Row → Order（解密 + JSON 解析由 from_db_row 负责）。"""
        return Order.from_db_row(dict(row))

    def _select_columns(self) -> str:
        return ", ".join(_WRITABLE_COLUMNS)

    # ------------------------------------------------------------------
    # 写入：create / update
    # ------------------------------------------------------------------

    def create(
        self,
        order: Order,
        *,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Order:
        """插入新订单，并写入首条 status_history（from=None → status）。

        - 重复主键 / 重复 external_id 抛 :class:`DuplicateOrder`。
        - 重复 phone_hash（非唯一索引，仅用于查询）允许 — 同一手机号
          下不同省份/年份可以下多单。

        返回: 写入后的 Order（数据库回读，字段已对齐 SQLite 默认值）。
        """
        db_row = order.to_db_row()
        # 防御：过滤掉 schema 中不存在的列
        valid_cols = set(_WRITABLE_COLUMNS)
        db_row = {
            k: self._coerce_for_db(k, v) for k, v in db_row.items() if k in valid_cols
        }
        # 落盘 timestamp 不能为空
        if not db_row.get("status_updated_at"):
            db_row["status_updated_at"] = utc_now_iso()
        if not db_row.get("created_at"):
            db_row["created_at"] = utc_now_iso()

        cols = list(db_row.keys())
        placeholders = ",".join("?" for _ in cols)
        values = [db_row[c] for c in cols]

        with self.transaction():
            try:
                self._conn.execute(
                    f"INSERT INTO orders ({','.join(cols)}) VALUES ({placeholders})",
                    values,
                )
            except sqlite3.IntegrityError as exc:
                msg = str(exc).lower()
                if "unique" in msg or "primary key" in msg:
                    raise DuplicateOrder(
                        f"订单已存在: id={order.id} source={order.source} external_id={order.external_id} ({exc})"
                    ) from exc
                raise
            self._insert_status_history(
                order_id=order.id,
                from_status=None,
                to_status=order.status,
                actor=actor or "dao_create",
                reason=reason or "create",
            )
            # 读回行（确保返回字段与 DB 对齐）
            created_id = order.id
            with self._row_factory_ctx():
                row = self._conn.execute(
                    f"SELECT {self._select_columns()} FROM orders WHERE id=?",
                    (created_id,),
                ).fetchone()
        return self._row_to_order(row)

    def update(
        self,
        order_id: str,
        updates: dict[str, Any],
        *,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Order:
        """按主键更新订单业务字段（非 status 字段）。

        适用字段：customer_name / customer_wechat / candidate_name /
        candidate_province / candidate_score / candidate_rank /
        candidate_subjects / candidate_interests / candidate_strong_subjects /
        candidate_weak_subjects / candidate_family / assigned_consultant /
        plan_file / audit_report / pdf_path / notes / tags / amount_cents /
        service_version / external_id。

        **禁止**通过本方法改 ``status`` —— 改状态请走 :meth:`transition_status`，
        以保证状态机校验和历史写入。

        - 不存在抛 :class:`OrderNotFound`。
        - 重复 external_id 抛 :class:`DuplicateOrder`。

        返回: 更新后的 Order。
        """
        if "status" in updates:
            raise ValueError("禁止通过 update() 改 status；请使用 transition_status()")

        allowed = set(_WRITABLE_COLUMNS) - {"id", "status", "status_updated_at"}
        bad = set(updates) - allowed
        if bad:
            raise ValueError(
                f"update() 不允许字段: {sorted(bad)}（仅业务字段，不含 status/timestamp）"
            )

        with self.transaction():
            with self._row_factory_ctx():
                row = self._conn.execute(
                    "SELECT id FROM orders WHERE id=?",
                    (order_id,),
                ).fetchone()
            if row is None:
                raise OrderNotFound(f"订单不存在: {order_id}")

            set_clauses: list[str] = []
            values: list[Any] = []
            for k, v in updates.items():
                set_clauses.append(f"{k}=?")
                values.append(self._coerce_for_db(k, v))
            # 业务字段更新不影响 status_updated_at；只有 transition_status 才动
            values.append(order_id)
            try:
                self._conn.execute(
                    f"UPDATE orders SET {','.join(set_clauses)} WHERE id=?",
                    values,
                )
            except sqlite3.IntegrityError as exc:
                msg = str(exc).lower()
                if "unique" in msg:
                    raise DuplicateOrder(
                        f"订单更新违反唯一约束: id={order_id} ({exc})"
                    ) from exc
                raise
            with self._row_factory_ctx():
                row = self._conn.execute(
                    f"SELECT {self._select_columns()} FROM orders WHERE id=?",
                    (order_id,),
                ).fetchone()
        return self._row_to_order(row)

    # ------------------------------------------------------------------
    # 状态转换
    # ------------------------------------------------------------------

    def transition_status(
        self,
        order_id: str,
        to_status: str,
        *,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Order:
        """状态机守护的状态转换。

        流程（单事务）:

        1. 读现状 ``SELECT status FROM orders WHERE id=?``
        2. ``assert_valid_transition(from, to)`` 校验；非法抛
           :class:`InvalidStateTransition` 并回滚
        3. ``UPDATE orders SET status=?, status_updated_at=?, <status timestamp>=COALESCE(?, ?)``
        4. ``INSERT INTO order_status_history(from, to, actor, reason)``
        5. 读回返回

        返回: 转换后的 Order。
        """
        if not is_known_status(to_status):
            raise InvalidStateTransition(f"未知目标状态: {to_status!r}")

        with self.transaction():
            with self._row_factory_ctx():
                row = self._conn.execute(
                    "SELECT status FROM orders WHERE id=?",
                    (order_id,),
                ).fetchone()
            if row is None:
                raise OrderNotFound(f"订单不存在: {order_id}")
            from_status = row["status"]
            # 状态机校验（非法时抛 InvalidStateTransition）
            assert_valid_transition(from_status, to_status)

            now_iso = utc_now_iso()
            # 对应时间戳字段：COALESCE(原值, 新值) — 已有则保留
            ts_col = _STATUS_TIMESTAMP.get(to_status)
            if ts_col is not None:
                self._conn.execute(
                    f"""
                    UPDATE orders SET
                        status=?,
                        status_updated_at=?,
                        {ts_col} = COALESCE({ts_col}, ?)
                    WHERE id=?
                    """,
                    (to_status, now_iso, now_iso, order_id),
                )
            else:
                # refunded / pending 等没有专用时间戳
                self._conn.execute(
                    """
                    UPDATE orders SET
                        status=?,
                        status_updated_at=?
                    WHERE id=?
                    """,
                    (to_status, now_iso, order_id),
                )

            self._insert_status_history(
                order_id=order_id,
                from_status=from_status,
                to_status=to_status,
                actor=actor or "dao_transition",
                reason=reason,
                changed_at=now_iso,
            )
            with self._row_factory_ctx():
                row = self._conn.execute(
                    f"SELECT {self._select_columns()} FROM orders WHERE id=?",
                    (order_id,),
                ).fetchone()
        return self._row_to_order(row)

    def _insert_status_history(
        self,
        *,
        order_id: str,
        from_status: Optional[str],
        to_status: str,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
        changed_at: Optional[str] = None,
    ) -> int:
        """插入一条 order_status_history 记录，返回 rowid。

        不 commit —— 由外层 transaction() 统一提交。
        """
        if changed_at is None:
            changed_at = utc_now_iso()
        cur = self._conn.execute(
            """
            INSERT INTO order_status_history(
                order_id, from_status, to_status, actor, reason, changed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (order_id, from_status, to_status, actor, reason, changed_at),
        )
        return int(cur.lastrowid or 0)

    def get_status_history(self, order_id: str) -> List[StatusChange]:
        """读订单完整状态历史（按 changed_at 升序）。"""
        with self._row_factory_ctx():
            rows = self._conn.execute(
                """
                SELECT id, order_id, from_status, to_status, actor, reason, changed_at
                FROM order_status_history
                WHERE order_id=?
                ORDER BY changed_at ASC, id ASC
                """,
                (order_id,),
            ).fetchall()
        return [
            StatusChange(
                id=int(r["id"]),
                order_id=r["order_id"],
                from_status=r["from_status"],
                to_status=r["to_status"],
                actor=r["actor"],
                reason=r["reason"],
                changed_at=r["changed_at"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # 查询：get / list / find
    # ------------------------------------------------------------------

    def get(self, order_id: str) -> Order:
        """按主键读取订单（解密 PII）。不存在抛 :class:`OrderNotFound`。"""
        with self._row_factory_ctx():
            row = self._conn.execute(
                f"SELECT {self._select_columns()} FROM orders WHERE id=?",
                (order_id,),
            ).fetchone()
        if row is None:
            raise OrderNotFound(f"订单不存在: {order_id}")
        return self._row_to_order(row)

    def get_by_external_id(self, source: str, external_id: str) -> Optional[Order]:
        """按 (source, external_id) 查询；找不到返回 None。"""
        with self._row_factory_ctx():
            row = self._conn.execute(
                f"SELECT {self._select_columns()} FROM orders "
                "WHERE source=? AND external_id=? LIMIT 1",
                (source, external_id),
            ).fetchone()
        return self._row_to_order(row) if row is not None else None

    def find_by_phone(self, phone: str) -> List[Order]:
        """按手机号 hash 查询（去重 / 客户识别用），返回全部匹配。

        phone 接受明文；DAO 内部按 SHA-256 hash 查询。
        """
        from .crypto import hash_for_index

        with self._row_factory_ctx():
            rows = self._conn.execute(
                f"SELECT {self._select_columns()} FROM orders "
                "WHERE customer_phone_hash=? ORDER BY created_at DESC",
                (hash_for_index(phone),),
            ).fetchall()
        return [self._row_to_order(r) for r in rows]

    def list(
        self,
        *,
        status: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Order]:
        """按筛选条件列订单（默认按 created_at DESC）。

        - ``status`` 必须是已知 6 态之一；传未知值抛 :class:`ValueError`。
        - ``limit`` 取值 1..1000；越界抛 :class:`ValueError`。
        - ``offset`` ≥ 0。
        """
        if status is not None and not is_known_status(status):
            raise ValueError(f"未知 status: {status!r}")
        if not (1 <= limit <= 1000):
            raise ValueError(f"limit 越界 (1..1000): {limit}")
        if offset < 0:
            raise ValueError(f"offset 不能为负: {offset}")

        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            clauses.append("status=?")
            params.append(status)
        if source is not None:
            clauses.append("source=?")
            params.append(source)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = (
            f"SELECT {self._select_columns()} FROM orders "
            f"{where} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])

        with self._row_factory_ctx():
            rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_order(r) for r in rows]

    def count(
        self, *, status: Optional[str] = None, source: Optional[str] = None
    ) -> int:
        """统计订单数（同样支持 status / source 过滤）。"""
        if status is not None and not is_known_status(status):
            raise ValueError(f"未知 status: {status!r}")
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            clauses.append("status=?")
            params.append(status)
        if source is not None:
            clauses.append("source=?")
            params.append(source)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        row = self._conn.execute(
            f"SELECT COUNT(*) AS n FROM orders {where}",
            params,
        ).fetchone()
        # COUNT 总是返回 1 行；防御性 default
        return int(row[0] if row else 0)

    def stats_by_status(self) -> dict[str, int]:
        """按 status 分组统计订单数（含 0 计数的完整 6 态）。"""
        rows = self._conn.execute(
            "SELECT status, COUNT(*) AS n FROM orders GROUP BY status"
        ).fetchall()
        result: dict[str, int] = {
            s: 0
            for s in (
                "pending",
                "paid",
                "serving",
                "delivered",
                "completed",
                "refunded",
            )
        }
        for r in rows:
            # 允许 sqlite3.Row / tuple 两种形态
            status_key = r["status"] if hasattr(r, "keys") else r[0]
            count_val = r["n"] if hasattr(r, "keys") else r[1]
            if status_key in result:
                result[status_key] = int(count_val)
        return result

    # ------------------------------------------------------------------
    # 幂等 upsert（与 T8.1 dao_extension 对齐）
    # ------------------------------------------------------------------

    def upsert_by_external_id(
        self,
        order: Order,
        *,
        actor: str = "channel_sync",
        reason: Optional[str] = None,
    ) -> UpsertResult:
        """按 (source, external_id) 唯一索引写入或更新订单。

        行为（与 :mod:`data.channel_sync.dao_extension.upsert_by_external_id` 对齐）:

        - **external_id 缺失** → ``action='illegal_transition'`` + error
        - **不存在** → 插入新行 + 写 status_history(from=None → status)
        - **已存在且状态不变** → ``action='unchanged'``，不写 status_history
        - **已存在且状态可推进** → 更新 status / status_updated_at + 写 status_history
        - **已存在但状态非法转换** → ``action='illegal_transition'`` + error

        返回: :class:`UpsertResult`。
        """
        if not order.external_id:
            return UpsertResult(
                order_id=order.id,
                action="illegal_transition",
                error="external_id 缺失，无法做幂等 upsert",
            )

        # 1) 查重
        with self._row_factory_ctx():
            row = self._conn.execute(
                "SELECT * FROM orders WHERE source=? AND external_id=? LIMIT 1",
                (order.source, order.external_id),
            ).fetchone()

        if row is None:
            # INSERT — 沿用调用方传入的 reason/actor
            try:
                created = self.create(order, actor=actor, reason=reason)
            except DuplicateOrder as exc:
                return UpsertResult(
                    order_id=order.id,
                    action="illegal_transition",
                    error=f"重复订单: {exc}",
                )
            return UpsertResult(
                order_id=created.id,
                action="inserted",
                old_status=None,
                new_status=created.status,
            )

        # 2) 已存在：判断状态转换
        existing = self._row_to_order(row)
        old_status = existing.status
        if old_status == order.status:
            return UpsertResult(
                order_id=existing.id,
                action="unchanged",
                old_status=old_status,
                new_status=order.status,
            )
        try:
            assert_valid_transition(old_status, order.status)
        except InvalidStateTransition as exc:
            return UpsertResult(
                order_id=existing.id,
                action="illegal_transition",
                old_status=old_status,
                new_status=order.status,
                error=str(exc),
            )

        # 3) 合法推进：走 transition_status
        self.transition_status(
            existing.id,
            order.status,
            actor=actor,
            reason=reason or f"upsert_{order.source}",
        )
        return UpsertResult(
            order_id=existing.id,
            action="updated",
            old_status=old_status,
            new_status=order.status,
        )

    # ------------------------------------------------------------------
    # 删除（保留 — 业务上极少使用，但测试 + GDPR 流程可能需要）
    # ------------------------------------------------------------------

    def delete(self, order_id: str, *, hard: bool = False) -> bool:
        """删除订单。

        - ``hard=False``（默认）：仅删除订单行，order_status_history
          由 ``ON DELETE CASCADE`` 自动清理。**该模式用于业务侧强制
          删除（如恶意订单）**；请注意：已加密的 PII 字段随行一起
          消失，状态历史同样消失。
        - ``hard=True``：当前等价于 ``hard=False``；预留 ``PRAGMA
          secure_delete`` 配置接口。
        - 不存在返回 False；成功删除返回 True。

        注意：状态机不提供"删除"操作 — 这是物理删除，不会写 status_history。
        如需审计可改用 :class:`DataDeletionAudit` 单独的审计表。
        """
        del hard  # 当前未使用 — 预留
        with self.transaction():
            cur = self._conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __enter__(self) -> "OrdersDAO":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()


__all__ = [
    "OrdersDAO",
    "UpsertResult",
    "StatusChange",
    "OrderNotFound",
    "DuplicateOrder",
]
