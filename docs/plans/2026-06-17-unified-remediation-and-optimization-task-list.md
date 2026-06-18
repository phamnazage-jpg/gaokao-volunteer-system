# Unified Remediation And Optimization Task List

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 2026-06-16 优化主线与 2026-06-17 全面评审整改项合并成一份统一任务清单，形成唯一的后续执行优先级。

**Architecture:** 以 `docs/CURRENT_STATE.md` 和 `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md` 为真相源，先把已收口项从执行面剔除，再把当前真实阻塞按 `P0 / P1 / P2` 重排。原则是“先修会导致错误状态或假阳性验收的底层缺陷，再继续 6/16 计划里尚未完成的 CLI/真相源治理/后续优化”。

**Tech Stack:** Python 3.11, FastAPI, sqlite3, pytest, bash scripts, Markdown docs

---

## 1. 合并依据

本清单合并自以下来源：

1. `docs/plans/2026-06-16-optimization-program.md`
2. `docs/plans/2026-06-17-comprehensive-review-remediation.md`
3. `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md`
4. `docs/CURRENT_STATE.md`
5. `reports/COMPREHENSIVE_SYSTEM_REVIEW_2026-06-17.md`

合并规则：

- `6/16` 计划中**已经收口**的规则真相源、专业目录 MVP、major validation 接入，不再作为当前待办。
- `6/17` 评审中识别出的 **P0 / P1 真实缺陷**，整体前置到所有新功能和 CLI 扩展之前。
- `6/16` 中尚未完成但仍然有效的主线，例如统一 CLI 命令面、真相源治理、后续可信化扩面，保留为第二阶段。

---

## 2. 已收口，不再进入当前待办

这些任务已由 `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md` 明确收口：

### 2.1 已完成的 6/16 优化主线内容

- 规则真相源化（执行 Phase 1 / 1.5）
  - `rules/_truth/national.yaml`
  - `rules/_truth/province/*.yaml`
  - `data/rules/loader.py`
  - `data/rules/cli.py` 的 `rules {status,verify}`
- 国家级专业目录 MVP（执行 Phase 2 Batch 1）
  - `data/majors_catalog/*`
  - `majors {status,lookup,verify,changes}`
- 校级招生目录骨架（执行 Phase 2 Batch 2）
  - `school-status / school-verify`
- `audit_engine` 接入 majors 校验（执行 Phase 2 Batch 3）
  - `AuditEngine._validate_majors`
  - `gaokao-cli audit run`

### 2.2 说明

这些工作不是“完全终局态”，但已经不是当前最优先的执行面。  
后续只在以下情况下回到这些模块：

- 修复 6/17 评审指出的真实缺陷
- 做可信化扩面，而不是重复做已收口的 MVP 骨架

---

## 3. 新的统一任务优先级

---

## P0：必须先处理的阻塞项

### P0-1 统一产品定位与真相源口径

**来源**

- `6/16` Workstream D：规划/实现优化
- `6/17` 综合评审：产品定位与 MVP 边界未统一

**目标**

- 让 `CURRENT_STATE / README / PRD / ROADMAP / MARKET_RESEARCH / TECH_ARCHITECTURE` 口径一致
- 明确当前产品是“人工服务运营增强系统”，不是可对外承诺的完整 Web 自助 SaaS

**涉及文件**

- `docs/CURRENT_STATE.md`
- `README.md`
- `product/PRD.md`
- `product/ROADMAP.md`
- `product/MARKET_RESEARCH.md`
- `docs/TECH_ARCHITECTURE.md`

**验收**

- 不再同时出现两种产品定位
- 对外表述边界统一
- 评审、路线图、实现状态不再互相打架

### P0-2 生产支付 provider fail-closed

**来源**

- `6/17` 综合评审 P0

**目标**

- 禁止 `prod + mock/alipay_sim`
- 禁止生产环境暴露模拟支付入口

**涉及文件**

- `admin/config.py`
- `admin/app.py`
- `admin/routes/web_public.py`
- `.env.docker.example`

**验收**

- `GAOKAO_ENV=prod` 下，`GAOKAO_PAYMENT_PROVIDER=mock` 直接拒绝启动
- `/pay/mock/*`、`/pay/alipay-sim/*` 在生产不可用

