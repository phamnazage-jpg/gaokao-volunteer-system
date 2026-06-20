# DELIVERY_RETENTION_OPS_RUNBOOK

最后更新: 2026-06-20（T12-D 端到端本地 acceptance 步骤新增；T12-D 修复
`OrdersDAO.__exit__` 不区分 conn 所有权导致多订单连续 anonymize 失败的 bug）

## 1. 当前真相

### delivery dispatcher / watchdog

当前已落仓并可接定时任务的事实：

- 执行脚本：`scripts/gaokao-delivery-dispatch.py`
- 巡检脚本：`scripts/gaokao-delivery-watchdog.py`
- systemd 样例：`deploy/systemd/gaokao-delivery-dispatch.{service,timer}` / `deploy/systemd/gaokao-delivery-watchdog.{service,timer}`
- cron 样例：`deploy/cron/gaokao-jobs.crontab`

注意边界：

- 当前 `station` 事件的最终状态是 `validated`，表示站内交付物校验通过；只有 `email` 渠道真实发送后才进入 `delivered`。
- dispatcher 每次会处理 `ready` 与 `validated` 事件；如果缺少 HTML/PDF，会把事件记为 `failed`，并递增 `attempt_count`。
- watchdog 复用同一 dispatch 路径，但只要本轮出现失败事件就返回 exit code `2`，适合接宿主机监控或外部告警。

### backup verify / restore smoke

当前灾备验证链路的事实：

- `bash scripts/backup_verify.sh`：从 live 数据做一次本地 staging + restore smoke
- `bash scripts/backup_verify.sh --from-backup <snapshot_dir>`：直接对已有快照做 restore smoke
- live staging 下的 SQLite 不再裸复制 `.db`，而是通过 `sqlite3.backup()` 生成一致性副本，避免 WAL 模式下出现空库 / 缺表误判
- `live-smoke` 与 `snapshot-verify` 共用同一 restore smoke，但前者验证“当前运行中数据能否被一致性抽样复制”，后者验证“已有快照是否可恢复”

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
- 它会清理订单侧敏感字段、清空 `delivery_notifications.payload_json`，并修剪 `deletion-requests.jsonl` / `share_link_access_events` 中对应订单的旁路记录。
- 它不等于“前台删除工单流程已上线”。

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
# 主动推进 ready/validated 事件
python3 scripts/gaokao-delivery-dispatch.py --channel station --limit 100

# 巡检：有失败时返回 2
python3 scripts/gaokao-delivery-watchdog.py --channel station --limit 100

# retention dry-run（人工指定 cutoff）
python3 scripts/gaokao-retention-cleanup.py --cutoff 2025-12-31T00:00:00+00:00 --dry-run

# retention 定时模式（自动计算 cutoff）
python3 scripts/gaokao-retention-cleanup.py --retention-days 180
```

执行后至少抽查：

- 候选订单已匿名化
- 对应 `delivery_notifications.payload_json` 已变成 `{}`
- `deletion-requests.jsonl` 中对应订单记录已被修剪
- `share_link_access_events` 中对应 report_id 的访问事件已被修剪

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

---

## 8. T12-D 本地端到端 acceptance（2026-06-20 落地）

下面这套步骤可在任意干净临时目录里复现 retention cleanup 真实行为，
用于部署前最后一道本地 smoke。回归测试已锁住相同契约：

`tests/test_retention_cleanup.py::test_retention_cleanup_apply_anonymizes_multiple_old_orders_in_sequence`

### 8.1 前置环境

```bash
export PY=/home/long/project/gaokao-volunteer-system/.venv/bin/python
export GAOKAO_ORDERS_DB_PATH=/tmp/t12d-orders.db
export GAOKAO_SHARE_DB_PATH=/tmp/t12d-share.db
export GAOKAO_DELETION_REQUEST_LOG_PATH=/tmp/t12d-deletion-requests.jsonl
export GAOKAO_ORDERS_FERNET_KEY="test-secret-for-web-self-service"
```

### 8.2 最小 acceptance 步骤

```bash
# 1) 跑针对性回归（必须全过）
cd /home/long/project/gaokao-volunteer-system
$PY -m pytest tests/test_retention_cleanup.py -q
# 期望: 6 passed

