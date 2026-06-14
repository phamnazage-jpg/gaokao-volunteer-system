# P1-8 backup restore drill

最后更新: 2026-06-14
状态: 本地最小演练方案已落地，生产主机安装/告警仍待外部收口

## 1. 目标

把“只能证明文件可复制”的状态，提升到“可对快照执行 restore smoke，验证最小服务链可用”。

## 2. 本次落地范围

- 新增 `scripts/backup_snapshot.sh`
- 扩展 `scripts/backup_verify.sh`
- 新增 `scripts/backup_restore_smoke.py`
- 补 `ops/cron` 与 `ops/systemd` 示例接入口径
- 补 pytest 验证用例 `tests/test_backup_workflow.py`

## 3. 演练步骤

### 3.1 生成快照

```bash
bash scripts/backup_snapshot.sh /tmp/gaokao-backups
```

### 3.2 对快照执行恢复校验

```bash
bash scripts/backup_verify.sh --from-backup /tmp/gaokao-backups/backup-<UTC_TIMESTAMP>
```

### 3.3 校验成功标准

- `manifest_ok` 输出存在
- SQLite 文件输出 `sqlite_ok`
- restore smoke JSON 至少包含：
  - `health_status = 200`
  - `portal_status = 200`
  - `portal_report = 200`
  - `portal_pdf = 200`

## 4. 设计约束

1. restore smoke 只在临时恢复副本上写入测试订单，不改原始快照
2. 若仓库内不存在现成交付物，smoke 允许在恢复副本下生成极小 HTML/PDF 占位物
3. 本方案不宣称“完整生产恢复完成”，只证明最小服务链可被恢复副本支撑

## 5. 非目标

- 异地备份
- 主机级定时器安装
- 失败告警链
- 密钥轮换真实执行记录
- 完整支付/退款/交付全链恢复

## 6. 后续外部动作

- 在目标主机安装 cron 或 systemd timer
- 将备份日志接入监控/通知
- 形成季度恢复演练记录
- 补密钥轮换 runbook 与演练记录
