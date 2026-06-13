# 订单数据模块 (T4.1 + T4.2 + T11.2)

提供订单的 SQLite schema、AES-256 加密（Fernet）、6 态状态机、Order dataclass，以及完整的 DAO 数据访问层（T4.2）。

## 目录结构

```
data/orders/
├── __init__.py
├── README.md
├── crypto.py            # Fernet 加密/解密/哈希派生
├── masking.py           # 展示脱敏工具 (T11.2)
├── state_machine.py     # 6 态转换验证
├── models.py            # Order dataclass + 序列化 (to_dict 支持 mask 策略)
├── schema.py            # DDL + apply_schema()
├── dao.py               # OrdersDAO — CRUD + 事务 + 状态机守护 (T4.2)
└── tests/
    ├── __init__.py
    ├── test_crypto.py
    ├── test_masking.py
    ├── test_models.py
    ├── test_schema.py
    ├── test_state_machine.py
    └── test_dao.py
```

## 字段分类

| 类别       | 处理方式                | 字段                                  |
| ---------- | ----------------------- | ------------------------------------- |
| 强敏感 PII | AES-256 加密 + 展示遮罩 | `customer_phone`, `candidate_id_card` |
| 弱敏感 PII | 脱敏存储 + 展示遮罩     | `customer_name`, `candidate_name`     |
| 索引用哈希 | SHA-256 hex             | `customer_phone_hash`                 |
| 业务字段   | 明文                    | `amount_cents`, `source`, `status`    |
| 元数据     | 明文                    | `created_at`, `tags`                  |

> T11.2 起，`Order.to_dict()` 默认走"展示遮罩"（如 `138****1234`），
> API 响应 / 前端列表无需再做额外处理。

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

## 快速使用 — DAO 方式（推荐，T4.2）

```python
import os
os.environ["GAOKAO_ORDERS_FERNET_KEY"] = "your-secret-here"

from data.orders import (
    OrdersDAO, Order, generate_order_id,
    OrderNotFound, DuplicateOrder, UpsertResult,
)

# 1. 连接 + 建表（幂等）
with OrdersDAO.connect("data/orders.db") as dao:
    # 2. 创建订单（明文 PII 入口，内部加密落盘）
    order = Order(
        id=generate_order_id(),
        source="xianyu",
        service_version="standard",
        amount_cents=9900,
        status="pending",
        customer_name="张三",
        customer_phone="13800001234",
        candidate_name="张同学",
    )
    created = dao.create(order, actor="manual_entry")

    # 3. 读回 — PII 自动解密
    out = dao.get(created.id)
    assert out.customer_phone == "13800001234"

    # 4. 状态转换（事务内：UPDATE orders + INSERT order_status_history）
    paid = dao.transition_status(created.id, "paid", reason="wechat_pay")

    # 5. 查历史
    history = dao.get_status_history(created.id)
    for h in history:
        print(h.from_status, "→", h.to_status, "by", h.actor)

    # 6. 幂等 upsert（接 T8.1 闲鱼 Webhook）
    result = dao.upsert_by_external_id(order)
    print(result.action)  # 'inserted' / 'updated' / 'unchanged' / 'illegal_transition'

    # 7. 批量 / 显式事务
    with dao.transaction() as conn:
        conn.execute(...)  # 任何异常自动回滚
```

## DAO API 一览 (T4.2)

| 方法                                                   | 用途                                                 |
| ------------------------------------------------------ | ---------------------------------------------------- |
| `OrdersDAO.connect(path)`                              | 按路径建连接 + 应用 schema + 强制 `sqlite3.Row` 工厂 |
| `OrdersDAO(conn)`                                      | 接管已有连接（不自动关闭）                           |
| `dao.create(order, actor=..., reason=...)`             | 插入订单 + 写首条 status_history                     |
| `dao.update(id, {field: value})`                       | 改业务字段（**禁止改 status**，状态机字段）          |
| `dao.transition_status(id, to, ...)`                   | 状态机守护的转换（事务内 UPDATE + INSERT history）   |
| `dao.get(id)` / `dao.get_by_external_id(src, eid)`     | 单查（解密 PII）                                     |
| `dao.find_by_phone(phone)`                             | 按手机号 hash 查询（去重 / 客户识别）                |
| `dao.list(status=..., source=..., limit=50, offset=0)` | 分页列表                                             |
| `dao.count(status=..., source=...)`                    | 统计                                                 |
| `dao.stats_by_status()`                                | 按状态分组统计（含 0 计数的完整 6 态）               |
| `dao.get_status_history(id)`                           | 状态变更时间线（`StatusChange` 列表）                |
| `dao.upsert_by_external_id(order, ...)`                | 幂等 upsert（4 种 `action` 区分）                    |
| `dao.delete(id)`                                       | 物理删除（CASCADE 清空 status_history）              |
| `dao.transaction()`                                    | 显式事务上下文（异常回滚 / 正常提交）                |
| `with dao as ...:`                                     | 上下文管理器（推荐）                                 |

## 异常

- `OrderNotFound(LookupError)` — 主键 / 唯一键查不到
- `DuplicateOrder(ValueError)` — 主键或 `(source, external_id)` 冲突
- `InvalidStateTransition(ValueError)` — 非法状态转换（`transition_status` / `upsert` 时）

## 加密透明化的边界