# 2) 端到端 smoke：seed 4 订单 + apply + 验证后置状态
#    （一次性脚本，留在仓库外即可）
$PY -c "
import os, json
from admin.config import load_settings
from data.orders.dao import OrdersDAO
from data.orders.models import Order
from data.share.short_link import ShortLinkService
from data.orders.retention_cleanup import run_cleanup

# 4 笔订单: 2 笔终端态(应被清理) + 1 笔 pending(应保留) + 1 笔 paid-in-window(应保留)
with OrdersDAO.connect('/tmp/t12d-orders.db') as dao:
    for spec in [
        dict(id='GKO-T12D-OLD-COMPLETED', status='completed', phone='13800000001'),
        dict(id='GKO-T12D-OLD-REFUNDED',  status='refunded',  phone='13800000002'),
        dict(id='GKO-T12D-FRESH-PENDING', status='pending',   phone='13800000003'),
        dict(id='GKO-T12D-PAID-RECENT',   status='paid',      phone='13800000004'),
    ]:
        o = Order(id=spec['id'], source='web', service_version='standard',
                  amount_cents=9900, status=spec['status'],
                  customer_name='张某', customer_phone=spec['phone'],
                  candidate_name='考生', candidate_province='湖南',
                  notes='seeded', created_at='2024-12-01T00:00:00+00:00')
        dao.create(o, actor='smoke', reason='seed')

print(run_cleanup('/tmp/t12d-orders.db',
                  cutoff_iso='2025-06-30T00:00:00+00:00', apply=True,
                  deletion_request_log_path='/tmp/t12d-deletion-requests.jsonl',
                  share_db_path='/tmp/t12d-share.db').__dict__)
"
```

### 8.3 验收通过判定（2026-06-20 实测）

| 检查项 | 期望 | 实际 |
| --- | --- | --- |
| `candidates` | 2（仅 terminal 且 < cutoff） | 2 ✅ |
| `anonymized` | 2（无 `Cannot operate on a closed database`） | 2 ✅ |
| GKO-T12D-OLD-COMPLETED post-state | `customer_phone=None, customer_name="已匿名化"` | ✅ |
| GKO-T12D-OLD-REFUNDED post-state | 同上 | ✅ |
| GKO-T12D-FRESH-PENDING post-state | 原值保留 | ✅ |
| GKO-T12D-PAID-RECENT post-state | 原值保留 | ✅ |
| `deletion_logs_pruned` | 匹配订单日志被裁掉 | 1 ✅ |
| `share_events_pruned` | 指向已删订单的访问事件被裁掉 | 2 ✅ |

### 8.4 历史 bug 背景

T12-D acceptance 之前，端到端 smoke 在 `apply=True` 多订单场景下崩溃：
- 现象: 第一笔 `anonymize_order` 退出时，`OrdersDAO.__exit__` 不区分
  连接所有权（外部传入的 `conn` 也被 `close()`），把
  `OrderDeletionService` 持有的连接关掉
- 后果: 第二笔开始全部 `sqlite3.ProgrammingError: Cannot operate on a closed database`
- 触发条件: `retention_cleanup.run_cleanup` 一次命中 ≥ 2 笔终端态订单
  （生产环境 retention_days=180 + 周日 03:30 触发时极易命中）
- 修复: `OrdersDAO.__init__` 新增 `owns_conn: bool = False` 参数；
  `__exit__` 仅在 `owns_conn=True` 时 close；`connect()` classmethod
  创建的连接自动设 `owns_conn=True`（保持原行为）；外部 service
  包成 DAO 走 with-block 默认不 close

### 8.5 部署前 checklist

- [ ] `tests/test_retention_cleanup.py` 全过（6 passed）
- [ ] 本节 8.2 smoke 实跑通过
- [ ] `deploy/systemd/gaokao-retention-cleanup.service` 中 `WorkingDirectory` /
      `GAOKAO_ORDERS_DB_PATH` / `GAOKAO_PYTHON_BIN` 与目标主机实际路径一致
- [ ] `deploy/systemd/gaokao-retention-cleanup.timer` 已 `systemctl enable --now`
- [ ] 首次 cron / timer 触发后，`journalctl -u gaokao-retention-cleanup.service`
      出现 `"candidates"` 字段且数量与后端订单分布合理
- [ ] 上述部署动作的真实执行记录已留在 ops 留痕