### P0-3 修复退款后成功回调重入导致的状态回写

**来源**

- `6/17` 综合评审 P0

**目标**

- 退款后的 payment 保持终态
- 成功回调重放不得把 `payment.status` 从 `refunded` 回写到 `paid`

**涉及文件**

- `data/payments/service.py`
- `data/payments/tests/test_service.py`
- `data/payments/tests/test_webhook.py`

**验收**

- 成功回调重放只返回幂等成功
- `payment` 与 `order` 不再分裂成 `paid / refunded`

### P0-4 让 `gaokao-cli audit run` 真正执行省规则

**来源**

- `6/16` Workstream A：统一审计入口
- `6/17` 综合评审 P0：当前只做 majors 校验

**目标**

- 把 `max_volunteers` 等省规则接入 `AuditEngine.audit_plan()`

**涉及文件**

- `data/rules/audit_engine.py`
- `data/rules/cli.py`
- `tests/test_audit_cli_major_validation_phase2.py`
- `tests/test_audit_engine_major_validation_phase2.py`

**验收**

- 超志愿数能返回结构化失败
- `overall_pass` 不再在明显省规则违规时返回 `true`

### P0-5 修复 WAL 管理库快照假成功

**来源**

- `6/17` 综合评审 P0
- `6/16` Workstream D：可信运维底座

**目标**

- 让 `admin.db` 在 WAL 模式下可被真实恢复

**涉及文件**

- `admin/db.py`
- `scripts/backup_snapshot.sh`
- `tests/test_backup_workflow.py`

**验收**

- 备份副本里的 `db/admin.db` 至少包含 `admin_users`
- 不再出现“manifest 有文件，但表为空”

---

## P1：P0 收口后立刻继续

### P1-1 建立“每订单单一活跃支付单”保护

**来源**

- `6/17` 综合评审 P1

**目标**

- 防止重复创建 pending payment
- 防止 portal 页面因最新 payment 记录错误而退回 `pending_payment`

**涉及文件**

- `data/payments/dao.py`
- `data/payments/service.py`
- `admin/routes/web_public.py`
- 相关支付/portal 测试

**验收**

- 单订单不会出现多条活跃 payment
- portal 阶段推导与订单状态保持一致

### P1-2 修复通知多渠道唯一键设计

**来源**

- `6/17` 综合评审 P1
- `6/16` Workstream C：CLI/交付链路正式化

**目标**

- 允许 `station` 与 `email` 并存
- 唯一键包含 `channel`

**涉及文件**

- `data/notifications/email_service.py`
- `data/notifications/dispatcher.py`
- 通知相关测试

**验收**

- 同一订单同一事件可存在多渠道通知
- 冲突不再被静默吞掉

### P1-3 扩大备份范围，覆盖 portal 上传目录与真实交付物

**来源**

- `6/17` 综合评审 P1
- `6/16` Workstream D：运维与真相源治理

**目标**

- 把 `GAOKAO_PORTAL_UPLOAD_DIR` 纳入快照
- 补齐真实交付物覆盖

**涉及文件**

- `scripts/backup_snapshot.sh`
- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `ops/systemd/gaokao-backup.service`
- `ops/cron/gaokao-backup.crontab.example`

**验收**

- 恢复后不只 DB 在，附件与交付文件也在

### P1-4 提升 restore smoke 真实性

**来源**

- `6/17` 综合评审 P1

**目标**

- 不再用伪造密钥和强制 `mock` provider 掩盖恢复问题

**涉及文件**

- `scripts/backup_restore_smoke.py`
- `tests/test_backup_workflow.py`
- `tests/test_backup_restore_service_level.py`

**验收**

- 缺真实恢复条件时，smoke 明确失败
- 不再产生“恢复链路已验证”的假阳性

### P1-5 修正文档与实现的运维口径漂移

**来源**

- `6/16` Workstream D
- `6/17` 综合评审 P1

**目标**

- 修正 `README` 中 `ready -> sent`
- 修正 runbook 中 dispatcher 处理状态说明
- 收敛 `TECH_ARCHITECTURE` 里的现状/目标混写

