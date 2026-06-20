# ACTIVE_EXECUTION_BOARD_2026-06-20

最后更新: 2026-06-20
状态词: 当前有效问题执行板
真相源: `docs/CURRENT_STATE.md`
问题来源: `docs/ACTIVE_REMEDIATION_2026-06-20.md`

> 本文件取代 `docs/ACTIVE_EXECUTION_BOARD_2026-06-19.md`（已降级为历史快照）。

---

## 1. 当前门禁结论

结论: v2.1.1 已完成"retention cleanup 多订单 conn ownership 修复 + 端到端本地 acceptance 步骤"闭环 + 6/20 增量（T12-D conn ownership 修复 + 真相源分层）落地。
dev-verify 状态: 直接相关子集 205 passed, 0 failed；retention 6 passed；ruff + mypy 通过。完整 dev-verify 跑通结果在 main `f9e68ee` 之后由 `bash scripts/dev-verify.sh` 确认。

禁止事项：

- 不再重复处理已修复的历史问题
- 不把 T12 之外的 Web 自助能力混入已完成的 v2.1 结论
- 不把"设计占位"误报为"已实现"
- 不把 Git/文档修订当成支付/交付/合规能力的替代
- 不把"端到端本地 acceptance 步骤就绪"误报为"生产已部署"（T12-D 仍需 ops 在目标主机实际执行 `systemctl enable --now` 与首次 timer 触发后留痕）

---

## 2. 6/20 增量执行情况

### T12-D retention cleanup conn ownership 修复（P1, 2026-06-20 落地）

- 状态: ✅ completed（端到端本地 acceptance 步骤就绪 + 生产化部署动作待 ops 执行）
- 落地:
  - `data/orders/dao.py` 新增 `owns_conn: bool = False` 参数；`__exit__` 仅在 `owns_conn=True` 时 close；`connect()` classmethod 自动设 `owns_conn=True`
  - `tests/test_retention_cleanup.py` 新增 `test_retention_cleanup_apply_anonymizes_multiple_old_orders_in_sequence` 锁住多订单连续 anonymize 契约
  - `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` §8 新增 T12-D 本地端到端 acceptance 步骤 + 验收通过判定表 + 部署前 checklist + 历史 bug 背景
  - `CHANGELOG.md` 顶部加 v2.1.1 (2026-06-20) 段
  - `docs/CURRENT_STATE.md` 顶部加 6/20 增量段；真相源优先级 6/20 > 6/19
  - `docs/ACTIVE_REMEDIATION_2026-06-20.md` + `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md` 取代 6/19 版本
- 验证: 6 个 retention 测试全过 + 205 个直接相关子集全过 + ruff + mypy 通过 + 端到端 smoke 4 笔订单实测通过
- 提交: `bcb1e68` fix(retention): T12-D acceptance — OrdersDAO conn ownership → `f9e68ee` merge: T12-D retention cleanup conn ownership fix

---

## 3. 仍有效的执行任务清单（按优先级）

### T12-A 真实支付 acceptance

- Owner: tech-lead / ops
- 优先级: P0
- 状态: pending
- 目标:
  - 在真实商户主体 + 备案域名 + 公网 notify_url 就绪后, 跑支付宝沙箱/生产 acceptance
- 依赖:
  - 外部商户与域名前置
  - `data/payments/service.py` 6/19 持久化已就绪

### T12-B `info_submitted -> serving` 自动主链

- Owner: engineer
- 优先级: P0
- 状态: pending
- 目标:
  - 真实 worker/生成服务/线上调度收口

### T12-D retention cleanup 生产化部署验收（6/20 端到端 acceptance 步骤就绪）

- Owner: ops
- 优先级: P1
- 状态: ⚠ acceptance 步骤就绪 + 实际部署动作待执行
- 目标:
  - `scripts/gaokao-retention-cleanup.py` 在目标主机实际安装 + cron/systemd 留痕
  - 监控 180 天窗口外的实际清理结果
- 依赖:
  - `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` §8 acceptance 步骤已就绪
  - 6/20 conn ownership 修复已落地（bug 必现，6/20 已修）

### L-A 隐私政策 / 服务协议正式法务审定

- Owner: PM / legal
- 优先级: P1
- 状态: pending
- 依赖:
  - 当前已有 `docs/LEGAL_PRIVACY_BASELINE.md` + `docs/PRIVACY_POLICY_DRAFT.md` + `docs/SERVICE_TERMS.md` + `docs/DATA_RETENTION_AND_DELETION.md` 基线

### L-B 备份恢复异机演练 + 密钥轮换记录

- Owner: ops
- 优先级: P1
- 状态: pending
- 依赖:
  - 当前已有 `scripts/backup_snapshot.sh` + `scripts/backup_verify.sh` + `scripts/backup_restore_smoke.py`

### Q-A crowd_db 非湖南省份高置信数据密度

- Owner: data
- 优先级: P1
- 状态: pending
- 目标:
  - 提升非湖南 crowd_db 数据置信度

### A-2 后台/外部渠道补录同意审计统一化（6/20 完成）

- Owner: engineer
- 优先级: P1
- 状态: ✅ completed（6/20 已落地）
- 目标:
  - 闲鱼/微信/学校/web 渠道代录/补录走同一同意审计口径
  - 同意字段写入 `order_intakes` 表 + `orders` 表冗余
- 落地: `CreateOrderRequest.consent: ConsentInfo` 必填；4 个 source 一致；`consent_operator` 严格按基线白名单 `self / guardian / admin_import`
- 提交: `187b2ae` → `bd27b01`

---

## 4. 当前仍然禁止的错误完成表述

禁止:

- "已完成完整 Web 自助 SaaS"
- "支付线上 acceptance 已完成"
- "27省高质量推荐数据已完成"
- "T12 Web 自助闭环已全部完成"
- "T12-D 已生产化部署"（仅"端到端本地 acceptance 步骤就绪" + "代码 conn ownership bug 修复" — 实际部署动作待 ops 执行）

允许:

- "v2.1.1 已完成 retention cleanup 多订单 conn ownership 修复 + 端到端本地 acceptance 步骤"
- "v2.1 人工服务运营增强系统 + 6/19 保留期门禁 + 支付失败持久化 + 前台删除工单 + 6/20 retention cleanup conn ownership 修复已落地"
- "T12 Web 自助闭环仍在线上 acceptance 阶段"
- "支付 / 交付 / 合规 / 备份恢复仍是当前有效问题"

---

## 5. 当前推荐读取顺序

1. `docs/CURRENT_STATE.md`
2. `docs/ACTIVE_REMEDIATION_2026-06-20.md`
3. `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`（本文件）
4. `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` §8（T12-D acceptance 步骤）
5. `docs/plans/2026-06-19-production-readiness-remediation-plan.md`
6. `reports/PRODUCTION_STRICT_REVIEW_2026-06-19.md`
7. `product/PRD.md` / `product/ROADMAP.md`

---

## 6. 下一步执行建议

最优先（6/20 后续）:

1. 推进 L-A 隐私政策法务审定
2. 推进 A-2 后台/外部渠道补录同意审计统一化
3. 推进 T12-D 实际生产化部署动作（ops 在目标主机执行）

原因:

- L-A 与 A-2 都是 P1 且不依赖外部商户/域名前置
- T12-D 实际部署动作依赖 ops 主机访问，6/20 已提供完整 acceptance 步骤与部署前 checklist
- 这三项完成后，下一阶段（v2.2）才有干净的合规与生产化基线
