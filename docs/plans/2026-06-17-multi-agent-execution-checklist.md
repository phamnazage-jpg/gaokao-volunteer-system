# Multi-Agent Execution Checklist

> **Execution entry:** 以后续执行为目标时，本文件作为“多子代理拆分与验证闸门”入口；任务优先级仍以 `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md` 为准。

**Goal:** 把统一任务清单拆成可由多个子代理分别执行的工作流，同时建立任务级、批次级、总体验证级三层闸门，确保全部优化目标真正收口，而不是只完成局部改动。

**Controller rule:** 允许多个子代理并行，但只允许在“文件边界明确且无冲突”的前提下并行；存在共享文件的任务必须合并到同一工作流内串行执行。

**Verification rule:** 任何子代理都不能用“应该通过”“理论上完成”作为完成标记。每个任务都必须附带新鲜的验证命令、退出码和关键结果。

---

## 1. 控制器与子代理角色

### 1.1 主控代理

负责：

- 维护唯一执行面：
  - `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`
  - `docs/plans/2026-06-17-multi-agent-execution-checklist.md`
- 分发任务给独立子代理
- 维护文件锁与依赖顺序
- 审核每个子代理提交的验证证据
- 汇总批次结果并决定是否进入下一批

### 1.2 每条工作流的标准角色

每个工作流固定使用三类子代理：

1. 实施代理
   - 只负责该工作流内的实现、测试、文档更新、自检
2. 规格评审代理
   - 检查是否严格满足统一任务清单，不允许漏项或额外扩张
3. 代码质量评审代理
   - 检查可维护性、测试质量、边界条件、回归风险

### 1.3 全局收口代理

在全部工作流完成后，额外使用两个全局代理：

1. 集成验证代理
   - 跑跨模块回归与端到端恢复/支付/审计链路验证
2. 结项审计代理
   - 对照 `reports/COMPREHENSIVE_SYSTEM_REVIEW_2026-06-17.md` 和统一任务清单逐项销账

---

## 2. 执行前置条件

### 2.1 先处理当前工作树冲突风险

当前已观察到未提交改动：

- `admin/routes/web_public.py`
- `admin/tests/test_web_public.py`

因此执行前必须先做以下动作：

1. 主控代理确认这些改动是否属于仍在执行的 6/16 优化分支
2. 如果属于在途工作，支付相关工作流必须基于最新内容继续，不能覆盖
3. 如果要真正并行执行，优先使用独立 worktree 或独立分支，而不是让多个子代理直接改同一工作树

### 2.2 真相源冻结

在本轮执行期间，以下文件视为真相源，修改必须经过主控代理确认：

- `docs/CURRENT_STATE.md`
- `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md`
- `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`

### 2.3 完成标记规则

任一任务只有在同时满足下面 4 条时才允许标记为完成：

1. 代码或文档改动已落地
2. 该任务列出的定向验证命令已重新执行
3. 规格评审代理判定通过
4. 代码质量评审代理判定通过

---

## 3. 工作流拆分

## WF-A 支付与 Portal 一致性工作流

**范围**

- P0-2 生产支付 provider fail-closed
- P0-3 修复退款后成功回调重入
- P1-1 建立“每订单单一活跃支付单”保护

**原因**

- 这些任务共享支付状态机、portal 阶段推导与 `web_public.py`
- 如果拆成多个代理并行修改，高概率互相覆盖

**主要文件锁**

- `admin/config.py`
- `admin/app.py`
- `admin/routes/web_public.py`
- `admin/tests/test_web_public.py`
- `admin/tests/test_p2_4_p2_5_secrets.py`
- `data/payments/service.py`
- `data/payments/dao.py`
- `data/payments/tests/test_service.py`
- `data/payments/tests/test_webhook.py`

**执行顺序**

1. P0-2
2. P0-3
3. P1-1

**子代理交付物**

- 生产环境支付 fail-closed 政策
- 退款后 webhook replay 回归测试与修复
- 单订单单活跃支付保护与 portal 阶段回归测试

**工作流验收**

- `GAOKAO_ENV=prod` 下禁止 `mock/alipay_sim`
- 退款后成功回调重放不再把 `refunded` 回写成 `paid`
- 单订单不会生成多条活跃 payment
- portal 页面的阶段推导与订单状态一致

**建议验证命令**

```bash
./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py
./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py
```

---

## WF-B 规则审计与可信化工作流

**范围**

- P0-4 让 `gaokao-cli audit run` 真正执行省规则
- P2-2 规则可信化扩面

**原因**

- 两项都围绕规则真相源、审计引擎和规则 CLI
- 先修“是否执行”，再扩“规则可信度”

**主要文件锁**

- `data/rules/audit_engine.py`
- `data/rules/cli.py`
- `data/rules/loader.py`
- `rules/_truth/national.yaml`
- `rules/_truth/province/*.yaml`
- `tests/test_audit_cli_major_validation_phase2.py`
- `tests/test_audit_engine_major_validation_phase2.py`

