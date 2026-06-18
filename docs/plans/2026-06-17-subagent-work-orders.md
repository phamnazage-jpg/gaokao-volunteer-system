# Subagent Work Orders

> **Goal linkage:** 本文件服务于当前 active goal，目标是完成 2026-06-17 统一整改与优化目标，并在全部工作流完成后完成跨模块集成验证与结项审计。
>
> **Use with:**
> - `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`
> - `docs/plans/2026-06-17-multi-agent-execution-checklist.md`
> - `docs/ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17.md`

**Purpose:** 为 A-G 七个子代理生成可直接执行的逐条派工单。每个派工单都包含范围、依赖、文件边界、执行步骤、验证命令、回传格式和完成标准。

---

## 0. 全体子代理通用规则

### 0.1 必读材料

开始执行前必须先读：

1. `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`
2. `docs/plans/2026-06-17-multi-agent-execution-checklist.md`
3. 与自己工作流直接相关的代码与测试文件

### 0.2 禁止事项

- 不得修改未授权文件
- 不得跳过测试就宣称完成
- 不得跨工作流“顺手修复”别人的问题
- 不得覆盖当前工作树中的在途改动
- 不得把“预期通过”当成验证结果

### 0.3 回传格式

每个子代理完成后必须按以下格式回传：

1. 本次完成的任务编号
2. 实际修改的文件清单
3. 新增或更新的测试
4. 执行过的验证命令
5. 每条验证命令的退出码与关键结果
6. 剩余风险
7. 是否提交给规格评审代理
8. 是否提交给代码质量评审代理

### 0.4 完成判定

以下四项缺一不可：

1. 任务内要求的改动已完成
2. 任务内要求的回归测试已执行
3. 规格评审代理通过
4. 代码质量评审代理通过

---

## A 号子代理派工单

**工作流:** WF-A 支付与 Portal 一致性  
**批次:** Batch 1 起步，Batch 2 继续  
**对应任务:** P0-2、P0-3、P1-1

### A-1 目标

在不破坏当前支付主链的前提下，完成以下三件事：

1. 生产环境支付 provider fail-closed
2. 修复退款后成功回调重入导致的状态回写
3. 建立“每订单单一活跃支付单”保护

### A-2 允许修改的文件

- `admin/config.py`
- `admin/app.py`
- `admin/routes/web_public.py`
- `admin/tests/test_web_public.py`
- `admin/tests/test_p2_4_p2_5_secrets.py`
- `data/payments/service.py`
- `data/payments/dao.py`
- `data/payments/tests/test_service.py`
- `data/payments/tests/test_webhook.py`

### A-3 禁止修改的文件

- `scripts/backup_*`
- `data/rules/*`
- `docs/CURRENT_STATE.md`
- `product/*`

### A-4 执行步骤

1. 先确认当前 `admin/routes/web_public.py` 与 `admin/tests/test_web_public.py` 的在途改动内容，避免覆盖
2. 为 `prod + mock/alipay_sim` 写失败测试
3. 实现生产环境 provider fail-closed
4. 为退款后 webhook replay 写回归测试
5. 修复 `refunded -> paid` 的终态回写问题
6. 为重复创建活跃 payment 写测试
7. 在 DAO 或 service 层建立单订单单活跃 payment 保护
8. 校验 portal 阶段推导不会被错误 payment 记录拖回 `pending_payment`

### A-5 必跑验证命令

```bash
./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py
./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py
```

### A-6 交付标准

- `GAOKAO_ENV=prod` 下禁止 `mock/alipay_sim`
- 退款后重复回调保持 `refunded` 终态
- 单订单不会生成多条活跃 payment
- portal 页面状态与订单真实状态一致

### A-7 回传给谁

1. 规格评审代理 `A-spec`
2. 代码质量评审代理 `A-quality`

---

## B 号子代理派工单

**工作流:** WF-B 规则审计与可信化  
**批次:** Batch 1 起步，Batch 3 继续  
**对应任务:** P0-4、P2-2

### B-1 目标

先让 `gaokao-cli audit run` 真正执行省规则，再推进规则可信化扩面。

### B-2 允许修改的文件

- `data/rules/audit_engine.py`
- `data/rules/cli.py`
- `data/rules/loader.py`
- `rules/_truth/national.yaml`
- `rules/_truth/province/*.yaml`
- `tests/test_audit_cli_major_validation_phase2.py`
- `tests/test_audit_engine_major_validation_phase2.py`
- 与规则证据层直接相关的新增测试

### B-3 禁止修改的文件

- `data/payments/*`
- `scripts/backup_*`
- `docs/CURRENT_STATE.md`
- `product/*`

### B-4 执行步骤

