# T4.2 实现订单数据访问层（DAO） - 实施记录

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal**: 订单 DAO 层（CRUD + 事务 + 加密字段处理 + 6 态状态机守护），落地为 `data/orders/dao.py`

**Architecture**:

- `OrdersDAO` class — 封装 `sqlite3.Connection`，所有方法自包含事务或事务上下文
- 加密/解密透明化 — API 入口 `Order` dataclass 走明文 PII，DAO 内部 `to_db_row()` / `from_db_row()` 转换
- 状态机守护 — `transition_status()` 单事务内 `UPDATE orders` + `INSERT order_status_history`
- 嵌套事务 — `_tx_depth` 计数；外层事务中内层不重复 commit，异常统一回滚外层
- row_factory 隔离 — `_row_factory_ctx()` 临时切 `sqlite3.Row`、退出后恢复

**Tech Stack**: Python 3.10+, sqlite3 (stdlib), pytest, ruff

**Ref**: TECH_ARCHITECTURE.md §3.4 数据模型 + §6.1 数据安全; REMEDIATION_TASK_BOARD P2-9; T4-1-order-schema.md

---

## 1. 设计原则

### 1.1 API 形态

```python
with OrdersDAO.connect("data/orders.db") as dao:
    # 1) 写
    created = dao.create(order, actor="manual_entry", reason="wechat_inquiry")
    dao.update(created.id, {"plan_file": "/data/plans/abc.md"})
    paid = dao.transition_status(created.id, "paid", reason="wechat_pay")
    # 2) 查
    out = dao.get(created.id)              # 解密 PII
    rows = dao.list(status="paid", limit=20)
    history = dao.get_status_history(created.id)
    # 3) 幂等
    result = dao.upsert_by_external_id(order)  # 'inserted'|'updated'|'unchanged'|'illegal_transition'
    # 4) 显式事务
    with dao.transaction() as conn:
        conn.execute(...)
```

### 1.2 加密透明化

| API                          | 形态                            |
| ---------------------------- | ------------------------------- |
| `create(order)` 入参         | `Order`（明文 PII）             |
| `get(id).customer_phone`     | **明文**（已解密）              |
| `get(id).customer_phone_enc` | **不存在**（DAO 内部消化）      |
| `list()` / `find_by_phone()` | 全部解密返回 `Order`            |
| `Order.to_dict(decrypt=...)` | 应用层控制（True/False/"mask"） |

### 1.3 状态机守护

- 6 态转换图（沿用 T4.1 状态机）：`pending → paid → serving → delivered → completed`，任意非终态 → `refunded`
- `transition_status(id, to, ...)` 单事务：
  1. 读 `SELECT status FROM orders WHERE id=?`
  2. `assert_valid_transition(from, to)` —— 非法抛 `InvalidStateTransition` 并回滚
  3. `UPDATE orders SET status=?, status_updated_at=?, <ts_col>=COALESCE(<ts_col>, ?)`
  4. `INSERT INTO order_status_history(from, to, actor, reason)`
- 时间戳联动：`paid → paid_at`、`serving → started_at`、`delivered → delivered_at`、`completed → completed_at` 由状态自动置位（`COALESCE` 保留首次值）

### 1.4 幂等 upsert 契约（与 T8.1 对齐）

`upsert_by_external_id()` 返回 4 种 `action` 字符串，与 `data/channel_sync/dao_extension.upsert_by_external_id` 完全对齐：

| action               | 含义                                         |
| -------------------- | -------------------------------------------- |
| `inserted`           | DB 不存在该 `(source, external_id)`，已新建  |
| `updated`            | 已存在且状态可推进，已 UPDATE + 写 history   |
| `unchanged`          | 已存在但状态未变                             |
| `illegal_transition` | 已存在但状态非法回退；`error` 字段附非法原因 |

T8.1 现有的 `data/channel_sync/dao_extension.py` 可在迁移完成后删除（行为已对齐）。

