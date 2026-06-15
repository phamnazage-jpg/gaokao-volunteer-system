# BACKUP_AND_RECOVERY_PLAN

最后更新: 2026-06-14
状态: 最小恢复基线（已具备本地快照 + 完整性校验 + restore smoke）

## 1. 目标

为 T12 Web 自助 MVP 建立最小可恢复方案，覆盖：

- SQLite 数据库
- 报告 HTML/PDF 文件
- 上传/分享产物
- 运行所需关键配置与密钥映射关系
- 本地可执行的备份、校验、恢复演练入口

## 2. RPO / RTO 建议

- RPO: 24 小时内
- RTO: 4 小时内

说明：当前是轻量单机 MVP，不承诺秒级恢复，也不等同于生产级多机容灾。

## 3. 需要备份的对象

1. 数据库
   - 管理库 `data/orders/admin.db`
   - 订单库 `data/orders.db`
   - 分享库 `data/share/short_links.db`
2. 文件目录
   - 分享/公开报告目录
   - 报告 HTML/PDF 产物
   - `data/examples` 中的样例交付物（用于恢复 smoke）
3. 配置与运维资料
   - `.env` 实际部署值（不入 Git）
   - systemd / docker-compose 部署配置
4. 密钥资料
   - JWT secret
   - Fernet key
   - 支付相关密钥/证书

## 4. 当前已落地产物

- `scripts/backup_snapshot.sh`
  - 生成时间戳快照目录
  - 复制 DB / 文件 / 可选 config / 可选 secrets
  - 生成 `manifest.json`
  - 按 `GAOKAO_BACKUP_KEEP` 保留最近 N 份
- `scripts/backup_verify.sh`
  - 可校验 live staging 或已有快照
  - 校验 SQLite 可读性
  - 校验 `manifest.json` 哈希完整性
  - 调用 restore smoke
- `scripts/backup_restore_smoke.py`
  - 在恢复副本上启动 FastAPI `TestClient`
  - 走 `/health`、portal 状态页、报告 HTML、PDF 下载最小链路
  - 只改临时恢复副本，不改原始快照
- 定时接入口径示例
  - `ops/cron/gaokao-backup.crontab.example`
  - `ops/systemd/gaokao-backup.service`
  - `ops/systemd/gaokao-backup.timer`
  - `ops/systemd/gaokao-backup-verify.service`
  - `ops/systemd/gaokao-backup-verify.timer`

## 5. 最小备份策略

### 数据库

- 每日一次目录快照
- 文件名包含 UTC 时间戳
- 保留最近 7 份日备（可由 `GAOKAO_BACKUP_KEEP` 调整）

### 文件目录

- 与数据库同批次快照
- 报告/分享目录和样例报告分开保存，避免后续排障时混淆

### 配置与密钥

- `.env`、部署配置、密钥目录不与业务数据库混写到同一路径
- 通过环境变量显式声明：
  - `GAOKAO_BACKUP_ENV_FILE`
  - `GAOKAO_BACKUP_CONFIG_DIR`
  - `GAOKAO_BACKUP_SECRETS_DIR`
- 只允许受控人员访问

## 6. 最小 runbook（本地可执行）

### 6.1 生成快照

```bash
bash scripts/backup_snapshot.sh /tmp/gaokao-backups
```

可选环境变量：

```bash
export GAOKAO_BACKUP_KEEP=7
export GAOKAO_BACKUP_ENV_FILE=/etc/gaokao/.env
export GAOKAO_BACKUP_CONFIG_DIR=/etc/gaokao
export GAOKAO_BACKUP_SECRETS_DIR=/var/lib/gaokao/secrets
```

### 6.2 校验最近一份快照

```bash
bash scripts/backup_verify.sh --from-backup /tmp/gaokao-backups/backup-<UTC_TIMESTAMP>
```

校验内容：

1. `manifest.json` 哈希一致
2. SQLite 文件可打开、表可枚举
3. 恢复副本可跑最小服务 smoke：
   - `/health`
   - `/portal/{token}/status`
   - `/portal/{token}/report`
   - `/portal/{token}/report.pdf`

### 6.3 从 live 数据直接做一次恢复演练

```bash
bash scripts/backup_verify.sh
```

该命令会把当前 live DB / 文件复制到临时目录后执行同样的校验链。

## 7. 定时接入口径

### cron 示例

见：`ops/cron/gaokao-backup.crontab.example`

- 每天 02:30 生成快照
- 每周一 03:00 对最近一份快照执行 restore smoke

### systemd timer 示例

见：

- `ops/systemd/gaokao-backup.service`
- `ops/systemd/gaokao-backup.timer`
- `ops/systemd/gaokao-backup-verify.service`
- `ops/systemd/gaokao-backup-verify.timer`

说明：这些文件只是仓库内口径样例，不代表目标主机已经安装启用。

## 8. MVP 上线前最低要求

1. 至少完成一次真实快照生成
2. 至少完成一次 `backup_verify.sh --from-backup ...` 演练
3. 明确密钥存放位置和负责人
4. 不得再使用“Git 备份即可恢复系统”作为对外或内部结论

## 9. 当前仍未闭环的外部/后续缺口

- 异机 / 异地备份尚未落地
- 目标主机上的 cron / systemd timer 尚未实际安装验收
- 真实 SMTP / IM / 监控通道的目标机联调与失败演练记录仍未归档
- 密钥轮换与应急恢复仍缺真实执行记录

## 10. 不可降级的不变量

- 备份必须覆盖 4 节列出的所有对象, 不得漏备份 `share_reports`
- 快照必须含 manifest (`manifest.json`), 含每个文件的 SHA-256
- 校验必须走 `scripts/backup_verify.sh`, 不允许用裸 SQLite `sqlite3 <file> ".schema"` 代替
- 恢复演练必须是服务级 (FastAPI TestClient) 而不仅是文件级
- `delivered` / `failed` 事件备份必须保留 `failure_reason`, 用于事后根因分析
- 备份介质必须使用 24h RPO, 不允许依赖“Git 备份可恢复系统”作为对外口径

## 11. 流程 (MVP)

```
定时任务 (cron / systemd timer)
    │
    ▼
1. 快照阶段: 复制 SQLite + 报告 + manifest.json
    │
    ▼
2. 校验阶段: backup_verify.sh 走 restore smoke
    │        ├─ 200 healthz
    │        ├─ 200 portal_status
    │        ├─ 200 portal_report
    │        └─ 200 portal_pdf
    │
    ▼
3. 失败处理: watchdog 退出码 != 0
    │
    ▼
4. 告警: 邮件 / IM / 监控 (P1-8 整改后)
```

## 12. 后续工作

- 接入 P1-8 整改的 service-level smoke (已完成)
- 增加异机异地备份 (P2-6 之后)
- 接入告警推送 (P1-8 后续)
- 备份失败告警链仍需目标主机接入真实 SMTP / IM / monitoring；仓库内尚未提供可直接安装的 backup alert service
- 接入密钥轮换演练 (P2-6 之后)
- 真实演练记录归档（模板：`reports/DR_DRILL_TEMPLATE.md`，示例：`reports/DR_DRILL_2026-07-01.md`）
- 当前 restore smoke 证明的是“最小服务链可用”，不是完整生产级全链恢复
