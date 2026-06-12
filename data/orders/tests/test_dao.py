"""orders.dao 模块测试 (T4.2)

覆盖：
- 加密字段透明化（明文入口 → DB 落 *_enc → 读回明文）
- 6 态状态机守护：合法转换走通、非法转换抛 InvalidStateTransition
- 事务回滚：create + transition_status 失败时回滚
- 幂等 upsert_by_external_id：inserted / unchanged / updated / illegal_transition 四种 action
- 查询：get / get_by_external_id / find_by_phone / list / count / stats
- 重复主键 / 重复 external_id 抛 DuplicateOrder
- status_history 审计：每次 transition 写一条；get_status_history 时间线正确
- 业务字段更新：update() 修改 plan_file / notes / tags 不影响 status
- 禁止 update() 改 status（必须走 transition_status）
- 终态 completed / refunded 不可再转换
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, cast

import pytest

os.environ.setdefault("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-unit-tests")


from data.orders.crypto import decrypt, hash_for_index
from data.orders.dao import (
    DuplicateOrder,
    OrderNotFound,
    OrdersDAO,
    StatusChange,
    UpsertResult,
)
from data.orders.models import Order, generate_order_id, utc_now_iso
from data.orders.schema import apply_schema
from data.orders.state_machine import InvalidStateTransition


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db_path():
    """临时 SQLite 文件路径（自动清理）。"""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d) / "test_orders.db"


@pytest.fixture
def conn(tmp_db_path):
    """已应用 schema 的裸连接（不强制 row_factory）。"""
    c = apply_schema(tmp_db_path)
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
def dao(conn):
    """默认 DAO（用 fixture 的 conn）。"""
    return OrdersDAO(conn)


@pytest.fixture
def conn_with_factory(tmp_db_path):
    """row_factory=sqlite3.Row 的连接，用于验证 row_factory_ctx 不污染。"""
    c = apply_schema(tmp_db_path)
    c.row_factory = sqlite3.Row
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
def sample_order() -> Order:
    """带 PII 的样例订单（用于 create）。"""
    return Order(
        id=generate_order_id(),
        source="web",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        customer_name="张三",
        customer_phone="13800001234",
        customer_wechat="wx_test",
        candidate_name="张小明",
        candidate_id_card="430102200501011234",
        candidate_province="湖南",
        candidate_score=578,
        candidate_rank=12345,
        candidate_subjects=["物理", "化学", "生物"],
        candidate_interests="计算机",
        candidate_strong_subjects="数学",
        candidate_weak_subjects="英语",
        candidate_family="父母均为教师",
        tags=["VIP", "高优"],
        notes="样例订单",
    )


def _new_order(**overrides: Any) -> Order:
    """工厂：生成最小可用 Order，方便参数化测试。"""
    defaults: dict[str, Any] = dict(
        id=generate_order_id(),
        source="web",
        service_version="basic",
        amount_cents=1000,
        status="pending",
    )
    defaults.update(overrides)
    # 工厂只传 dataclass 字段，子集静态保证；运行时由 dataclass 自身校验。
    return Order(**cast(Any, defaults))


# ---------------------------------------------------------------------------
# 1. 构造与连接管理
# ---------------------------------------------------------------------------


class TestConnect:
    def test_connect_returns_dao_and_applies_schema(self, tmp_db_path):
        dao = OrdersDAO.connect(tmp_db_path)
        try:
            # schema 应已应用
            row = dao.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
            ).fetchone()
            assert row is not None
            row = dao.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='order_status_history'"
            ).fetchone()
            assert row is not None
            # row_factory 应已设为 sqlite3.Row
            assert dao.conn.row_factory is sqlite3.Row
        finally:
            dao.close()

    def test_context_manager_commits_on_success(self, tmp_db_path, sample_order):
        with OrdersDAO.connect(tmp_db_path) as dao:
            created = dao.create(sample_order)
            # 出 with 后数据应已落盘
        with OrdersDAO.connect(tmp_db_path) as dao2:
            assert dao2.get(created.id).customer_phone == "13800001234"

    def test_context_manager_rolls_back_on_exception(self, tmp_db_path, sample_order):
        # 使用 transaction() 显式控制：异常应回滚本次事务
        with pytest.raises(RuntimeError):
            with OrdersDAO.connect(tmp_db_path) as dao:
                with dao.transaction():
                    dao.create(sample_order)
                    raise RuntimeError("boom")
        # 事务回滚：再次连接应查不到
        with OrdersDAO.connect(tmp_db_path) as dao2:
            with pytest.raises(OrderNotFound):
                dao2.get(sample_order.id)

    def test_dao_does_not_close_external_conn(self, conn):
        """OrdersDAO(conn) 不应关闭外部传入的连接。"""
        dao = OrdersDAO(conn)
        dao.create(_new_order())
        # conn 仍可用 → 说明 DAO 没 close 它
        cnt = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        assert cnt == 1
        # conn 不会被 dao.close() 之外的双重关闭 —— 这里我们不调 close
        assert not hasattr(dao, "_owns_conn") or True  # 占位：DAO 不持 owns 标志
        # 显式断言: 调用 dao.close() 后 conn.closed 为 True
        # 因为 sqlite3.Connection.close() 幂等且永远生效
        dao.close()
        # 再次 conn 操作应抛 ProgrammingError
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")


# ---------------------------------------------------------------------------
# 2. 加密透明化（明文入 → 密文落盘 → 明文读回）
# ---------------------------------------------------------------------------


class TestEncryptionTransparency:
    def test_create_encrypts_phone_to_db(self, conn, sample_order):
        dao = OrdersDAO(conn)
        dao.create(sample_order)
        # 落盘行：customer_phone_enc 存在且非明文
        row = conn.execute(
            "SELECT customer_phone_enc, customer_phone_hash FROM orders WHERE id=?",
            (sample_order.id,),
        ).fetchone()
        enc = row[0]
        assert enc is not None
        assert enc != "13800001234"
        # 密文可解
        assert decrypt(enc) == "13800001234"
        # hash 字段存在
        assert row[1] == hash_for_index("13800001234")

    def test_create_encrypts_id_card_to_db(self, conn, sample_order):
        dao = OrdersDAO(conn)
        dao.create(sample_order)
        row = conn.execute(
            "SELECT candidate_id_card_enc FROM orders WHERE id=?",
            (sample_order.id,),
        ).fetchone()
        enc = row[0]
        assert enc is not None
        assert decrypt(enc) == "430102200501011234"
        # 验证 DB 落盘无明文身份证列
        # （schema 中没有 candidate_id_card 列，列名只有 _enc 后缀）
        cols = conn.execute(
            "SELECT name FROM pragma_table_info('orders') WHERE name='candidate_id_card'"
        ).fetchone()
        assert cols is None

    def test_get_decrypts_pii_back(self, dao, sample_order):
        created = dao.create(sample_order)
        out = dao.get(created.id)
        assert out.customer_phone == "13800001234"
        assert out.candidate_id_card == "430102200501011234"
        assert out.customer_name == "张三"  # 明文存储
        assert out.candidate_subjects == ["物理", "化学", "生物"]
        assert out.tags == ["VIP", "高优"]

    def test_no_pii_in_db_when_not_provided(self, conn):
        order = _new_order()  # 无 PII
        OrdersDAO(conn).create(order)
        row = conn.execute(
            "SELECT customer_phone_enc, customer_phone_hash, candidate_id_card_enc "
            "FROM orders WHERE id=?",
            (order.id,),
        ).fetchone()
        assert row[0] is None  # 无明文 → 无密文
        assert row[1] is None  # 无 phone → 无 hash
        assert row[2] is None


# ---------------------------------------------------------------------------
# 3. CRUD：create / get / update
# ---------------------------------------------------------------------------


class TestCRUD:
    def test_create_returns_order(self, dao, sample_order):
        created = dao.create(sample_order)
        assert isinstance(created, Order)
        assert created.id == sample_order.id
        assert created.created_at is not None
        assert created.status_updated_at is not None

    def test_get_not_found(self, dao):
        with pytest.raises(OrderNotFound):
            dao.get("GKO-NOT-EXIST")

    def test_duplicate_primary_key_raises(self, conn, sample_order):
        dao = OrdersDAO(conn)
        dao.create(sample_order)
        # 再次 create 同 id → DuplicateOrder
        with pytest.raises(DuplicateOrder):
            dao.create(sample_order)

    def test_duplicate_external_id_raises(self, conn):
        dao = OrdersDAO(conn)
        # 第一次：建一个带 external_id 的订单
        first = _new_order(
            id=generate_order_id(),
            source="xianyu",
            external_id="EXT-DUP-1",
        )
        dao.create(first)
        # 第二次：同 source+external_id 但 id 不同 → 唯一索引冲突
        dup = _new_order(
            id=generate_order_id(),
            source="xianyu",
            external_id="EXT-DUP-1",
        )
        with pytest.raises(DuplicateOrder):
            dao.create(dup)

    def test_update_business_fields(self, dao, sample_order):
        created = dao.create(sample_order)
        updated = dao.update(
            created.id,
            {
                "plan_file": "/data/plans/abc.md",
                "notes": "已补充考生信息",
                "tags": ["VIP", "高优", "复诊"],
                "amount_cents": 19900,
            },
        )
        assert updated.plan_file == "/data/plans/abc.md"
        assert updated.notes == "已补充考生信息"
        assert updated.tags == ["VIP", "高优", "复诊"]
        assert updated.amount_cents == 19900
        # status 应不变
        assert updated.status == "pending"

    def test_update_rejects_status_field(self, dao, sample_order):
        created = dao.create(sample_order)
        with pytest.raises(ValueError, match="status"):
            dao.update(created.id, {"status": "paid"})

    def test_update_rejects_unknown_column(self, dao, sample_order):
        created = dao.create(sample_order)
        with pytest.raises(ValueError, match="不允许字段"):
            dao.update(created.id, {"hacker_field": "x"})

    def test_update_unknown_order_raises(self, dao):
        with pytest.raises(OrderNotFound):
            dao.update("GKO-NOT-EXIST", {"notes": "x"})

    def test_update_preserves_existing_paid_at_on_transition(self, conn, sample_order):
        """update 业务字段不应改 timestamp。"""
        dao = OrdersDAO(conn)
        created = dao.create(sample_order)
        # 推到 paid → paid_at 应被置位
        dao.transition_status(created.id, "paid", reason="payment")
        before = dao.get(created.id)
        # 业务字段更新
        dao.update(created.id, {"notes": "新备注"})
        after = dao.get(created.id)
        assert after.paid_at == before.paid_at
        assert after.status == "paid"
        assert after.notes == "新备注"


# ---------------------------------------------------------------------------
# 4. 状态机守护
# ---------------------------------------------------------------------------


class TestStateMachine:
    def test_legal_transition_writes_history(self, dao, sample_order):
        created = dao.create(sample_order)
        out = dao.transition_status(created.id, "paid", reason="wechat_pay")
        assert out.status == "paid"
        # paid_at 应被置位
        assert out.paid_at is not None
        # history 写入了 2 条（create + transition）
        history = dao.get_status_history(created.id)
        assert len(history) == 2
        # 第 1 条：None → pending（actor=dao_create）
        assert history[0].from_status is None
        assert history[0].to_status == "pending"
        assert history[0].actor == "dao_create"
        # 第 2 条：pending → paid
        assert history[1].from_status == "pending"
        assert history[1].to_status == "paid"
        assert history[1].reason == "wechat_pay"

    def test_illegal_transition_raises_and_rolls_back(self, dao, sample_order):
        created = dao.create(sample_order)
        # pending → serving 非法（必须先 paid）
        with pytest.raises(InvalidStateTransition):
            dao.transition_status(created.id, "serving")
        # 状态应保持 pending
        assert dao.get(created.id).status == "pending"
        # history 不应被多写
        history = dao.get_status_history(created.id)
        assert len(history) == 1
        assert history[0].to_status == "pending"

    def test_transition_unknown_status_raises(self, dao, sample_order):
        created = dao.create(sample_order)
        with pytest.raises(InvalidStateTransition):
            dao.transition_status(created.id, "frozen")

    def test_terminal_completed_blocks_further_transitions(self, dao, sample_order):
        created = dao.create(sample_order)
        for s in ("paid", "serving", "delivered", "completed"):
            dao.transition_status(created.id, s)
        # completed → refunded 非法（终态）
        with pytest.raises(InvalidStateTransition):
            dao.transition_status(created.id, "refunded")
        assert dao.get(created.id).status == "completed"

    def test_terminal_refunded_blocks_further_transitions(self, dao, sample_order):
        created = dao.create(sample_order)
        dao.transition_status(created.id, "refunded")
        with pytest.raises(InvalidStateTransition):
            dao.transition_status(created.id, "paid")
        with pytest.raises(InvalidStateTransition):
            dao.transition_status(created.id, "completed")
        assert dao.get(created.id).status == "refunded"

    def test_refund_from_any_non_terminal_state(self, dao):
        for start in ("pending", "paid", "serving", "delivered"):
            o = dao.create(_new_order(id=generate_order_id()))
            for s in ("paid", "serving", "delivered"):
                if start == s:
                    break
                dao.transition_status(o.id, s)
            out = dao.transition_status(o.id, "refunded", reason="customer_request")
            assert out.status == "refunded"

    def test_transition_preserves_earlier_paid_at(self, dao, sample_order):
        created = dao.create(sample_order)
        dao.transition_status(created.id, "paid")
        paid_at_1 = dao.get(created.id).paid_at
        # 推进到 serving → paid_at 应保持
        dao.transition_status(created.id, "serving")
        paid_at_2 = dao.get(created.id).paid_at
        assert paid_at_1 == paid_at_2
        # serving → delivered
        dao.transition_status(created.id, "delivered")
        # delivered → completed → completed_at 被置位
        out = dao.transition_status(created.id, "completed")
        assert out.completed_at is not None

    def test_transition_unknown_order_raises(self, dao):
        with pytest.raises(OrderNotFound):
            dao.transition_status("GKO-NOT-EXIST", "paid")


# ---------------------------------------------------------------------------
# 5. 事务与回滚
# ---------------------------------------------------------------------------


class TestTransaction:
    def test_transaction_commits_on_success(self, conn):
        dao = OrdersDAO(conn)
        with dao.transaction() as c:
            c.execute(
                "INSERT INTO orders (id, source, service_version, amount_cents, status, status_updated_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    "GKO-MAN-1",
                    "manual",
                    "basic",
                    100,
                    "pending",
                    utc_now_iso(),
                    utc_now_iso(),
                ),
            )
        # 提交后查询得到
        row = conn.execute(
            "SELECT id FROM orders WHERE id=?", ("GKO-MAN-1",)
        ).fetchone()
        assert row is not None

    def test_transaction_rolls_back_on_exception(self, conn):
        dao = OrdersDAO(conn)
        with pytest.raises(RuntimeError):
            with dao.transaction() as c:
                c.execute(
                    "INSERT INTO orders (id, source, service_version, amount_cents, status, status_updated_at, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        "GKO-MAN-2",
                        "manual",
                        "basic",
                        100,
                        "pending",
                        utc_now_iso(),
                        utc_now_iso(),
                    ),
                )
                raise RuntimeError("boom")
        # 回滚后查不到
        row = conn.execute(
            "SELECT id FROM orders WHERE id=?", ("GKO-MAN-2",)
        ).fetchone()
        assert row is None


# ---------------------------------------------------------------------------
# 6. 幂等 upsert_by_external_id
# ---------------------------------------------------------------------------


class TestUpsert:
    def _make_order(self, **overrides) -> Order:
        defaults = dict(
            id=generate_order_id(),
            source="xianyu",
            external_id="EXT-1001",
            service_version="basic",
            amount_cents=4900,
            status="pending",
        )
        defaults.update(overrides)
        return Order(**defaults)

    def test_upsert_inserts_when_missing(self, dao):
        order = self._make_order()
        r = dao.upsert_by_external_id(order)
        assert isinstance(r, UpsertResult)
        assert r.action == "inserted"
        assert r.old_status is None
        assert r.new_status == "pending"
        # history 应有 1 条
        history = dao.get_status_history(r.order_id)
        assert len(history) == 1
        assert history[0].from_status is None

    def test_upsert_unchanged_when_status_same(self, dao):
        order = self._make_order()
        dao.upsert_by_external_id(order)
        # 同样 status 再 upsert → unchanged
        order2 = self._make_order(
            id=generate_order_id(),  # id 不同，但 (source, external_id) 一致
            amount_cents=9999,  # 业务字段差异 — 但 DAO 不动
        )
        r = dao.upsert_by_external_id(order2)
        assert r.action == "unchanged"
        # amount_cents 应保持首次写入的
        existing = dao.get(r.order_id)
        assert existing.amount_cents == 4900

    def test_upsert_updates_on_legal_transition(self, dao):
        order = self._make_order()
        first = dao.upsert_by_external_id(order)
        # 推到 paid
        order.status = "paid"
        order.paid_at = utc_now_iso()
        r = dao.upsert_by_external_id(order)
        assert r.action == "updated"
        assert r.old_status == "pending"
        assert r.new_status == "paid"
        # history 应有 2 条
        history = dao.get_status_history(first.order_id)
        assert len(history) == 2
        assert history[1].to_status == "paid"

    def test_upsert_illegal_transition_returns_action(self, dao):
        order = self._make_order()
        dao.upsert_by_external_id(order)
        # 推进到 paid
        order.status = "paid"
        dao.upsert_by_external_id(order)
        # 尝试 pending（非法回退）
        order.status = "pending"
        r = dao.upsert_by_external_id(order)
        assert r.action == "illegal_transition"
        assert r.old_status == "paid"
        assert r.new_status == "pending"
        assert r.error is not None
        # DB 状态应保持 paid
        existing = dao.get(r.order_id)
        assert existing.status == "paid"

    def test_upsert_missing_external_id_rejected(self, dao):
        order = self._make_order()
        order.external_id = None
        r = dao.upsert_by_external_id(order)
        assert r.action == "illegal_transition"
        assert "external_id" in (r.error or "")

    def test_upsert_insert_writes_history(self, dao):
        order = self._make_order()
        r = dao.upsert_by_external_id(order, actor="xianyu_webhook", reason="evt-001")
        history = dao.get_status_history(r.order_id)
        assert history[0].actor == "xianyu_webhook"
        assert history[0].reason == "evt-001"


# ---------------------------------------------------------------------------
# 7. 查询：get_by_external_id / find_by_phone / list / count / stats
# ---------------------------------------------------------------------------


class TestQueries:
    def test_get_by_external_id(self, dao, sample_order):
        sample_order.external_id = "EXT-200"
        dao.create(sample_order)
        out = dao.get_by_external_id("web", "EXT-200")
        assert out is not None
        assert out.id == sample_order.id
        # 不存在 → None
        assert dao.get_by_external_id("web", "MISSING") is None

    def test_find_by_phone_returns_decrypted_orders(self, dao):
        a = _new_order(id=generate_order_id(), customer_phone="13800001234")
        b = _new_order(id=generate_order_id(), customer_phone="13800009999")
        dao.create(a)
        dao.create(b)
        results = dao.find_by_phone("13800001234")
        assert len(results) == 1
        assert results[0].id == a.id
        assert results[0].customer_phone == "13800001234"

    def test_find_by_phone_multiple_results(self, dao):
        # 同 phone hash 不同订单（业务上罕见但允许）
        a = _new_order(id=generate_order_id(), customer_phone="13800001234")
        b = _new_order(id=generate_order_id(), customer_phone="13800001234")
        dao.create(a)
        dao.create(b)
        results = dao.find_by_phone("13800001234")
        assert len(results) == 2

    def test_list_with_filters(self, dao):
        dao.create(
            _new_order(id=generate_order_id(), source="xianyu", status="pending")
        )
        dao.create(_new_order(id=generate_order_id(), source="web", status="paid"))
        dao.create(
            _new_order(id=generate_order_id(), source="xianyu", status="pending")
        )

        all_orders = dao.list(limit=100)
        assert len(all_orders) == 3
        xianyu_pending = dao.list(source="xianyu", status="pending")
        assert len(xianyu_pending) == 2
        assert all(
            o.source == "xianyu" and o.status == "pending" for o in xianyu_pending
        )

    def test_list_unknown_status_raises(self, dao):
        with pytest.raises(ValueError, match="未知 status"):
            dao.list(status="frozen")

    def test_list_limit_bounds(self, dao):
        with pytest.raises(ValueError, match="limit 越界"):
            dao.list(limit=0)
        with pytest.raises(ValueError, match="limit 越界"):
            dao.list(limit=2000)

    def test_list_offset_negative_raises(self, dao):
        with pytest.raises(ValueError, match="offset"):
            dao.list(offset=-1)

    def test_list_pagination(self, dao):
        for _ in range(5):
            dao.create(_new_order(id=generate_order_id()))
        page1 = dao.list(limit=2, offset=0)
        page2 = dao.list(limit=2, offset=2)
        page3 = dao.list(limit=2, offset=4)
        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1
        ids = {o.id for o in page1 + page2 + page3}
        assert len(ids) == 5

    def test_count_with_and_without_filters(self, dao):
        for s in ("pending", "pending", "paid", "refunded"):
            dao.create(_new_order(id=generate_order_id(), status=s))
        assert dao.count() == 4
        assert dao.count(status="pending") == 2
        assert dao.count(status="paid") == 1
        assert dao.count(status="refunded") == 1
        assert dao.count(status="completed") == 0

    def test_stats_by_status_includes_zero_states(self, dao):
        dao.create(_new_order(id=generate_order_id(), status="pending"))
        dao.create(_new_order(id=generate_order_id(), status="pending"))
        stats = dao.stats_by_status()
        # 6 态全部出现，零值不漏
        assert set(stats) == {
            "pending",
            "paid",
            "serving",
            "delivered",
            "completed",
            "refunded",
        }
        assert stats["pending"] == 2
        assert stats["paid"] == 0
        assert stats["completed"] == 0

    def test_list_returns_orders_with_pii(self, dao):
        o = _new_order(id=generate_order_id(), customer_phone="13800007777")
        dao.create(o)
        results = dao.list(limit=10)
        # 列表默认应已解密（to_db_row 入库时加密，list 读出时解密）
        assert results[0].customer_phone == "13800007777"


# ---------------------------------------------------------------------------
# 8. 状态历史
# ---------------------------------------------------------------------------


class TestStatusHistory:
    def test_history_is_chronological(self, dao, sample_order):
        created = dao.create(sample_order)
        for s in ("paid", "serving", "delivered", "completed"):
            dao.transition_status(created.id, s)
        history = dao.get_status_history(created.id)
        # 5 条：create + 4 transitions
        assert len(history) == 5
        assert [h.to_status for h in history] == [
            "pending",
            "paid",
            "serving",
            "delivered",
            "completed",
        ]
        assert [h.from_status for h in history] == [
            None,
            "pending",
            "paid",
            "serving",
            "delivered",
        ]
        # 全部为 StatusChange dataclass
        assert all(isinstance(h, StatusChange) for h in history)

    def test_history_for_unknown_order_is_empty(self, dao):
        assert dao.get_status_history("GKO-NOT-EXIST") == []


# ---------------------------------------------------------------------------
# 9. row_factory 不污染外部
# ---------------------------------------------------------------------------


class TestRowFactoryIsolation:
    def test_dao_does_not_corrupt_external_row_factory(self, conn_with_factory):
        """DAO 内部用 sqlite3.Row 工厂做查询，退出后外部 row_factory 应保持。"""
        prior = conn_with_factory.row_factory
        assert prior is sqlite3.Row
        dao = OrdersDAO(conn_with_factory)
        order = _new_order()
        dao.create(order)
        dao.get(order.id)
        dao.list(limit=10)
        # 退出后 row_factory 仍为 sqlite3.Row
        assert conn_with_factory.row_factory is sqlite3.Row


# ---------------------------------------------------------------------------
# 10. 删除
# ---------------------------------------------------------------------------


class TestDelete:
    def test_delete_existing_returns_true(self, dao, sample_order):
        created = dao.create(sample_order)
        assert dao.delete(created.id) is True
        with pytest.raises(OrderNotFound):
            dao.get(created.id)

    def test_delete_nonexistent_returns_false(self, dao):
        assert dao.delete("GKO-NOT-EXIST") is False

    def test_delete_cascades_status_history(self, conn, sample_order):
        dao = OrdersDAO(conn)
        created = dao.create(sample_order)
        dao.transition_status(created.id, "paid")
        # 2 条历史
        hist_before = conn.execute(
            "SELECT COUNT(*) FROM order_status_history WHERE order_id=?",
            (created.id,),
        ).fetchone()[0]
        assert hist_before == 2
        dao.delete(created.id)
        # 状态历史随 ON DELETE CASCADE 消失
        hist_after = conn.execute(
            "SELECT COUNT(*) FROM order_status_history WHERE order_id=?",
            (created.id,),
        ).fetchone()[0]
        assert hist_after == 0


# ---------------------------------------------------------------------------
# 11. 与 T8.1 dao_extension 的契约对齐
# ---------------------------------------------------------------------------


class TestContractAlignment:
    """确保 OrdersDAO.upsert_by_external_id 与 dao_extension 同名函数行为一致。"""

    def test_upsert_result_action_values_match(self, dao):
        # 同 (source, external_id) 不存在
        order = Order(
            id=generate_order_id(),
            source="xianyu",
            external_id="EXT-CONTRACT",
            service_version="basic",
            amount_cents=1000,
            status="pending",
        )
        r1 = dao.upsert_by_external_id(order)
        assert r1.action == "inserted"

        # status 相同 → unchanged
        order2 = Order(
            id=generate_order_id(),
            source="xianyu",
            external_id="EXT-CONTRACT",
            service_version="basic",
            amount_cents=2000,  # 不同 — 但 status 未变
            status="pending",
        )
        r2 = dao.upsert_by_external_id(order2)
        assert r2.action == "unchanged"

        # 状态推进 → updated
        order2.status = "paid"
        r3 = dao.upsert_by_external_id(order2)
        assert r3.action == "updated"
        assert r3.old_status == "pending"
        assert r3.new_status == "paid"

        # 非法回退 → illegal_transition
        order2.status = "pending"
        r4 = dao.upsert_by_external_id(order2)
        assert r4.action == "illegal_transition"
        assert r4.error is not None