| 入参 / 出参                      | 形态                                               |
| -------------------------------- | -------------------------------------------------- |
| `create(order)` 入参 Order       | **明文 PII**                                       |
| `create()` 抛 `DuplicateOrder`   | DB 已落密文                                        |
| `get(id).customer_phone`         | **明文**（已解密）                                 |
| `get(id).customer_phone_enc`     | **不存在**（DAO 内部消化）                         |
| `list()` / `find_by_phone()`     | 全部解密返回 Order                                 |
| `to_dict(decrypt_sensitive=...)` | 应用层控制（True 明文 / False 移除 / "mask" 遮罩） |

## 验收（DoD）

- [x] AES-256 加密（Fernet）对 customer_phone / candidate_id_card 落盘
- [x] 6 态状态机 + 转换合法性校验
- [x] SQLite schema 幂等可重建
- [x] 外键约束启用
- [x] SHA-256 hash 字段支持手机号去重
- [x] CHECK 约束拒绝非法 status
- [x] 展示脱敏（T11.2）：Order.to_dict 默认走 mask 策略
- [x] **T4.2 DAO**：CRUD + 事务 + 加密字段处理 + 状态机守护（51 用例全绿）

## 展示脱敏 (T11.2)

为防止 API 响应 / 前端 / 日志 / 截图泄露完整 PII，订单数据模型支持"展示遮罩"：

```python
from data.orders.models import Order

order = Order(
    id="GKO-20260612-AAAA",
    source="web",
    service_version="basic",
    customer_name="张三",
    customer_phone="13800001234",
    candidate_id_card="430102200501011234",
)

# 默认:mask 模式 — 适合 API 响应 / 前端
order.to_dict()
# {
#   "customer_phone": "138****1234",
#   "candidate_id_card": "430102********1234",
#   "customer_name": "张*",
#   ...
# }

# 显式明文(后台人工核对场景)
order.to_dict(decrypt_sensitive=True)

# 完全移除(对外公开统计/审计日志)
order.to_dict(decrypt_sensitive=False)
```

`masking` 模块是纯字符串工具，与 `crypto` 正交，可在任意层（API 序列化、Jinja2
模板过滤器、日志格式化、CSV 导出器）独立复用。

## T4.3 订单管理 CLI

入口：`scripts/gaokao-order-manager`

```bash
# 创建订单
python3 scripts/gaokao-order-manager create \
  --source web --service-version standard --amount-cents 9900 \
  --customer-name 张三 --customer-phone 13800001234 \
  --candidate-name 李同学 --candidate-province 湖南 --candidate-score 578

# 订单列表 / 详情
python3 scripts/gaokao-order-manager list --status pending
python3 scripts/gaokao-order-manager show GKO-20260612-ABCD

# 更新业务字段（禁止直接改 status）
python3 scripts/gaokao-order-manager update GKO-20260612-ABCD \
  --assigned-consultant consultant-a --note 已分配顾问 --tag VIP

# 支付 / 交付 / 升级
python3 scripts/gaokao-order-manager pay GKO-20260612-ABCD --reason wechat_pay
python3 scripts/gaokao-order-manager deliver GKO-20260612-ABCD --reason report_ready
python3 scripts/gaokao-order-manager upgrade GKO-20260612-ABCD \
  --service-version standard --target-amount-cents 9900 --reason upgrade_to_standard

# 统计 / 最小导出
python3 scripts/gaokao-order-manager stats
python3 scripts/gaokao-order-manager export \
  --output /tmp/orders-report.csv --status pending --source school
```

子命令：

- `create`：新建订单，默认输出 JSON，敏感字段默认遮罩
- `list` / `show`：查询订单；`show` 同时返回 `history`
- `update`：只允许改业务字段，拒绝空更新与直接改 `status`
- `pay`：推进 `pending -> paid`
- `deliver`：从 `paid` 自动推进 `serving -> delivered`；若已在 `serving` 则只做最后一步
- `upgrade`：按目标总价创建补差价升级单，关联 `upgrade_from`，并给原单补 `upgraded` 标记
- `stats`：返回 `total_orders`、`by_status`、`by_source`、`by_service_version`
- `export`：导出最小 CSV 报表，字段固定为 `订单号/渠道/金额/状态/创建时间`

## 下游衔接

- **T4.3 CLI**: `gaokao-order-manager` 直接 import `OrdersDAO` + `Order`
- **T6.1 FastAPI**: schema 不变，DAO 复用（API 层只做权限校验 + `to_dict(decrypt_sensitive=...)`）
- **T8.1 闲鱼 Webhook**: 用 `dao.upsert_by_external_id()` 取代 `data/channel_sync/dao_extension.py`
  的同名函数（行为已对齐 — 4 种 `action` 字符串完全相同；该扩展模块可删除）

## 版本

v1.4 — 2026-06-12 — T4.5 最小导出（CLI export 子命令 + CSV 报表字段 `订单号/渠道/金额/状态/创建时间`）
v1.3 — 2026-06-12 — T4.4 升级订单流程（upgrade 子命令 + upgrade_order + 补差价校验）
v1.2 — 2026-06-12 — T4.2 DAO 层落地（51 用例，ruff 0 warning，data/ 386 用例全绿）
v1.1 — 2026-06-12 — T11.2 展示脱敏（mask 策略 + masking.py）
v1.0 — 2026-06-12 — T4.1 实施