**执行顺序**

1. P0-4
2. P2-2

**子代理交付物**

- `max_volunteers` 等省规则接入 `AuditEngine.audit_plan()`
- 规则可信化扩面设计与实现
- 逐省证据矩阵或等价真相源字段

**工作流验收**

- 明显超志愿数时，`overall_pass` 返回失败
- CLI 输出包含结构化规则失败信息
- 规则数据包含版本/更新时间或等价可信字段

**建议验证命令**

```bash
./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py
./.venv/bin/python -m data.rules.cli audit run --help
```

---

## WF-C 备份、恢复与工程门禁工作流

**范围**

- P0-5 修复 WAL 管理库快照假成功
- P1-3 扩大备份范围
- P1-4 提升 restore smoke 真实性
- P2-4 `dev-verify` 契约与忽略项治理

**原因**

- 四项都属于“验收可信度底座”
- 如果这个工作流没收口，其他工作流通过也可能是假阳性

**主要文件锁**

- `admin/db.py`
- `scripts/backup_snapshot.sh`
- `scripts/backup_restore_smoke.py`
- `scripts/dev-verify.sh`
- `tests/test_backup_workflow.py`
- `tests/test_backup_restore_service_level.py`
- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `ops/systemd/gaokao-backup.service`
- `ops/cron/gaokao-backup.crontab.example`

**执行顺序**

1. P0-5
2. P1-3
3. P1-4
4. P2-4

**子代理交付物**

- WAL 模式真实可恢复快照
- 上传目录与交付物纳入备份
- restore smoke 不再依赖伪造密钥和强制 mock provider
- `--skip-install` 真正不联网，过期忽略项被清理

**工作流验收**

- 恢复副本中的 `admin.db` 含真实表
- 恢复结果覆盖 DB、portal 上传目录、真实交付物
- 缺关键恢复条件时 smoke 明确失败
- `GAOKAO_SKIP_INSTALL=1` 不再触发联网安装

**建议验证命令**

