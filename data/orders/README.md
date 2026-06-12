# 订单数据模块 (T4.1)

提供订单的 SQLite schema、AES-256 加密（Fernet）、6 态状态机、Order dataclass。

## 目录结构

```
data/orders/
├── __init__.py
├── README.md
├── crypto.py            # Fernet 加密/解密/哈希派生
├── state_machine.py     # 6 态转换验证
├── models.py            # Order dataclass + 序列化
├── schema.py            # DDL + apply_schema()
└── tests/
    ├── __init__.py
    ├── test_crypto.py
    ├── test_state_machine.py
    └── test_schema.py
```

## 字段分类

| 类别       | 处理方式     | 字段                                  |
| ---------- | ------------ | ------------------------------------- |
| 强敏感 PII | AES-256 加密 | `customer_phone`, `candidate_id_card` |
| 弱敏感 PII | 脱敏存储     | `customer_name`, `candidate_name`     |
| 索引用哈希 | SHA-256 hex  | `customer_phone_hash`                 |
| 业务字段   | 明文         | `amount_cents`, `source`, `status`    |
| 元数据     | 明文         | `created_at`, `tags`                  |

## 6 态状态机

```
pending → paid → serving → delivered → completed
   │        │        │          │
   └──┬─────┴────────┴──────────┘
      ▼
  refunded (终态)
```

completed / refunded 为终态，不可再转换。

## 加密密钥

环境变量 `GAOKAO_ORDERS_FERNET_KEY` 必须配置；缺失时 `get_fernet()` 抛 `MissingEncryptionKey`，**禁止降级为明文**。

生产环境密钥生成示例：

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 快速使用

```python
import os
os.environ["GAOKAO_ORDERS_FERNET_KEY"] = "your-secret-here"

from data.orders.schema import apply_schema
from data.orders.crypto import encrypt, decrypt, hash_for_index
from data.orders.state_machine import OrderStatus, assert_valid_transition
from data.orders.models import Order, generate_order_id

# 1. 建表
conn = apply_schema("data/orders.db")

# 2. 创建订单
order = Order(
    id=generate_order_id(),
    source="xianyu",
    service_version="standard",
    amount_cents=9900,
    status=OrderStatus.PENDING.value,
    customer_name="张*",
    customer_phone="13800001234",
    candidate_name="张同学",
)
conn.execute(
    "INSERT INTO orders (...) VALUES (...)",
    order.to_db_row(),
)

# 3. 状态转换
assert_valid_transition(order.status, "paid")
```

## 验收（DoD）

- [x] AES-256 加密（Fernet）对 customer_phone / candidate_id_card 落盘
- [x] 6 态状态机 + 转换合法性校验
- [x] SQLite schema 幂等可重建
- [x] 外键约束启用
- [x] SHA-256 hash 字段支持手机号去重
- [x] CHECK 约束拒绝非法 status

## 下游衔接

- **T4.2 DAO**: 调用 `apply_schema()` 建表，使用 `state_machine.assert_valid_transition()` 守护状态变更
- **T4.3 CLI**: 直接 import `Order` dataclass + crypto
- **T6.1 FastAPI**: schema 不变，DAO 复用

## 版本

v1.0 — 2026-06-12 — T4.1 实施
