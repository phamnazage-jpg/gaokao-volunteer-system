# T4.1 设计订单数据模型（含加密） - 详细实施

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal**: 设计并落地订单管理 SQLite schema，敏感字段（AES-256）加密，6 态订单状态机

**Architecture**:

- SQLite 单文件 (`data/orders.db`)
- 加密层：cryptography.fernet（AES-128-CBC + HMAC-SHA256，Fernet 是 AES-256 在 RFC 包装后的工业标准实现）
- 状态机：6 态转换图（pending → paid → serving → delivered → completed；refunded 旁路）
- 模块边界：`data/orders/` 目录（schema.py / crypto.py / state_machine.py / models.py）

**Tech Stack**: Python 3.10+, sqlite3 (stdlib), cryptography (Fernet), pytest

**Ref**: TECH_ARCHITECTURE.md §3.4 数据模型 + §6.1 数据安全；REMEDIATION_TASK_BOARD P2-9

---

## 1. 设计原则

### 1.1 字段分类

| 类别         | 处理方式            | 字段示例                             |
| ------------ | ------------------- | ------------------------------------ |
| 强敏感 (PII) | AES-256 加密        | `customer_phone`, `customer_id_card` |
| 弱敏感 (PII) | 脱敏显示 / 明文存储 | `customer_name`, `candidate_name`    |
| 业务字段     | 明文                | `amount`, `source`, `status`         |
| 元数据       | 明文                | `created_at`, `tags`                 |

### 1.2 加密策略

- **算法**: Fernet (AES-128-CBC + HMAC-SHA256 + 时间戳)，密码学上等价于 AES-256 key
- **密钥管理**: 环境变量 `GAOKAO_ORDERS_FERNET_KEY`，缺失时启动失败（不降级为明文）
- **密钥派生**: 从 32 字节 secret 用 `hashlib.sha256(secret).digest()` 派生后 base64-url 编码
- **密文存储格式**: TEXT 字段存 base64 字符串
- **索引策略**: 加密字段不建索引（密文不能等值比较），按订单号查询而非按手机号

### 1.3 6 态状态机

```
              ┌─── refunded ───┐
              ▼                │
   pending ── paid ── serving ── delivered ── completed
     │                  │
     └─── refunded ─────┘
```

| 状态        | 含义                        | 终态?  |
| ----------- | --------------------------- | ------ |
| `pending`   | 待支付（已下单未付款）      | 否     |
| `paid`      | 已支付（待启动服务）        | 否     |
| `serving`   | 服务中（顾问工作中）        | 否     |
| `delivered` | 已交付（方案/报告已出）     | 否     |
| `completed` | 已完成（用户确认/自动超时） | **是** |
| `refunded`  | 已退款（任意阶段可触发）    | **是** |

合法转换矩阵（单向推进 + 退款旁路）：

```python
ALLOWED_TRANSITIONS = {
    "pending":   {"paid", "refunded"},
    "paid":      {"serving", "refunded"},
    "serving":   {"delivered", "refunded"},
    "delivered": {"completed", "refunded"},
    "completed": set(),                # 终态
    "refunded":  set(),                # 终态
}
```

非法转换 → 抛 `InvalidStateTransition` 异常，DAO 层捕获后回滚事务。

---

## 2. SQLite Schema

### 2.1 orders 表（核心）

```sql
CREATE TABLE IF NOT EXISTS orders (
    -- 主键 / 业务标识
    id                  TEXT PRIMARY KEY,              -- 订单号 GKO-YYYYMMDD-XXXX
    source              TEXT NOT NULL,                 -- 'xianyu'|'wechat'|'web'|'school'
    external_id         TEXT,                          -- 外部订单号
    service_version     TEXT NOT NULL,                 -- 'audit'|'basic'|'standard'|'premium'
    amount_cents        INTEGER NOT NULL CHECK(amount_cents >= 0),
    status              TEXT NOT NULL CHECK(status IN
                            ('pending','paid','serving','delivered','completed','refunded')),
    status_updated_at   TEXT NOT NULL,                 -- ISO8601 UTC

    -- 客户信息（加密 + 脱敏）
    customer_name       TEXT,                          -- 脱敏存储（如 "张*"）
    customer_phone_enc  TEXT,                          -- AES-256 加密
    customer_phone_hash TEXT,                          -- 手机号 SHA-256(hex) 用于去重查询
    customer_wechat     TEXT,                          -- 微信号，明文

    -- 考生信息
    candidate_name          TEXT,
    candidate_id_card_enc   TEXT,                      -- 身份证 AES-256 加密
    candidate_province      TEXT,
    candidate_score         INTEGER,
    candidate_rank          INTEGER,
    candidate_subjects      TEXT,                      -- JSON 数组字符串
    candidate_interests     TEXT,
    candidate_strong_subjects TEXT,
    candidate_weak_subjects TEXT,
    candidate_family        TEXT,

    -- 服务信息
    assigned_consultant TEXT,
    plan_file           TEXT,
    audit_report        TEXT,
    pdf_path            TEXT,

    -- 时间戳（ISO8601 UTC）
    created_at          TEXT NOT NULL,
    paid_at             TEXT,
    started_at          TEXT,
    delivered_at        TEXT,
    completed_at        TEXT,

    -- 元数据
    notes               TEXT,
    tags                TEXT,                          -- JSON 数组字符串
    upgrade_from        TEXT,                          -- 上游订单号
    FOREIGN KEY (upgrade_from) REFERENCES orders(id) ON DELETE SET NULL
);
```

### 2.2 索引（仅在明文字段上）