1. 用最小复现先证明当前 `audit run` 对省规则漏检
2. 为 `max_volunteers` 等规则补失败测试
3. 把省规则接入 `AuditEngine.audit_plan()`
4. 让 CLI 返回结构化失败信息
5. 在 P0 收口后，再推进规则可信化扩面
6. 为版本、更新时间、证据矩阵等可信字段补测试或校验

### B-5 必跑验证命令

```bash
./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py
./.venv/bin/python -m data.rules.cli audit run --help
```

### B-6 交付标准

- 超志愿数时返回结构化失败
- `overall_pass` 不再对明显违规输入返回 `true`
- 规则真相源带有可信化字段或等价证据结构

### B-7 回传给谁

1. 规格评审代理 `B-spec`
2. 代码质量评审代理 `B-quality`

---

## C 号子代理派工单

**工作流:** WF-C 备份、恢复与工程门禁  
**批次:** Batch 1 起步，Batch 2/3 继续  
**对应任务:** P0-5、P1-3、P1-4、P2-4

### C-1 目标

把“备份可恢复”和“验证可信”这条底座真正做实，避免所有后续验收建立在假阳性上。

### C-2 允许修改的文件

- `admin/db.py`
- `scripts/backup_snapshot.sh`
- `scripts/backup_restore_smoke.py`
- `scripts/dev-verify.sh`
- `tests/test_backup_workflow.py`
- `tests/test_backup_restore_service_level.py`
- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `ops/systemd/gaokao-backup.service`
- `ops/cron/gaokao-backup.crontab.example`

### C-3 禁止修改的文件

- `data/payments/*`
- `data/rules/*`
- `docs/CURRENT_STATE.md`
- `product/*`

### C-4 执行步骤

1. 为 WAL 快照假成功问题补回归测试
2. 修复 WAL 模式下 `admin.db` 的真实快照方式
3. 把 `GAOKAO_PORTAL_UPLOAD_DIR` 和真实交付物纳入备份
4. 让 restore smoke 不再依赖伪造密钥和强制 `mock` provider
5. 修复 `GAOKAO_SKIP_INSTALL=1` 仍联网安装的问题
6. 清理 `PRE_EXISTING_IGNORES` 中过期项

### C-5 必跑验证命令