**涉及文件**

- `README.md`
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- `docs/TECH_ARCHITECTURE.md`

**验收**

- 运维人员读文档时不再得到错误执行口径

---

## P2：第二阶段优化项

这些任务来自 `6/16` 优化计划，仍然有效，但要排在上述整改之后。

### P2-1 统一 CLI 命令面（执行 Phase 3，当前未启动）

**来源**

- `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md:56-68`
- `6/16` Workstream C

**目标**

- 形成统一 `gaokao-cli {order,share,delivery,retention,payment,backup,channel,doctor}`

**最小范围**

- `order`
- `share`
- `delivery`
- `retention`
- `payment`
- `backup`
- `channel`
- `doctor`

**说明**

- 这是当前 6/16 优化主线中，仍然明确“未启动”的正式执行项
- 但它必须排在支付/备份/规则审计修复之后

### P2-2 规则可信化扩面

**来源**

- `6/16` Workstream A

**目标**

- 在已完成真相源化基础上，继续做：
  - 逐省证据矩阵
  - 全国通用规则抽象
  - 规则版本与更新时间字段

**说明**

- MVP 骨架已完成
- 当前剩余的是“可信化”而不是“从零开始做规则系统”

### P2-3 专业目录可信化扩面

**来源**

- `6/16` Workstream B

**目标**

- 建立国家目录与校级招生专业之间的正式映射
- 引入近两年专业增减风险标签
- 形成版本化更新策略

**说明**

- 当前 national + school skeleton 已有
- 剩余工作是可信度与扩面，不是再造目录骨架

### P2-4 `dev-verify` 契约与忽略项治理

**来源**

- `6/17` 实现评审

**目标**

- 让 `--skip-install` 真正不联网
- 清理过期 `PRE_EXISTING_IGNORES`

**说明**

- 这是工程门禁质量问题，不是业务主链，但会持续影响回归可信度

---

## 4. 新的执行顺序

### Phase A：先止血

1. P0-2 生产支付 provider fail-closed
2. P0-3 修复退款后回调重入
3. P0-5 修复 WAL 管理库快照
4. P0-4 让 `audit run` 真执行省规则

### Phase B：统一口径

5. P0-1 统一产品定位与真相源口径
6. P1-5 修正文档与实现的运维口径漂移

### Phase C：补主链闭环

7. P1-1 单活跃支付保护
8. P1-2 通知多渠道唯一键修复
9. P1-3 扩大备份范围
10. P1-4 提升 restore smoke 真实性

### Phase D：恢复优化计划主线

11. P2-1 统一 CLI 命令面
12. P2-2 规则可信化扩面
13. P2-3 专业目录可信化扩面
14. P2-4 `dev-verify` 契约与忽略项治理

---

## 5. 对旧计划的处理方式

### 5.1 保留但不再作为直接执行入口

- `docs/plans/2026-06-16-optimization-program.md`
- `docs/plans/2026-06-17-comprehensive-review-remediation.md`

### 5.2 当前推荐执行入口

后续执行建议同时使用两份文件：

- `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`
- `docs/plans/2026-06-17-multi-agent-execution-checklist.md`

分工如下：

- 统一任务清单：负责定义唯一优先级
- 多子代理执行清单：负责定义工作流拆分、并行边界、验证闸门、总收口标准

原因：

- 第一份文件已经把“6/16 的中期优化主线”和“6/17 的新增高优先级缺陷”重新排序
- 第一份文件剔除了已收口项
- 第二份文件解决了“由谁执行、哪些可并行、哪些必须串行、何时才算真的完成”的执行问题

---

## 6. 推荐下一步

如果立刻开始执行，建议只开两批：

### Batch 1

- P0-2 生产支付 provider fail-closed
- P0-3 修复退款后回调重入
- P0-5 修复 WAL 管理库快照
- P0-4 让 `audit run` 真执行省规则

### Batch 2

- P0-1 统一产品定位与真相源口径
- P1-1 单活跃支付保护
- P1-2 通知多渠道唯一键修复
- P1-3 / P1-4 灾备链路真实性修复

---

Plan complete and saved to `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