### 1.5 事务嵌套

```python
def transaction(self):
    self._tx_depth += 1
    try:
        if self._tx_depth == 1:
            yield self._conn
            self._conn.commit()
        else:
            yield self._conn  # 嵌套不 commit
    except Exception:
        if self._tx_depth == 1:
            self._conn.rollback()
        raise
    finally:
        self._tx_depth -= 1
```

这让 `create()` 内部用 `with self.transaction():` 时，在外层 `dao.transaction()` 包住的情况下不会重复 commit；任一层异常 → 外层回滚。

---

## 2. 模块结构

### 2.1 新增文件

```
data/orders/
├── dao.py                  # T4.2 — OrdersDAO
└── tests/
    └── test_dao.py         # T4.2 — 51 用例
```

### 2.2 修改文件

- `data/orders/__init__.py` — 导出 `OrdersDAO` / `UpsertResult` / `StatusChange` / `OrderNotFound` / `DuplicateOrder`
- `data/orders/README.md` — DAO API 一览表 + 加密透明化边界表 + 下游衔接
- `CHANGELOG.md` — T4.2 条目

---

## 3. DoD

- [x] CRUD 完整（create / get / list / count / update / delete）
- [x] 事务守护（`transaction()` 上下文 + 嵌套语义）
- [x] 加密字段透明化（明文入口 → 密文落盘 → 明文读回）
- [x] 6 态状态机守护（合法转换 + 非法回滚 + 终态不可再转）
- [x] 时间戳联动（paid_at / started_at / delivered_at / completed_at）
- [x] 幂等 upsert（4 种 action 与 T8.1 对齐）
- [x] 状态历史审计（`order_status_history` 自动写入）
- [x] 重复主键 / 重复 `(source, external_id)` 抛 `DuplicateOrder`
- [x] `update()` 显式拒绝 `status` 字段（必须走 `transition_status`）
- [x] row_factory 不污染外部连接
- [x] 模块 51 用例全绿 / data/orders 总计 163 用例全绿 / data/ 386 全绿
- [x] ruff 0 warning / py_compile clean

---

## 4. 验证命令

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m pytest data/orders/tests/test_dao.py -v
python3 -m pytest data/orders/tests/ -q     # 163/163
python3 -m pytest data/ -q                  # 386/386
ruff check data/orders/
python3 -m py_compile data/orders/dao.py data/orders/__init__.py
```

---

## 5. 风险与降级

| 风险                                  | 降级策略                                                                                |
| ------------------------------------- | --------------------------------------------------------------------------------------- |
| Fernet 密钥丢失 → 密文不可恢复        | 启动时校验密钥存在；强制备份流程写入 runbook（沿用 T4.1）                               |
| `transactions` 嵌套语义不直观         | 文档明示 + 测试覆盖三层嵌套 (`create()` 内部 `transaction()` + 外层 `transaction()`)    |
| `dao_extension` 与本 DAO 行为漂移     | `TestContractAlignment` 测试组 4 种 action 显式对齐；dao_extension 删除前必须过这个测试 |
| 业务字段在 `update()` 中误传 `status` | 显式 `ValueError("禁止通过 update() 改 status；请使用 transition_status()")`            |

---

## 6. 下游衔接

- **T4.3 CLI (`gaokao-order-manager`)**: 直接 `with OrdersDAO.connect(...) as dao:`
- **T6.1 FastAPI**: DAO 复用 + `to_dict(decrypt_sensitive=...)` 控制 API 响应
- **T8.1 闲鱼 Webhook**: `dao.upsert_by_external_id()` 替代 `dao_extension.upsert_by_external_id`
- **T11.1 性能基线**: DAO 的 `list()` 走 `customer_phone_hash` / `(source, external_id)` 索引

---

**版本**: v1.0 | **最后更新**: 2026-06-12 | **作者**: coder (kanban t_168e0ece)
