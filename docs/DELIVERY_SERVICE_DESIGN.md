# DELIVERY_SERVICE_DESIGN

最后更新: 2026-06-14

## 1. 目标

将“报告生成完成”与“已交付给用户”明确区分，避免把 `delivered` 误当成只是一条后台状态修改。

## 2. 设计原则

1. 交付是独立业务对象，不等于报告文件存在
2. 用户可见状态必须基于真实交付物
3. 通知触发点应尽量靠近稳定主链，而不是只挂在单一路由
4. 至少一种 MVP 交付方式先闭环

## 3. MVP 交付方式

当前优先：

- 站内查看 HTML 报告
- 站内下载 PDF

后续可扩展：

- 邮件投递
- 微信/渠道通知

## 4. 建议对象

### delivery_job

- `delivery_id`
- `order_id`
- `channel` (`station/email/...`)
- `status` (`pending/ready/sent/failed`)
- `payload_json`
- `created_at`
- `updated_at`

### delivery_attempt

- `delivery_id`
- `attempt_no`
- `status`
- `failure_reason`
- `created_at`

## 5. 当前实现状态

已存在：

- `delivery_notifications` 事件表
- portal 状态页 / 报告页 / PDF 下载页
- `delivered` 但无交付物时不再误报 `report_ready`
- `data.notifications.dispatcher.DeliveryDispatcher`
- `scripts/gaokao-delivery-dispatch.py`
- `ready -> sent` / `缺文件 -> failed` / `attempt_count` 递增

未完成：

- 独立 `delivery_job` / `delivery_attempt` 模型
- 邮件/渠道真实发送执行器
- 自动重试调度与告警链
- 多通道统一投递状态页

## 6. 当前最短闭环

1. 订单进入 `delivered`
2. 真实 HTML/PDF 都存在
3. portal 显示 `report_ready`
4. 状态页提供查看/下载入口
5. `report_ready` 事件落库且幂等
6. `gaokao-delivery-dispatch.py --channel station` 可把 ready 事件推进到 sent
7. 缺失交付物时事件转 failed，并记录 `failure_reason`

## 7. 下一步实施建议

1. 把 dispatcher 接入定时任务或 systemd timer
2. 增加邮件或站内通知真实发送器（二选一先闭环）
3. 增加失败重试阈值与告警
4. 再决定是否扩到多通道
