# ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17

> 真相源: `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`
> 执行清单: `docs/plans/2026-06-17-multi-agent-execution-checklist.md`
> 派工单: `docs/plans/2026-06-17-subagent-work-orders.md`
> Goal: active，目标为“完成 2026-06-17 统一整改与优化目标，并在全部工作流完成后完成跨模块集成验证与结项审计”
> 状态口径: `未启动 / 进行中 / 待评审 / 已通过 / 阻塞`

---

## 1. 总体目标

本看板用于和 active goal 同步，跟踪：

- P0 / P1 / P2 任务销账
- A-G 七个子代理执行状态
- 每批次验证证据
- 最终集成验证与结项审计结果

---

## 2. 当前批次状态

- Batch 0: 已通过
- Batch 1: 已通过
- Batch 2: 已通过
- Batch 3: 已通过
- 集成验证: 已通过
- 结项审计: 未启动

---

## 3. 子代理状态总览

| 代理 | 工作流 | 任务范围 | 当前状态 | 前置依赖 | 验证证据 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| A | 支付与 Portal 一致性 | P0-2 / P0-3 / P1-1 | 已通过 | Batch 0 | `pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py` => `34 passed in 3.89s`；`pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py` => `13 passed in 1.52s` | P0-2/P0-3/P1-1 已拿到完整退出码证据 |
| B | 规则审计与可信化 | P0-4 / P2-2 | 已通过 | Batch 0 | `pytest -q tests/test_rules_truth_phase1.py tests/test_rules_cli_phase1.py tests/test_rules_evidence_layer.py tests/test_cli_doctor_phase3.py tests/test_legacy_checker_truth_wrapper.py` => `345 passed in 4.00s`；`python scripts/gaokao-cli rules scaffold-evidence --json` => `created_rule_count=286`；`python scripts/gaokao-cli rules status --json` / `rules verify --json` / `doctor --json` exit `0` | P0-4 已闭环；P2-2 已补 version/last_verified_at、evidence matrix、`rules list/explain`、stale 告警与 evidence 模板脚手架，北京/湖南/江苏/浙江/上海/安徽/山东/广东/湖北/河北/海南/福建/四川/江西/甘肃/贵州/云南/辽宁/吉林/黑龙江/广西/青海/西藏/新疆/天津/河南/重庆均已完成 `11/11`，当前 active 省份 evidence 缺口已清零 |
| C | 备份、恢复与工程门禁 | P0-5 / P1-3 / P1-4 / P2-4 | 已通过 | Batch 0 | `pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py` => `8 passed in 2.30s`；`env GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh --skip-pre-existing` => `1013 passed, 1 deselected` + `coverage gate summary: overall=90.35%, core=100.00%` + `mypy Success` | P0-5/P1-3/P1-4/P2-4 已验证通过，`dev-verify` 已收紧到只忽略 locust 探针 |
| D | 产品定位与文档真相源 | P0-1 / P1-5 | 已通过 | Batch 1 完成 | `pytest -q tests/test_design_docs_substantive.py` => `6 passed` | P0-1/P1-5 已完成并补齐回归测试 |
| E | 通知通道一致性 | P1-2 | 已通过 | Batch 1 完成 | `pytest -q tests/test_delivery_notification.py tests/test_delivery_dispatcher.py` => `13 passed`；`pytest -q tests -k notification` => `6 passed, 322 deselected` | 通知唯一键已收口到 `(order_id, event_type, channel)`，同事件支持 `station/email` 并存 |
| F | 统一 CLI 命令面 | P2-1 | 已通过 | Batch 2 完成 | `pytest -q tests/test_cli_doctor_phase3.py` => `12 passed`；`python scripts/gaokao-cli --help` exit `0` | 顶层 help 已显式暴露 `order/share/payment/channel/delivery/retention/backup/doctor` 统一命令面，预委派逻辑保持兼容 |
| G | 专业目录可信化扩面 | P2-3 | 已通过 | WF-B P0 收口 + Batch 2 完成 | `pytest -q tests/test_majors_catalog_phase2.py tests/test_majors_cli_phase2.py tests/test_majors_school_catalog_phase2.py tests/test_majors_school_cli_phase2.py` => `12 passed`；`python scripts/gaokao-cli majors status/verify/school-status/school-verify --json` exit `0` | 已收口显式 national 映射、风险标签与版本策略，但当前仍仅 1 所学校样本 |

### 3.1 当前已分发代理实例

- A 号代理：`Copernicus` / `019ed60b-1f3c-7a81-a41a-419999e22a24`
  - 范围：P0-2、P0-3
- B 号代理：`Rawls` / `019ed60b-535b-7b70-9dcb-78a410a7a358`
  - 范围：P0-4
