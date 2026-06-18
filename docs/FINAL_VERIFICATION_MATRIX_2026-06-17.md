# FINAL_VERIFICATION_MATRIX_2026-06-17

> 用途：作为 active goal 的最终结项证据矩阵。只有本文件中的每项都拿到直接证据，才能把 goal 标记为完成。
>
> 配套文件：
> - `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`
> - `docs/plans/2026-06-17-multi-agent-execution-checklist.md`
> - `docs/ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17.md`

---

## 1. 证据判定规则

每项任务必须至少具备以下证据：

1. 直接改动文件
2. 对应测试或验证命令
3. 退出码
4. 关键输出摘要
5. 如涉及文档真相源，还要有文档内容核对

禁止使用以下弱证据代替：

- “应该已经修复”
- “代码看起来没问题”
- “子代理说完成了”
- 旧测试结果

---

## 2. P0 证据矩阵

| 任务 | 证明目标 | 主要证据文件 | 必要验证命令 | 当前状态 | 证据摘要 |
| --- | --- | --- | --- | --- | --- |
| P0-1 | 产品定位与真相源口径统一 | `docs/CURRENT_STATE.md` `README.md` `product/PRD.md` `product/ROADMAP.md` `product/MARKET_RESEARCH.md` `docs/TECH_ARCHITECTURE.md` `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` | `./.venv/bin/pytest -q tests/test_design_docs_substantive.py` | 已验证 | `6 passed in 0.01s`；新增 current/target 边界回归测试，锁定 README/PRD/ROADMAP/runbook 口径 |
| P0-2 | `prod` 下 fail-closed 禁止 mock/alipay_sim | `admin/config.py` `admin/routes/web_public.py` `admin/tests/test_p2_4_p2_5_secrets.py` `admin/tests/test_web_public.py` | `./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py` | 已验证 | `34 passed in 3.89s`；生产 provider 校验、模拟支付入口隐藏、portal token 分离与公共下单回归全部通过 |
| P0-3 | 退款后 webhook replay 不回写 `refunded -> paid` | `data/payments/service.py` `data/payments/tests/test_service.py` `data/payments/tests/test_webhook.py` | `./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py` | 已验证 | `13 passed in 1.52s`；退款终态保护与 webhook 幂等回归已拿到完整退出码 |
| P0-4 | `audit run` 真正执行省规则 | `data/rules/audit_engine.py` `data/rules/cli.py` `tests/test_audit_cli_major_validation_phase2.py` `tests/test_audit_engine_major_validation_phase2.py` | `./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py` | 已验证 | `8 passed in 0.18s`；CLI `audit run --help` exit `0`；规格评审 PASS；质量评审 APPROVED |
| P0-5 | WAL 模式下 `admin.db` 快照可真实恢复 | `admin/db.py` `scripts/backup_snapshot.sh` `tests/test_backup_workflow.py` `tests/test_backup_restore_service_level.py` | `./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py` | 已验证 | `8 passed in 2.30s`；WAL 快照保表保数据，restore smoke 不再超时假阳性 |

---

## 3. P1 证据矩阵

