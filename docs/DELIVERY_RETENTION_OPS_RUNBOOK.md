# DELIVERY_RETENTION_OPS_RUNBOOK

最后更新: 2026-06-14

## 1. 当前真相

### delivery dispatcher / watchdog

当前已落仓并可接定时任务的事实：

- 执行脚本：`scripts/gaokao-delivery-dispatch.py`
- 巡检脚本：`scripts/gaokao-delivery-watchdog.py`
- systemd 样例：`deploy/systemd/gaokao-delivery-dispatch.{service,timer}` / `deploy/systemd/gaokao-delivery-watchdog.{service,timer}`
- cron 样例：`deploy/cron/gaokao-jobs.crontab`

注意边界：

- 当前 `station` 事件的最终状态是 `validated`，表示站内交付物校验通过；只有 `email` 渠道真实发送后才进入 `delivered`。
- dispatcher 每次会处理 `ready` 与 `failed` 事件；如果缺少 HTML/PDF，会把事件记为 `failed`，并递增 `attempt_count`。
- watchdog 复用同一 dispatch 路径，但只要本轮出现失败事件就返回 exit code `2`，适合接宿主机监控或外部告警。

### retention cleanup

当前已落仓并可接定时任务的事实：

- 手工入口：`scripts/gaokao-retention-cleanup.py --cutoff <ISO8601> [--dry-run]`
- 定时入口：`scripts/gaokao-retention-cleanup.py --retention-days 180 [--dry-run]`
- 兼容别名：`scripts/gaokao_retention_cleanup.py`
- systemd 样例：`deploy/systemd/gaokao-retention-cleanup.{service,timer}`
- cron 样例：`deploy/cron/gaokao-jobs.crontab`

注意边界：

- 当前清理动作是 **匿名化**（`anonymize_order`），不是物理删除。
- 只处理 `completed/refunded` 且锚点时间早于 cutoff 的订单。
- 它会清理订单侧敏感字段并写审计，但不等于“前台删除工单流程已上线”。

## 2. 统一环境配置

建议先复制：

```bash
cp deploy/systemd/gaokao-jobs.env.example deploy/systemd/gaokao-jobs.env
```

最少确认以下变量：

- `GAOKAO_ORDERS_DB_PATH`：生产订单 DB 路径
- `GAOKAO_PYTHON_BIN`：建议指向项目 `.venv/bin/python`
- `GAOKAO_DELIVERY_CHANNEL`：当前默认 `station`
- `GAOKAO_DELIVERY_LIMIT`：单次 dispatch/watchdog 扫描上限
- `GAOKAO_RETENTION_DAYS`：默认 `180`

## 3. 手工执行口径

```bash
# 主动推进 ready/failed 事件
python3 scripts/gaokao-delivery-dispatch.py --channel station --limit 100

# 巡检：有失败时返回 2
python3 scripts/gaokao-delivery-watchdog.py --channel station --limit 100

# retention dry-run（人工指定 cutoff）
python3 scripts/gaokao-retention-cleanup.py --cutoff 2025-12-31T00:00:00+00:00 --dry-run

# retention 定时模式（自动计算 cutoff）
python3 scripts/gaokao-retention-cleanup.py --retention-days 180
```

退出码：

- dispatcher：`0` = 脚本执行完成（结果看 JSON）
- watchdog：`0` = 本轮无失败；`2` = 本轮发现失败事件
- retention cleanup：`0` = 脚本执行完成；异常参数或运行错误会非 0 退出

## 4. systemd 安装口径

```bash
sudo cp deploy/systemd/gaokao-*.service /etc/systemd/system/
sudo cp deploy/systemd/gaokao-*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gaokao-delivery-dispatch.timer
sudo systemctl enable --now gaokao-delivery-watchdog.timer
sudo systemctl enable --now gaokao-retention-cleanup.timer
```

验证：

```bash
systemctl list-timers 'gaokao-*'
systemctl start gaokao-delivery-dispatch.service
systemctl status gaokao-delivery-watchdog.service --no-pager
journalctl -u gaokao-retention-cleanup.service -n 50 --no-pager
```

说明：

- watchdog 的 exit code `2` 会让对应 service 进入 failed，便于接 `OnFailure=` 或宿主机监控。
- 如果部署路径不是当前仓库路径，先修改 unit 里的 `WorkingDirectory` 与 `EnvironmentFile`。

## 5. cron 备用口径

`deploy/cron/gaokao-jobs.crontab` 给出最小样例，导入前先确保：

1. `/var/log/gaokao-volunteer-system/` 已创建且可写；
2. `GAOKAO_PYTHON_BIN` 指向安装完依赖的解释器；
3. crontab 中仓库路径与真实部署一致。

导入示例：

```bash
crontab deploy/cron/gaokao-jobs.crontab
crontab -l
```

## 6. 推荐节奏

- dispatcher：每 5 分钟
- watchdog：每 10 分钟
- retention cleanup：每周一次（周日 03:30 UTC）

## 7. 仍未收口的缺口

1. 尚无邮件/微信真实发送执行器。
2. watchdog 的本地告警 sink 已存在，但目标主机上的真实 SMTP / webhook 联调仍未验收。
3. retention cleanup 只是后台匿名化作业，前台/客服删除工单流程仍未上线。
4. 这些 unit/timer/cron 样例已落仓，但是否真正安装到目标生产主机，需要部署时另行执行并留存记录。