```bash
./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

---

## WF-D 产品定位与文档真相源工作流

**范围**

- P0-1 统一产品定位与真相源口径
- P1-5 修正文档与实现的运维口径漂移

**原因**

- 两项本质上都是“文档真相源治理”
- 应由同一个代理统一措辞、边界和 current/target 结构

**主要文件锁**

- `docs/CURRENT_STATE.md`
- `README.md`
- `product/PRD.md`
- `product/ROADMAP.md`
- `product/MARKET_RESEARCH.md`
- `docs/TECH_ARCHITECTURE.md`
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- `tests/test_design_docs_substantive.py`

**执行顺序**

1. P0-1
2. P1-5

**子代理交付物**

- 单一产品定位表述
- `Current / Target` 分离后的技术架构文档
- 文档与实现一致的支付、交付、运维说明

**工作流验收**

- 不再同时出现“当前是运营增强系统”和“当前已是完整 Web 自助 SaaS”两套口径
- README、CURRENT_STATE、PRD、ROADMAP、TECH_ARCHITECTURE 一致
- runbook 状态说明与代码一致

**建议验证命令**

```bash
./.venv/bin/pytest -q tests/test_design_docs_substantive.py
```

---

## WF-E 通知通道一致性工作流

**范围**

- P1-2 修复通知多渠道唯一键设计

**原因**

- 任务边界清晰，和其他工作流的重叠较小
- 适合单独并行推进

**主要文件锁**

- `data/notifications/email_service.py`
- `data/notifications/dispatcher.py`
- 通知相关测试文件

**执行顺序**

1. P1-2

**子代理交付物**

- 含 `channel` 的唯一键策略
- 站内信与邮件并存的回归测试

**工作流验收**

- 同一订单同一事件可以安全生成多渠道通知
- 冲突不再被静默吞掉

**建议验证命令**

```bash
./.venv/bin/pytest -q tests -k notification
```

---

## WF-F 统一 CLI 命令面工作流

**范围**

- P2-1 统一 CLI 命令面

**前置依赖**

- WF-A、WF-B、WF-C 至少完成对应 P0/P1 收口

**原因**

- 统一 CLI 应建立在支付、备份、规则主链稳定之后
- 否则会把不稳定能力包装成统一入口，放大错误面

**主要文件锁**

- CLI 聚合入口相关文件
- `order/share/delivery/retention/payment/backup/channel/doctor` 子命令相关模块

**工作流验收**

- 形成统一 `gaokao-cli {order,share,delivery,retention,payment,backup,channel,doctor}`
- 帮助信息、参数约定、错误返回风格统一

**建议验证命令**

```bash
./.venv/bin/python -m data.rules.cli --help
./.venv/bin/pytest -q tests -k "cli or doctor"
```

---

## WF-G 专业目录可信化扩面工作流

**范围**

- P2-3 专业目录可信化扩面

**前置依赖**

- WF-B 已完成规则主链收口

**主要文件锁**

- `data/majors_catalog/*`
- 相关专业目录映射、验证与变更分析测试

**工作流验收**

- 国家目录与校级招生专业之间存在正式映射
- 引入近两年增减风险标签或等价风险字段
- 形成版本化更新策略

**建议验证命令**

```bash
./.venv/bin/pytest -q tests -k "majors or catalog"
```

---

## 4. 并行批次划分

## Batch 0：执行准备

只允许主控代理执行：

1. 确认当前脏文件归属
2. 选定并行策略：
   - 独立 worktree
   - 独立分支
3. 冻结统一任务清单为本轮基线
4. 为每个工作流分配唯一负责人

**Batch 0 完成标志**

- 已消除“多个子代理直接写同一工作树”的风险

## Batch 1：P0 主链止血

允许并行：

- WF-A 执行 P0-2、P0-3
- WF-B 执行 P0-4
- WF-C 执行 P0-5

暂不启动：

- WF-D
- WF-E
- WF-F
- WF-G

**Batch 1 通过条件**

- 所有 P0 技术缺陷都有定向测试通过证据
- 主控代理完成跨工作流回归抽查

## Batch 2：口径统一与 P1 主链闭环

允许并行：

- WF-D 执行 P0-1、P1-5
- WF-A 执行 P1-1
- WF-E 执行 P1-2
- WF-C 执行 P1-3、P1-4

**Batch 2 通过条件**

- 文档真相源统一
- 支付/通知/灾备主链无已知 P1 缺口

## Batch 3：恢复 6/16 优化主线

允许并行：

- WF-F 执行 P2-1
- WF-B 执行 P2-2
- WF-G 执行 P2-3
- WF-C 执行 P2-4

**Batch 3 通过条件**

- CLI、规则可信化、专业目录可信化、工程门禁治理全部完成

---

## 5. 每个工作流的标准执行模板

主控代理给每个子代理的任务单必须至少包含：

1. 工作流编号与目标
2. 允许修改的文件清单
3. 禁止触碰的共享文件清单
4. 依赖的上游工作流状态
5. 定向验证命令
6. 必须补的回归测试
7. 完成后需要提交给哪两个评审代理

标准流程固定为：

1. 实施代理完成改动与自测
2. 规格评审代理逐条对照统一任务清单审核
3. 如有缺口，退回实施代理修复
4. 代码质量评审代理审核实现质量与测试完整性
5. 如有缺口，再退回实施代理修复
6. 主控代理验收验证证据并更新执行面

---

## 6. 总体验证与结项标准

## 6.1 子任务全部完成不等于项目收口

只有在以下项目全部满足时，才能认为“整体优化目标完全完成”：

1. 统一任务清单中的 P0、P1、P2 项全部销账
2. 每个工作流都有定向测试通过证据
3. 至少完成一次跨工作流集成验证
4. 评审报告中的关键发现有明确闭环记录
5. 文档真相源、执行面、实现状态三者一致

## 6.2 集成验证代理必须执行的项目

```bash
./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py
./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py
./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py
./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
./.venv/bin/pytest -q tests/test_design_docs_substantive.py
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

如其中任何一项失败：

- 不允许宣布“优化目标完成”
- 必须回退到对应工作流继续修复

## 6.3 结项审计代理必须输出的结论

结项时必须给出三段结论：

1. 已关闭项
   - 对应统一任务清单编号
   - 对应验证证据
2. 风险余项
   - 如果还有风险，不能写成“已完成”
3. 是否达到最终结项标准
   - 只有全部条件满足时才能写“是”

---

## 7. 当前推荐的直接执行方式

如果现在就开始执行，推荐按下面方式分派：

1. 子代理 A：WF-A `支付与 Portal 一致性`
2. 子代理 B：WF-B `规则审计与可信化`
3. 子代理 C：WF-C `备份、恢复与工程门禁`
4. 子代理 D：WF-D `产品定位与文档真相源`
5. 子代理 E：WF-E `通知通道一致性`
6. 子代理 F：WF-F `统一 CLI 命令面`
7. 子代理 G：WF-G `专业目录可信化扩面`

但真正启动顺序必须遵守批次门禁：

- 先 Batch 0
- 再 Batch 1
- Batch 1 过后才能开 Batch 2
- Batch 2 过后才能开 Batch 3

---

## 8. 建议的执行入口

后续若要正式开始多子代理执行，建议以本文件作为分发入口，以统一任务清单作为优先级依据：

- `docs/plans/2026-06-17-multi-agent-execution-checklist.md`
- `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`
- `docs/plans/2026-06-17-subagent-work-orders.md`
- `docs/ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17.md`

这两个文件的分工是：

- 统一任务清单：回答“先做什么”
- 多子代理执行清单：回答“由谁做、怎么并行、怎么验收、何时算真正完成”

新增两份执行文件的分工是：

- 子代理派工单：回答“每个代理具体做什么、改哪些文件、跑哪些命令、如何回传”
- 多代理执行看板：回答“当前做到哪一批、谁已完成、哪些证据已到位、goal 何时可以结项”