```bash
./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

### C-6 交付标准

- 备份副本中的 `admin.db` 具备真实表结构
- 恢复范围覆盖 DB、portal 上传目录、真实交付物
- 缺恢复条件时 smoke 明确失败
- `--skip-install` 不再触发联网安装

### C-7 回传给谁

1. 规格评审代理 `C-spec`
2. 代码质量评审代理 `C-quality`

---

## D 号子代理派工单

**工作流:** WF-D 产品定位与文档真相源  
**批次:** Batch 2  
**对应任务:** P0-1、P1-5

### D-1 目标

统一产品定位、技术架构和运维文档口径，让真相源、路线图和实现状态不再互相打架。

### D-2 允许修改的文件

- `docs/CURRENT_STATE.md`
- `README.md`
- `product/PRD.md`
- `product/ROADMAP.md`
- `product/MARKET_RESEARCH.md`
- `docs/TECH_ARCHITECTURE.md`
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- `tests/test_design_docs_substantive.py`

### D-3 禁止修改的文件

- 任意业务代码文件
- `data/payments/*`
- `data/rules/*`
- `scripts/backup_*`

### D-4 执行步骤

1. 先写文档一致性测试，锁死“当前是运营增强系统，不是完整 Web 自助 SaaS”口径
2. 收敛 README、CURRENT_STATE、PRD、ROADMAP、MARKET_RESEARCH 的定位描述
3. 把 `TECH_ARCHITECTURE.md` 改成 `Current / Target` 结构
4. 修正 runbook 中与实现不一致的状态说明
5. 检查文档之间不存在互相冲突的里程碑和产品承诺

### D-5 必跑验证命令

```bash
./.venv/bin/pytest -q tests/test_design_docs_substantive.py
```

### D-6 交付标准

- 不再同时出现两种产品定位
- 文档对外边界一致
- 运维说明与当前实现一致

### D-7 回传给谁

1. 规格评审代理 `D-spec`
2. 代码质量评审代理 `D-quality`

---

## E 号子代理派工单

**工作流:** WF-E 通知通道一致性  
**批次:** Batch 2  
**对应任务:** P1-2

### E-1 目标

修复通知多渠道唯一键设计，允许同一订单同一事件安全地产生 `station` 与 `email` 两类通知。

### E-2 允许修改的文件

- `data/notifications/email_service.py`
- `data/notifications/dispatcher.py`
- 通知相关测试文件

### E-3 禁止修改的文件

- `data/payments/*`
- `data/rules/*`
- `scripts/backup_*`
- `docs/CURRENT_STATE.md`

### E-4 执行步骤

1. 先证明当前唯一键会吞掉多渠道通知
2. 写失败测试，覆盖 `station + email` 共存
3. 调整唯一键设计，把 `channel` 纳入冲突边界
4. 补足冲突处理与分发回归测试

### E-5 必跑验证命令

```bash
./.venv/bin/pytest -q tests -k notification
```

### E-6 交付标准

- 同一订单同一事件可以生成多渠道通知
- 冲突不再被静默吞掉

### E-7 回传给谁

1. 规格评审代理 `E-spec`
2. 代码质量评审代理 `E-quality`

---

## F 号子代理派工单

**工作流:** WF-F 统一 CLI 命令面  
**批次:** Batch 3  
**对应任务:** P2-1

### F-1 启动前提

只有当以下前置完成后才能启动：

1. WF-A 完成对应 P0/P1 收口
2. WF-B 完成 P0 收口
3. WF-C 完成对应 P0/P1 收口

### F-2 目标

形成统一的 `gaokao-cli {order,share,delivery,retention,payment,backup,channel,doctor}` 命令面。

### F-3 允许修改的文件

- CLI 聚合入口文件
- `order/share/delivery/retention/payment/backup/channel/doctor` 对应 CLI 模块
- `docs/CLI_API_MAPPING.md`
- CLI 相关测试文件

### F-4 禁止修改的文件

- `rules/_truth/*`
- `data/majors_catalog/*` 数据文件
- 支付、规则、备份底层真相源实现文件

### F-5 执行步骤

1. 盘点当前已经存在的 CLI 子命令能力
2. 设计统一入口与帮助信息风格
3. 接入最小 `doctor` 自检能力
4. 保持旧 wrapper 兼容并加 deprecation warning
5. 更新 CLI 映射文档

### F-6 必跑验证命令

```bash
./.venv/bin/python -m data.rules.cli --help
./.venv/bin/pytest -q tests -k "cli or doctor"
```

### F-7 交付标准

- 命令面统一
- 帮助信息统一
- 错误返回风格统一
- 文档与实现一致

### F-8 回传给谁

1. 规格评审代理 `F-spec`
2. 代码质量评审代理 `F-quality`

---

## G 号子代理派工单

**工作流:** WF-G 专业目录可信化扩面  
**批次:** Batch 3  
**对应任务:** P2-3

### G-1 启动前提

只有当 WF-B 已完成规则主链收口后才能启动。

### G-2 目标

在已有 national + school skeleton 基础上，建立正式映射、风险标签和版本化更新策略。

### G-3 允许修改的文件

- `data/majors_catalog/*`
- 专业目录映射、版本、变化分析相关测试
- 专业目录可信化说明文档

### G-4 禁止修改的文件

- `data/payments/*`
- `scripts/backup_*`
- `docs/CURRENT_STATE.md`
- `product/*`

### G-5 执行步骤

1. 盘点现有国家目录与校级目录骨架
2. 建立国家目录到校级招生专业的正式映射
3. 引入近两年专业增减风险标签或等价风险字段
4. 建立版本化更新策略和验证逻辑
5. 补充 lookup / verify / changes 相关回归测试

### G-6 必跑验证命令

```bash
./.venv/bin/pytest -q tests -k "majors or catalog"
```

### G-7 交付标准

- 国家目录与校级目录存在正式映射
- 风险标签可被验证和读取
- 版本化更新策略落地

### G-8 回传给谁

1. 规格评审代理 `G-spec`
2. 代码质量评审代理 `G-quality`

---

## 9. 主控代理批次推进规则

### 9.1 Batch 0

主控代理先完成：

1. 确认当前脏文件归属
2. 确认并行策略是独立 worktree 还是独立分支
3. 把 `docs/ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17.md` 初始化为本轮唯一执行看板

### 9.2 Batch 1

启动：

- A 号子代理
- B 号子代理
- C 号子代理

### 9.3 Batch 2

只有当 Batch 1 全部有验证证据后，才能启动：

- D 号子代理
- E 号子代理
- A 号子代理的 P1-1 后续任务
- C 号子代理的 P1-3 / P1-4 后续任务

### 9.4 Batch 3

只有当 Batch 2 收口后，才能启动：

- F 号子代理
- G 号子代理
- B 号子代理的 P2-2 后续任务
- C 号子代理的 P2-4 后续任务

---

## 10. 最终验证责任

全部子代理完成后，不允许直接宣布目标完成。主控代理必须再分派：

1. 集成验证代理
2. 结项审计代理

只有在以下条件全部满足时，active goal 才允许标记完成：

1. P0/P1/P2 全部销账
2. 所有工作流验证通过
3. 跨工作流集成验证通过
4. 结项审计代理确认评审发现全部闭环