- C 号代理：`Wegener` / `019ed60b-7fb3-7f10-b8f8-8b79208c53b3`
  - 范围：P0-5

---

## 4. P0 / P1 / P2 销账看板

### 4.1 P0

- [x] P0-1 统一产品定位与真相源口径
- [x] P0-2 生产支付 provider fail-closed
- [x] P0-3 修复退款后成功回调重入导致的状态回写
- [x] P0-4 让 `gaokao-cli audit run` 真正执行省规则
- [x] P0-5 修复 WAL 管理库快照假成功

### 4.2 P1

- [x] P1-1 建立“每订单单一活跃支付单”保护
- [x] P1-2 修复通知多渠道唯一键设计
- [x] P1-3 扩大备份范围，覆盖 portal 上传目录与真实交付物
- [x] P1-4 提升 restore smoke 真实性
- [x] P1-5 修正文档与实现的运维口径漂移

### 4.3 P2

- [x] P2-1 统一 CLI 命令面
- [x] P2-2 规则可信化扩面
- [x] P2-3 专业目录可信化扩面
- [x] P2-4 `dev-verify` 契约与忽略项治理

---

## 5. 批次推进门禁

### 5.1 Batch 0 通过条件

- [x] 已确认当前脏文件归属
- [x] 已确定并行执行策略
- [x] 已给 A-G 子代理分配唯一负责人

### 5.1.1 Batch 0 结论记录

- 当前 `git status --short --branch` 显示：代码工作树无在途业务代码改动，当前仅有本轮新增文档未跟踪文件。
- 原先担心的 `admin/routes/web_public.py` 与 `admin/tests/test_web_public.py` 在途改动，当前工作树中不存在，视为已消除文件冲突前置风险。
- 并行策略采用：`multi_agent_v1` worker 子代理 + 各自 forked workspace。
- Batch 1 启动授权范围：
  - A 号代理独占支付与 portal 文件集
  - B 号代理独占规则审计与规则真相源文件集
  - C 号代理独占备份、恢复与工程门禁文件集

### 5.2 Batch 1 通过条件

- [x] A 号子代理提交 P0-2 / P0-3 验证证据
- [x] B 号子代理提交 P0-4 验证证据
- [x] C 号子代理提交 P0-5 验证证据
- [x] 主控代理完成跨工作流抽查

### 5.2.1 Batch 1 当前结论

- `P0-4` 已完成并通过双评审：
  - 主控 fresh 验证：`./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py` => `8 passed`
  - 主控 fresh 验证：`./.venv/bin/python -m data.rules.cli audit run --help` => exit `0`
  - 规格评审：`PASS`
  - 代码质量评审：`APPROVED`
- `P0-5 / P1-4` 当前状态已更新为“验证通过”：
  - 主控 fresh 验证：`./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py` => `8 passed in 2.30s`
  - 结论：WAL 快照与 restore smoke 真实性回归已一起通过，WF-C 不再被既有超时问题阻塞
- `P0-2 / P0-3` 当前状态已更新为“验证通过”：
  - 主控 fresh 验证：`./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py` => `34 passed in 3.89s`
  - 主控 fresh 验证：`./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py` => `13 passed in 1.52s`
  - 结论：生产 provider fail-closed、模拟支付入口隔离、退款终态保护均已拿到完整退出码证据；原 `TestClient` 阻塞已由路由直调测试收口

### 5.3 Batch 2 通过条件

- [x] D 号子代理提交 P0-1 / P1-5 验证证据
- [x] A 号子代理提交 P1-1 验证证据
- [x] E 号子代理提交 P1-2 验证证据
- [x] C 号子代理提交 P1-3 / P1-4 验证证据

### 5.3.1 Batch 2 当前结论

- `P1-3 / P1-4` 当前状态已更新为“验证通过”：
  - 主控 fresh 验证：`./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py` => `8 passed in 2.30s`
  - 结论：快照与 live verify 现在都会覆盖 `portal_uploads` 与订单挂载交付物，restore smoke 证据链维持通过，WF-C 当前仅剩 `P2-4`

### 5.4 Batch 3 通过条件

- [x] F 号子代理提交 P2-1 验证证据
- [ ] B 号子代理提交 P2-2 验证证据
- [x] G 号子代理提交 P2-3 验证证据
- [x] C 号子代理提交 P2-4 验证证据

### 5.4.1 Batch 3 当前结论

- `P2-1` 当前状态已更新为“验证通过”：
  - 主控 fresh 验证：`./.venv/bin/pytest -q tests/test_cli_doctor_phase3.py` => `12 passed`
  - 主控 fresh 验证：`./.venv/bin/python scripts/gaokao-cli --help` => exit `0`
  - 结论：`gaokao-cli` 顶层命令树已显式暴露 `order/share/payment/channel/delivery/retention/backup/doctor`，与既有预委派脚本兼容，不再出现“实际可用但 help 不可发现”的命令面漂移