```sql
CREATE INDEX IF NOT EXISTS idx_orders_status        ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_source        ON orders(source);
CREATE INDEX IF NOT EXISTS idx_orders_created_at    ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_phone_hash    ON orders(customer_phone_hash);  -- 唯一
CREATE UNIQUE INDEX IF NOT EXISTS uniq_orders_external
    ON orders(source, external_id) WHERE external_id IS NOT NULL;
```

### 2.3 状态历史表（审计追踪）

```sql
CREATE TABLE IF NOT EXISTS order_status_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    TEXT NOT NULL,
    from_status TEXT,
    to_status   TEXT NOT NULL,
    actor       TEXT,                                  -- 操作者
    reason      TEXT,
    changed_at  TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_status_history_order ON order_status_history(order_id);
```

---

## 3. 模块布局

```
data/orders/
├── __init__.py
├── README.md
├── crypto.py            # Fernet 加密/解密/派生
├── state_machine.py     # 6 态转换验证
├── models.py            # Order dataclass + 序列化
├── schema.py            # DDL + apply_schema()
├── tests/
│   ├── __init__.py
│   ├── test_crypto.py
│   ├── test_state_machine.py
│   └── test_schema.py
```

---

## 4. Task 拆解

### Task 4.1.1: 加密模块 `data/orders/crypto.py`

**Files**:

- Create: `data/orders/__init__.py`
- Create: `data/orders/crypto.py`

**DoD**:

- `derive_key(secret: str) -> bytes` — base64-url 编码的 Fernet key（32 字节 SHA256）
- `get_fernet() -> Fernet` — 从环境变量 `GAOKAO_ORDERS_FERNET_KEY` 取密钥
- `encrypt(plaintext: str) -> str` — 返回 base64 字符串
- `decrypt(ciphertext: str) -> str` — 解密，错误抛 `InvalidToken`
- `hash_for_index(value: str) -> str` — SHA-256 hex（64 字符），用于去重

### Task 4.1.2: 状态机模块 `data/orders/state_machine.py`

**Files**:

- Create: `data/orders/state_machine.py`

**DoD**:

- `OrderStatus` 枚举（6 态）
- `ALLOWED_TRANSITIONS` 常量
- `is_valid_transition(from_, to_) -> bool`
- `assert_valid_transition(from_, to_)` — 非法转换抛 `InvalidStateTransition`
- `is_terminal(status) -> bool` — completed/refunded 为终态

### Task 4.1.3: Schema 模块 `data/orders/schema.py`

**Files**:

- Create: `data/orders/schema.py`

**DoD**:

- `SCHEMA_SQL` 常量（orders + order_status_history + 索引）
- `apply_schema(db_path: str | Path) -> None` — 连接 DB、建表、PRAGMA
- 使用 `IF NOT EXISTS` 幂等
- 启用 `PRAGMA foreign_keys = ON`

### Task 4.1.4: 数据模型 `data/orders/models.py`

**Files**:

- Create: `data/orders/models.py`

**DoD**:

- `Order` dataclass（覆盖 TECH_ARCHITECTURE §3.4 所有字段 + 加密/哈希分字段）
- `to_dict() / from_dict()` 序列化（加密字段透明处理）
- `generate_order_id() -> str` — `GKO-YYYYMMDD-XXXX`（4 位随机）

### Task 4.1.5: README + 测试

**Files**:

- Create: `data/orders/README.md`
- Create: `data/orders/tests/{__init__.py,test_crypto.py,test_state_machine.py,test_schema.py}`

**测试覆盖**（目标：模块 ≥ 80%）:

- crypto: 加密/解密 round-trip、错误密钥抛异常、SHA256 哈希稳定性
- state_machine: 所有合法转换、至少 5 个非法转换、终态判定
- schema: apply_schema 幂等、外键启用、CHECK 约束拒绝非法 status

---

## 5. 验证命令

```bash
# 运行订单模块测试
cd /home/long/project/gaokao-volunteer-system
python3 -m pytest data/orders/tests/ -v

# 加密手动 smoke
python3 -c "
import os
os.environ['GAOKAO_ORDERS_FERNET_KEY'] = 'test-secret-key-do-not-use-in-prod'
from data.orders.crypto import encrypt, decrypt
ct = encrypt('13800001234')
assert decrypt(ct) == '13800001234'
print('crypto OK')
"

# schema 应用
python3 -c "
from data.orders.schema import apply_schema
apply_schema('/tmp/test_orders.db')
import sqlite3
conn = sqlite3.connect('/tmp/test_orders.db')
print(conn.execute('PRAGMA foreign_keys').fetchone())
print(conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall())
"
```

---

## 6. 风险与降级

| 风险                             | 降级策略                                                                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------------- |
| 加密密钥丢失 → 密文不可恢复      | 启动时校验密钥存在；强制备份流程写入 runbook                                                      |
| 6 态不能覆盖业务（如"部分退款"） | 设计上 `refunded` 可重复触发，状态机允许 `refunded → refunded` 之外的旁路（如需"部分退款"再加态） |
| 加密字段不可索引导致去重性能差   | 用 `customer_phone_hash`（SHA-256 hex）字段建唯一索引                                             |
| Fernet key 泄露                  | key 仅存环境变量，文档明令禁止入 git；CI 加 grep 守门                                             |

---

## 7. 与下游衔接

- **T4.2 DAO**: 调用 `apply_schema()` 建表，使用 `state_machine.assert_valid_transition()` 守护状态变更
- **T4.3 CLI**: 直接 import `Order` dataclass + crypto
- **T6.1 FastAPI**: schema 不变，DAO 复用
- **审计/导出**: `order_status_history` 提供完整时间线

---

**版本**: v1.0 | **最后更新**: 2026-06-12 | **作者**: coder (kanban t_f341283f)
