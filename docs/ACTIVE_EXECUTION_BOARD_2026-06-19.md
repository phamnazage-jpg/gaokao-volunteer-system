# ACTIVE_EXECUTION_BOARD_2026-06-19

> ⚠ **历史快照** — 本文件为 2026-06-19 执行板，已被 [`docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`](ACTIVE_EXECUTION_BOARD_2026-06-20.md) 取代。保留此文件仅供历史回溯；当前执行任务清单以 6/20 版本为准。
>
> **6/20 增量**: T12-D retention cleanup conn ownership 修复落地（端到端本地 acceptance 步骤就绪）— 见 `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md` §2

最后更新: 2026-06-19（已降级为历史快照）
状态词: 当前有效问题执行板
真相源: `docs/CURRENT_STATE.md`
问题来源: `docs/ACTIVE_REMEDIATION_2026-06-19.md`

> 本文件取代 `docs/ACTIVE_EXECUTION_BOARD_2026-06-13.md`（已降级为历史快照）。

---

## 1. 当前门禁结论

结论: v2.1 已完成"人工服务运营增强系统"闭环 + 6/19 增量（A1 保留期门禁 + B1 支付失败持久化 + T12-C 前台删除工单 + 文档校准）落地。
dev-verify 状态: 1179 passed, 0 failed, coverage overall=85.05% / core=100%, ruff + mypy 通过。

禁止事项：

- 不再重复处理已修复的历史问题
- 不把 T12 之外的 Web 自助能力混入已完成的 v2.1 结论
- 不把"设计占位"误报为"已实现"
- 不把 Git/文档修订当成支付/交付/合规能力的替代

---

## 2. 6/19 增量执行情况

### A1 删除/匿名化保留期门禁（P0）

- 状态: ✅ completed
- 提交范围:
  - `admin/errors/codes.py` 新增 `BIZ_ORDER_RETENTION_NOT_EXPIRED` (E02002) → HTTP 409
  - `admin/errors/registry.py` 注册中文文案
  - `admin/config.py` 新增 `retention_days` 字段（env: `GAOKAO_RETENTION_DAYS`，默认 180）
  - `admin/routes/orders.py` 入口加 `_assert_retention_expired` 守卫
  - `data/orders/deletion_service.py` 暴露 `RETENTION_GUARDED_STATUSES` 常量
  - `admin/tests/test_order_deletion.py` 新增 3 个回归用例 + `_expire_retention_window` helper
- 验证: 1175 passed, dev-verify all checks passed

### A2 文档 Current/Target 收口（P1）

- 状态: ✅ completed
- 范围:
  - `README.md` 顶部执行板指向 6/19 + 6/19 新增约束
  - `product/PRD.md` 顶部"最后更新"升级为 6/19
  - `product/ROADMAP.md` 顶部校准从 6/13 升级到 6/19
  - `docs/TECH_ARCHITECTURE.md` 顶部 Current/Target 指向 6/19

### B1 支付失败状态持久化与回归测试（P1）

- 状态: ✅ completed
- 提交范围:
  - `data/payments/service.py`: 失败 webhook 持久化（status='failed' + failure_reason）替代抛 PaymentError
  - `data/payments/dao.py`: schema 增量升级 `failed_at` / `failure_reason`，`update_status` 支持新参数
  - `data/payments/models.py`: `PaymentRecord` 新增 `failed_at` / `failure_reason`
  - `data/payments/tests/test_webhook.py`: 替换旧契约测试，新增 `test_handle_webhook_persists_failed_status`
- 验证: 1175 passed, dev-verify all checks passed

### B2 CURRENT_STATE / remediation / execution board 同步（P1）

- 状态: ✅ completed
- 范围:
  - 6/13 整改板/执行板顶部加"⚠ 历史快照"头注
  - 新建 6/19 整改板/执行板作为当前真相源
  - `docs/CURRENT_STATE.md` 顶部加 6/19 增量段

### T12-C 前台删除工单与"保留期外可申请"页（P1）

- 状态: ✅ completed（2026-06-19 落地）
- 落地:
  - `admin/routes/web_public.py` 加 `_resolve_retention_status` + `_next_step_for_retention`
  - `DeletionRequestCreate` Pydantic 锁 `scope` 到白名单 + `confirm_guardian` 强制 bool
  - `POST /portal/{token}/deletion-request` 根据订单保留期返回 3 种 next_step 文案
  - `GET /portal/{token}/deletion-request` 在表单上方加"保留期状态"提示卡
  - `admin/tests/test_order_info_form.py` 6 个新/增强测试覆盖
- 验证: 1179 passed (6 个 deletion 测试全过), dev-verify all checks passed

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

### T12-D retention cleanup 生产化部署验收

- Owner: ops
- 优先级: P1
- 状态: pending
- 目标:
  - `scripts/gaokao_retention_cleanup.py` 在目标主机实际安装 + cron/systemd 留痕
  - 监控 180 天窗口外的实际清理结果

### L-A 隐私政策 / 服务协议正式法务审定

- Owner: PM / legal
- 优先级: P1
- 状态: pending
- 依赖:
  - 当前已有 `docs/LEGAL_PRIVACY_BASELINE.md` + `docs/PRIVACY_POLICY_DRAFT.md` + `docs/DATA_RETENTION_AND_DELETION.md` 基线

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

---

## 4. 当前仍然禁止的错误完成表述

禁止:

- "已完成完整 Web 自助 SaaS"
- "支付线上 acceptance 已完成"
- "27省高质量推荐数据已完成"
- "T12 Web 自助闭环已全部完成"

允许:

- "v2.1 人工服务运营增强系统已完成 + 6/19 保留期门禁 + 支付失败持久化 + 前台删除工单已落地"
- "T12 Web 自助闭环仍在线上 acceptance 阶段"
- "支付 / 交付 / 合规 / 备份恢复仍是当前有效问题"

---

## 5. 当前推荐读取顺序

1. `docs/CURRENT_STATE.md`
2. `docs/ACTIVE_REMEDIATION_2026-06-19.md`
3. `docs/plans/2026-06-19-production-readiness-remediation-plan.md`
4. 本文件 `docs/ACTIVE_EXECUTION_BOARD_2026-06-19.md`
5. `reports/PRODUCTION_STRICT_REVIEW_2026-06-19.md`
6. `product/PRD.md` / `product/ROADMAP.md`

---

## 6. 下一步执行建议

最优先（6/19 后续）:

1. 推进 L-A 隐私政策法务审定
2. 推进 T12-D retention cleanup 生产化部署验收

原因:

- 这两个直接依赖 6/19 已落地的保留期门禁
- 不需要外部商户 / 域名前置
- 闭环后可让 v2.2 进一步推进
