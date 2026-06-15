# PAYMENT_DOMAIN_DESIGN

最后更新: 2026-06-14

## 1. 设计目标

把 T12 中的支付、退款、回调、对账从“页面动作”提升为一等领域对象，避免把订单状态与支付状态混为一体。

## 2. 领域对象

### payment_order

- `payment_id`
- `order_id`
- `provider`
- `amount_cents`
- `status` (`pending/paying/paid/failed/refund_pending/refunded`)
- `checkout_token`
- `provider_trade_no`
- `created_at`
- `updated_at`

### payment_attempt

- 用于保留多次发起支付/重试尝试
- MVP 可先不单独建表，但设计必须保留扩展位

### refund

- `refund_id`
- `payment_id`
- `order_id`
- `amount_cents`
- `status`
- `reason`
- `created_at`

### reconciliation_job

- 用于后续对账任务
- MVP 允许只停留在设计层

## 3. 状态机拆分

### 订单状态

- `pending`
- `paid`
- `serving`
- `delivered`
- `completed`
- `refunded`

### 支付状态

- `pending`
- `paying`
- `paid`
- `failed`
- `refund_pending`
- `refunded`

原则：

- 订单状态不直接替代支付状态
- portal 展示阶段由订单 + 支付 + 交付物共同推导

## 4. 回调处理要求

回调验收至少要覆盖：

1. provider 签名校验
2. `payment_id / order_id` 对应关系校验
3. `amount_cents` 金额校验
4. 幂等处理（重复通知不能重复记账）
5. provider trade no 持久化
6. 异常记录与人工补偿入口

回调字段映射：

- `payment_id` 永远以 provider 给出的 trade id 为唯一键
- `order_id` 是从 `payment_id` 推导的弱引用, 不允许在回调里伪造
- `amount_cents` 必须以服务端 SQLite 记录为准, 不允许以 provider 给出的值为准
- `provider_trade_no` 落入独立列, 便于后续对账

## 5. 当前实现状态

已存在：

- `data/payments/models.py`
- `data/payments/dao.py`
- `data/payments/service.py`
- `mock` / `alipay_sim` provider
- webhook 归一化处理

未完成：

- 真实 `alipay` provider
- refund 一等对象
- reconciliation job
- provider 级签名/证书联调

## 6. 决策

- MVP 只允许一个真实 provider 先闭环
- `alipay_sim` 只用于上线前模拟，不可冒充真实支付验收
- 真实支付上线前，必须先完成 provider doctor 与环境前置校验

## 7. 不可降级的不变量

- 支付状态与订单状态必须共存, 不允许互相覆盖
- 支付推进与订单推进必须在同一 SQLite 事务里完成
- 回调处理必须至少覆盖 4 节列出的 6 项校验
- 任何 webhook 失败不能直接标记 `refunded`; 必须回到 `refund_pending` 等人工处理
- MVP 阶段不使用 `payment_attempt` 独立表, 但代码必须保持扩展位, 允许后续单独建表

## 8. 流程 (MVP)

```
用户点击支付
    │
    ▼
create_checkout(order_id, portal_token)
    │  // 单事务, 同步推进订单 + 支付
    ▼
provider.build_checkout_url() ──▶ 用户跳转 provider
    │
    ▼
provider 异步回调 webhook
    │
    ▼
handle_webhook(payload, signature)
    │  // 单事务
    │  // 签名 + 金额 + 状态校验
    │  // 推进 payments.status = paid
    │  // 推进 orders.status = paid
    ▼
portal 状态页: 已支付 / 待资料
```

## 9. 数据流字段

支付主表 (`payments`):

| 字段              | 类型    | 说明                                 |
| ----------------- | ------- | ------------------------------------ |
| id                | text PK | payment_id                           |
| order_id          | text FK | 订单主表强引用                       |
| provider          | text    | `mock` / `alipay_sim` / `alipay`     |
| amount_cents      | int     | 服务端真相, 不允许以 provider 值为准 |
| currency          | text    | 默认 CNY                             |
| status            | text    | 见第 3 节支付状态                    |
| provider_trade_no | text    | 持久化 provider trade no, 用于对账   |
| checkout_token    | text    | portal_token 的镜像, 用于发件校验    |
| callback_payload  | text    | 原始回调 JSON, 仅排查用, 不可外泄    |
| refund_reason     | text    | 退款原因                             |
| paid_at           | text    | ISO8601                              |
| refunded_at       | text    | ISO8601                              |

## 10. 后续工作

- 把 `alipay` 真实 provider 升级为可联调
- 建立 `reconciliation_job` 一等对象, 支持定时对账
- 引入 `payment_attempt` 表记录每次发起/重试, 用于诊断
- 与退款设计 (`X-05` 一致) 合并为单篇《支付 + 退款 + 对账》主文档