| 任务 | 证明目标 | 主要证据文件 | 必要验证命令 | 当前状态 | 证据摘要 |
| --- | --- | --- | --- | --- | --- |
| P1-1 | 单订单单活跃 payment | `data/payments/dao.py` `data/payments/service.py` `data/orders/dao.py` `admin/routes/web_public.py` `data/payments/tests/test_service.py` `admin/tests/test_web_public.py` | `./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py` + `./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py` | 已验证 | `34 passed in 3.89s` + `13 passed in 1.52s`；新增并发创建只生成 1 条 pending payment、paid 后重复 checkout 复用同一 payment、portal 状态页不回退到 `pending_payment` 的回归测试 |
| P1-2 | 同事件可并存 `station` 与 `email` 通知 | `data/notifications/email_service.py` `data/notifications/dispatcher.py` `data/orders/dao.py` `tests/test_delivery_notification.py` `tests/test_delivery_dispatcher.py` | `./.venv/bin/pytest -q tests -k notification` | 已验证 | `6 passed, 322 deselected in 0.99s`；通知唯一键已改为 `(order_id, event_type, channel)`，同一 `report_ready` 事件可按 `station/email` 并存，dispatcher 按 channel 精确更新状态 |
| P1-3 | 备份覆盖 portal 上传目录与真实交付物 | `scripts/backup_collect_order_artifacts.py` `scripts/backup_snapshot.sh` `scripts/backup_verify.sh` `docs/BACKUP_AND_RECOVERY_PLAN.md` `ops/systemd/gaokao-backup.service` `ops/cron/gaokao-backup.crontab.example` `tests/test_backup_workflow.py` | `./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py` | 已验证 | `8 passed in 2.30s`；新增 `portal_uploads` 与订单 `audit_report/pdf_path` 采集逻辑，快照 manifest 与 live verify staging 都会落下真实附件和交付物 |
| P1-4 | restore smoke 不再假阳性 | `scripts/backup_restore_smoke.py` `tests/test_backup_workflow.py` `tests/test_backup_restore_service_level.py` | `./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py` | 已验证 | `8 passed in 2.30s`；新增缺失前置条件快速失败与真实恢复链路回归，restore smoke 退出码可信 |
| P1-5 | 运维文档与实现口径一致 | `README.md` `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` `docs/TECH_ARCHITECTURE.md` | `./.venv/bin/pytest -q tests/test_design_docs_substantive.py` | 已验证 | `6 passed in 0.01s`；README 状态词改为 `ready -> validated`，runbook 与 current/target 文档口径对齐 |

---

## 4. P2 证据矩阵