- `P2-2` 当前状态已更新为“验证通过”：
  - 主控 fresh 验证：`./.venv/bin/pytest -q tests/test_rules_truth_phase1.py tests/test_rules_cli_phase1.py tests/test_rules_evidence_layer.py tests/test_cli_doctor_phase3.py tests/test_legacy_checker_truth_wrapper.py` => `345 passed in 4.00s`
  - 主控 fresh 验证：`./.venv/bin/python scripts/gaokao-cli rules scaffold-evidence --json` => `created_rule_count=286`, `touched_index_count=28`
  - 主控 fresh 验证：`./.venv/bin/python scripts/gaokao-cli rules status --json` / `rules verify --json` / `doctor --json` / `rules explain HEBEI.retrieval_rule --json` => exit `0`
  - 结论：规则 truth 已显式带 `version` / `last_verified_at`，CLI 可枚举、解释和脚手架化缺失 evidence；stale 规则已接入 `rules status`、`rules verify` 与 `doctor` 总健康判定；北京、湖南、江苏、浙江、上海、安徽、山东、广东、湖北、河北、海南、福建、四川、江西、甘肃、贵州、云南、辽宁、吉林、黑龙江、广西、青海、西藏、新疆、天津、河南、重庆均已完成 `11/11`，其中重庆普通类本科批已按重庆市教育考试院 `2025-06-17` 志愿设置 / 录取规则问答、`2026-06-09` 考后时间节点安排与重庆市教委 `2025` 实施办法，将旧的 `batch: 普通批` 修正为 `本科批`、`collection_count: 1` 修正为动态机读口径 `null`，并确认 `专业+学校 / 96 / 无调剂 / 分数优先、遵循志愿、一次投档 / 3+1+2 / 750` 口径；当前 `rules status` 已推进到 `evidenced_rule_count=298`、`missing_evidence_rule_count=0`，`rules verify` 与 `doctor` 保持 `ok=true` 且 stale 计数为 `0`，因此 P2-2 已闭环
- `P2-3` 当前状态已更新为“验证通过”：
  - 主控 fresh 验证：`./.venv/bin/pytest -q tests/test_majors_catalog_phase2.py tests/test_majors_cli_phase2.py tests/test_majors_school_catalog_phase2.py tests/test_majors_school_cli_phase2.py` => `12 passed`
  - 主控 fresh 验证：`./.venv/bin/python scripts/gaokao-cli majors status --json` / `majors verify --json` / `majors school-status --year 2026 --json` / `majors school-verify --year 2026 --json` => exit `0`
  - 主控回归验证：`./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py` => `8 passed`
  - 结论：国家目录与校级目录之间已建立显式 `national_major_code` 映射契约，`changes/2024-2026.md` 与 `version_strategy` 已纳入 verify 门禁，未显式映射的校级专业会被标记为缺口；但校级样本数量仍只有 1 所，后续扩面仍属于下一批次工作

---

## 6. 集成验证证据

当前已补充：

- [x] `admin/tests/test_p2_4_p2_5_secrets.py`
- [x] `admin/tests/test_web_public.py`
- [x] `data/payments/tests/test_service.py`
- [x] `data/payments/tests/test_webhook.py`
- [x] `tests/test_audit_cli_major_validation_phase2.py`
- [x] `tests/test_audit_engine_major_validation_phase2.py`
- [x] `tests/test_backup_workflow.py`
- [x] `tests/test_backup_restore_service_level.py`
- [x] `tests/test_design_docs_substantive.py`
- [x] `GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh`

### 6.1 当前集成验证结论（2026-06-18）

- `./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py` => `34 passed in 3.89s`
- `./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py` => `13 passed in 1.52s`
- `./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py` => `8 passed`
- `./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py` => `8 passed in 2.30s`
- `./.venv/bin/pytest -q tests/test_design_docs_substantive.py` => `6 passed`
- `env GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh --skip-pre-existing` => `1013 passed, 1 deselected, 6 warnings` + `coverage gate summary: overall=90.35%, core=100.00%` + `ruff` / `mypy` 通过

---

## 7. 结项审计

只有在以下条件全部满足时，才允许把 goal 标记为完成：

- [ ] 统一任务清单中的 P0 / P1 / P2 已全部销账
- [ ] A-G 七个工作流全部通过规格评审和代码质量评审
- [x] 集成验证全部通过
- [ ] 评审报告中的关键发现已逐项闭环
- [ ] 文档真相源、执行面、实现状态一致
