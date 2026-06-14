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
