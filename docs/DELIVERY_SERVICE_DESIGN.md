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
- `scripts/gaokao-delivery-watchdog.py`（失败返回 exit code `2`）
- `ready -> sent` / `缺文件 -> failed` / `attempt_count` 递增
- `station` 通道 dispatch 时会真实生成 `station_notice`，portal 状态页展示“通知已发送”消息卡片
- `email` 通道使用 `SMTPDeliverySender` 发送真实邮件通知，支持 `GAOKAO_SMTP_*` 配置，并已通过本地 stub SMTP 验证
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- `deploy/systemd/gaokao-delivery-{dispatch,watchdog}.{service,timer}`
- `deploy/cron/gaokao-jobs.crontab`

未完成：

- 独立 `delivery_job` / `delivery_attempt` 模型
- 邮件/渠道真实发送执行器
- 告警推送集成（当前只有 watchdog 非 0 退出码）
- 多通道统一投递状态页

## 6. 当前最短闭环

1. 订单进入 `delivered`
2. 真实 HTML/PDF 都存在
3. portal 显示 `report_ready`
4. 状态页提供查看/下载入口
5. `report_ready` 事件落库且幂等
6. `gaokao-delivery-dispatch.py --channel station` 可把 ready 事件推进到 sent
7. 缺失交付物时事件转 failed，并记录 `failure_reason`
8. 可通过 systemd timer / cron 周期执行 dispatcher，并用 watchdog 暴露失败退出码

## 7. 下一步实施建议

1. 增加失败重试阈值与告警推送
2. 增加面向用户的独立通知审计页
3. 把事件生命周期细化为 `ready` / `validated` / `delivered` / `failed`
4. 区分 `station`（本地渲染）与 `email`（真实下游推送）两类 channel 的 `delivered` 判定
5. 再决定是否扩到更多通道

## 8. 事件生命周期（2026-06-14 修订）

P2-3 整改后, dispatcher 强制走如下状态机:

```
ready   ── 初始化, 还没校验
  │
  ▼
validated ── payload 解析通过 + 交付物 (html / pdf) 校验通过
  │           注意: station channel 在这一步会落 payload, 但不再升级为 delivered
  │
  ▼
delivered ── 真实下游推送完成 (仅 email)
  │
  ▼
failed ── 任意环节失败
```

- `ready -> validated` 必须有 artifact (html / pdf) 真实存在于磁盘
- `validated -> delivered` 必须由真实 sender 回调成功 (`email.send_report_ready` 返回成功)
- `station` 通道因为没有真实下游, 永远停在 `validated`
- `sent` 字段是 legacy alias, 仍然存在但不应再被新代码依赖

## 9. 生产化接入口径

仓库内已提供最小 runbook 与调度样例：

- runbook：`docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- systemd：`deploy/systemd/gaokao-delivery-dispatch.{service,timer}` / `deploy/systemd/gaokao-delivery-watchdog.{service,timer}`
- cron：`deploy/cron/gaokao-jobs.crontab`

注意：当前 watchdog 仍是“带失败退出码的 dispatch 巡检”，并不等于独立通知告警系统。

## 10. 不可降级的不变量

- 事件状态机 `ready` / `validated` / `delivered` / `failed` 必须被 dispatcher 严格遵守
- `delivered` 永远只能由真实 sender 成功返回
- `failed` 事件必须有 `failure_reason` 字段
- 同一 `(order_id, event_type)` 必须幂等, 重复 dispatcher 不会产生额外副作用
- `delivered` 之后, payload 写入的 `delivered_at` 必须等于 `last_attempt_at`

## 11. 后续工作

- 把独立 `delivery_job` / `delivery_attempt` 模型实现为 SQLite 表
- 引入 `attempt_count` 与 `last_attempt_at` 之外的成功重试预算
- 多通道统一投递状态页 (类似 notification audit 页面)
- 告警推送 (Sentry / 飞书 / 钉钉) 与 watchdog 整合