| 任务 | 证明目标 | 主要证据文件 | 必要验证命令 | 当前状态 | 证据摘要 |
| --- | --- | --- | --- | --- | --- |
| P2-1 | 统一 CLI 命令面收口 | `scripts/gaokao-cli` `data/rules/cli.py` `tests/test_cli_doctor_phase3.py` `docs/CLI_API_MAPPING.md` | `./.venv/bin/pytest -q tests/test_cli_doctor_phase3.py` + `./.venv/bin/python scripts/gaokao-cli --help` | 已验证 | `12 passed in 1.53s`；顶层 help 已显式列出 `order/share/payment/channel/delivery/retention/backup/doctor`，各委派入口仍可直达原 parser / shell，统一命令面与设计映射一致 |
| P2-2 | 规则可信化扩面落地 | `data/rules/models.py` `data/rules/loader.py` `data/rules/cli.py` `rules/_truth/*` `rules/_evidence/*` `docs/RULES_SOURCE_OF_TRUTH.md` `docs/CURRENT_RULES_STATE_2026-06-16.md` `tests/test_rules_truth_phase1.py` `tests/test_rules_cli_phase1.py` `tests/test_rules_evidence_layer.py` `tests/test_cli_doctor_phase3.py` `tests/test_legacy_checker_truth_wrapper.py` | `./.venv/bin/pytest -q tests/test_rules_truth_phase1.py tests/test_rules_cli_phase1.py tests/test_rules_evidence_layer.py tests/test_cli_doctor_phase3.py tests/test_legacy_checker_truth_wrapper.py` + `./.venv/bin/python scripts/gaokao-cli rules scaffold-evidence --json` + `./.venv/bin/python scripts/gaokao-cli rules status --json` + `./.venv/bin/python scripts/gaokao-cli rules verify --json` + `./.venv/bin/python scripts/gaokao-cli doctor --json` | 已验证 | `345 passed in 4.00s`；`rules scaffold-evidence` 已为 26 省缺失规则生成 `286` 个 `draft_template` 和 `28` 个 `INDEX.md`；随后北京、湖南、江苏、浙江、上海、安徽、山东、广东、湖北、河北、海南、福建、四川、江西、甘肃、贵州、云南、辽宁、吉林、黑龙江、广西、青海、西藏、新疆、天津、河南、重庆都已补齐 `11/11` 条真实官方摘录，其中重庆普通类本科批已按重庆市教育考试院 `2025-06-17` 志愿设置 / 录取规则问答、`2026-06-09` 考后时间节点安排与重庆市教委 `2025` 实施办法闭环，并将旧的 `batch: 普通批` 校正为 `本科批`、`collection_count: 1` 校正为动态机读口径 `null`；最新 `rules status` 为 `evidenced_rule_count=298`、`missing_evidence_rule_count=0`；`rules verify` 与 `doctor` 保持 `ok=true` 且 stale 计数为 `0` |
| P2-3 | 专业目录可信化扩面落地 | `data/majors_catalog/models.py` `data/majors_catalog/loader.py` `data/majors_catalog/cli.py` `data/majors_catalog/METADATA.md` `data/majors_catalog/changes/2024-2026.md` `data/majors_catalog/schools/2026/10001.json` `docs/MAJOR_DATA_SOURCE_OF_TRUTH.md` `tests/test_majors_catalog_phase2.py` `tests/test_majors_cli_phase2.py` `tests/test_majors_school_catalog_phase2.py` `tests/test_majors_school_cli_phase2.py` | `./.venv/bin/pytest -q tests/test_majors_catalog_phase2.py tests/test_majors_cli_phase2.py tests/test_majors_school_catalog_phase2.py tests/test_majors_school_cli_phase2.py` + `./.venv/bin/python scripts/gaokao-cli majors status --json` + `./.venv/bin/python scripts/gaokao-cli majors verify --json` + `./.venv/bin/python scripts/gaokao-cli majors school-status --year 2026 --json` + `./.venv/bin/python scripts/gaokao-cli majors school-verify --year 2026 --json` | 已验证 | `12 passed in 0.40s`；四个 majors CLI 命令均 exit `0`；`./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py` => `8 passed in 0.18s`；显式 `national_major_code` 映射、`risk_tags`、`changes/2024-2026.md` 与 `version_strategy` 已纳入门禁，但当前真实数据仍是 13 个 national subset + 1 所学校样本 |
| P2-4 | `dev-verify` 契约与忽略项治理完成 | `scripts/dev-verify.sh` `tests/test_dev_verify_entrypoint.py` `admin/tests/test_app.py` `admin/tests/conftest.py` `scripts/backup_restore_smoke.py` | `env GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh --skip-pre-existing` | 已验证 | `1013 passed, 1 deselected, 6 warnings in 68.66s`；`coverage gate summary: overall=90.35%, core=100.00%`；`ruff`/`mypy` 均通过；`PRE_EXISTING_IGNORES` 已收紧到仅保留 locust 探针，`skip-install` 不再触发 pip 升级 |

---

## 5. 全局集成验证

以下命令全部通过，才允许进入最终结项审计：

```bash
./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py
./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py
./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py
./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
./.venv/bin/pytest -q tests/test_design_docs_substantive.py
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

当前最新执行结果（2026-06-18）：

- `./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py` => `34 passed in 3.89s`
- `./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py` => `13 passed in 1.52s`
- `./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py` => `8 passed in 0.21s`
- `./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py` => `8 passed in 2.30s`
- `./.venv/bin/pytest -q tests/test_design_docs_substantive.py` => `6 passed in 0.01s`
- `env GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh --skip-pre-existing` => `1013 passed, 1 deselected, 6 warnings in 68.66s`；`coverage gate summary: overall=90.35%, core=100.00%`；`ruff` / `mypy` 通过

---

## 6. Goal 完成判定

只有同时满足以下条件，active goal 才允许标记完成：

1. P0 / P1 / P2 全部有直接证据
2. `docs/ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17.md` 中所有门禁项勾选完成
3. 全局集成验证通过
4. `reports/COMPREHENSIVE_SYSTEM_REVIEW_2026-06-17.md` 中关键发现已逐项闭环
