# T8.4 渠道失败兜底 SOP

状态：已落地（巡检 CLI + 人工补录指令）
适用范围：当前巡检事实源以 `xianyu` 的 `webhook_audit` / `poller_state` / `poller_run` 为准；其他渠道目前仅复用“人工补录模板”，不应误解为已接入同等自动健康判定。

## 1. 目标

当 Webhook 主路径异常、poller 兜底异常或渠道侧临时不可用时，运营/值班同学可以：

1. 先做事实巡检，确认是不是链路退化；
2. 再走人工补录，确保订单不因为渠道故障而丢单；
3. 最后继续用已有 order-manager CLI 推进 `paid/serving/delivered` 状态。

## 2. 定期检查

建议每 5~15 分钟执行一次：

```bash
python3 scripts/gaokao-channel-fallback --db data/orders.db check --source xianyu --human
```

返回语义：

- `status: ok`：最近未发现明显异常
- `status: warn`：链路可能未启动 / 最近运行过旧 / 存在失败信号，需要人工关注
- `status: critical`：poller 连续报错或最近一次 poller_run 失败，应立即切人工兜底

退出码：

- `0` = ok
- `1` = warn
- `2` = critical

适合 cron / systemd timer / 外部监控直接接入。

## 3. 人工兜底入口

### 3.1 打印模板

```bash
python3 scripts/gaokao-channel-fallback --db data/orders.db manual-template --source xianyu --human
```

### 3.2 新建订单

注意：当前 CLI 通过命令行参数接收姓名/手机号，存在 shell history / `ps` 暴露风险。仅建议在可信单用户主机上临时执行；执行后应清理历史记录，且不要把真实 PII 粘贴到工单/IM。

```bash
python3 scripts/gaokao-order-manager --db data/orders.db create \
  --source xianyu \
  --service-version basic \
  --amount-cents 0 \
  --customer-name 张三 \
  --customer-phone 13800001234 \
  --candidate-name 李同学 \
  --candidate-province 湖南
```

说明：

- `external_id` 可留空，允许渠道故障期先人工建单；
- `amount_cents` 在未确认实付时可先填 `0`，后续再 `update`；
- 订单创建后会自动生成 `GKO-*` 内部单号，后续推进都用该单号。

### 3.3 补齐字段 / 推进状态

```bash
python3 scripts/gaokao-order-manager --db data/orders.db update <ORDER_ID> \
  --assigned-consultant consultant-a \
  --note 渠道故障期人工补录

python3 scripts/gaokao-order-manager --db data/orders.db pay <ORDER_ID> --reason manual_pay
python3 scripts/gaokao-order-manager --db data/orders.db deliver <ORDER_ID> --reason manual_delivery
```

## 4. 值班判断规则

优先看以下事实：

1. `webhook_audit` 最近是否还有 `accepted`
2. `poller_state.last_run_at` 是否超过阈值
3. `poller_state.last_error` / `poller_run.error_message` 是否持续存在
4. 最近 60 分钟 `rejected + parse_error` 是否明显升高

建议阈值（CLI 默认值）：

- poller stale：15 分钟
- webhook stale：30 分钟
- recent window：60 分钟
- reject warn threshold：5 次
- poller error warn threshold：3 次

## 5. 推荐调度

最小 cron 方案：

```cron
*/10 * * * * cd /home/long/project/gaokao-volunteer-system && python3 scripts/gaokao-channel-fallback --db data/orders.db check --source xianyu
```

说明：

- 非 0 退出码表示要进入监控/告警；
- 真正是否有业务影响，还要结合最近是否有渠道订单流量；
- 若当前阶段尚未启用 poller，可接受 `warn`，但应明确值班同学走人工补录。

## 6. 当前边界

本次 T8.4 只补齐“巡检 + 人工兜底”闭环，不做：

- 自动调用真实闲鱼开放平台 API；
- 自动把外部失败订单直接转成人工建单；
- 自动通知企业微信/短信。
- 为 `wechat` / `school` 等非 xianyu 渠道建立独立 webhook/poller 健康事实源。

这些属于后续增强项，不影响当前人工值班闭环。
