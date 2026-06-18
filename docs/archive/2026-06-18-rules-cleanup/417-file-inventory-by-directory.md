# 417 File Inventory By Directory

本清单是对以下两个提交涉及文件的去重并集做目录级整理：

- `246f21c feat(review): land unified remediation and rules evidence closure`
- `2252157 docs(review): close out 2026-06-17 optimization goal`

基准命令：

```bash
git show --name-only --pretty=format: 246f21c 2252157 | sed '/^$/d' | sort -u | wc -l
```

结果：`417`

状态说明：

- `integrated_source_of_truth`: 当前真相源或证据链，保留在项目主路径
- `integrated_runtime_or_test`: 当前运行、运维或测试链路直接依赖，保留在项目主路径
- `retained_current_doc`: 当前入口文档或当前口径文档，保留在项目主路径
- `retained_historical_evidence`: 历史审计、结项或追溯证据，保留在项目主路径
- `archived_duplicate`: 已归档的重复副本

## 1. Root

- `README.md` × 1
  - 状态：`retained_current_doc`

## 2. Admin

- `admin/config.py` × 1
  - 状态：`integrated_runtime_or_test`
- `admin/routes/web_public.py` × 1
  - 状态：`integrated_runtime_or_test`
- `admin/tests/` × 6
  - `conftest.py`
  - `test_app.py`
  - `test_notification_audit_page.py`
  - `test_notifications_admin.py`
  - `test_p2_4_p2_5_secrets.py`
  - `test_web_public.py`
  - 状态：`integrated_runtime_or_test`

## 3. Data

- `data/majors_catalog/` × 6
  - `METADATA.md`
  - `changes/2024-2026.md`
  - `cli.py`
  - `loader.py`
  - `models.py`
  - `schools/2026/10001.json`
  - 状态：`integrated_runtime_or_test`
- `data/notifications/` × 2
  - `dispatcher.py`
  - `email_service.py`
  - 状态：`integrated_runtime_or_test`
- `data/orders/` × 1
  - `dao.py`
  - 状态：`integrated_runtime_or_test`
- `data/payments/` × 4
  - `dao.py`
  - `service.py`
  - `tests/test_service.py`
  - `tests/test_webhook.py`
  - 状态：`integrated_runtime_or_test`
- `data/rules/` × 4
  - `audit_engine.py`
  - `cli.py`
  - `loader.py`
  - `models.py`
  - 状态：`integrated_runtime_or_test`

## 4. Docs

- 当前入口或当前口径文档 × 8
  - `docs/BACKUP_AND_RECOVERY_PLAN.md`
  - `docs/CLI_API_MAPPING.md`
  - `docs/CURRENT_RULES_STATE_2026-06-16.md`
  - `docs/CURRENT_STATE.md`
  - `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
  - `docs/MAJOR_DATA_SOURCE_OF_TRUTH.md`
  - `docs/RULES_SOURCE_OF_TRUTH.md`
  - `docs/TECH_ARCHITECTURE.md`
  - 状态：`retained_current_doc`
- 历史证据文档 × 2
  - `docs/ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17.md`
  - `docs/FINAL_VERIFICATION_MATRIX_2026-06-17.md`
  - 状态：`retained_historical_evidence`
- `docs/plans/` × 4
  - `2026-06-17-comprehensive-review-remediation.md`
  - `2026-06-17-multi-agent-execution-checklist.md`
  - `2026-06-17-subagent-work-orders.md`
  - `2026-06-17-unified-remediation-and-optimization-task-list.md`
  - 状态：`retained_historical_evidence`

## 5. Ops

- `ops/cron/` × 1
  - `gaokao-backup.crontab.example`
  - 状态：`integrated_runtime_or_test`
- `ops/systemd/` × 1
  - `gaokao-backup.service`
  - 状态：`integrated_runtime_or_test`

## 6. Product

- `product/` × 3
  - `MARKET_RESEARCH.md`
  - `PRD.md`
  - `ROADMAP.md`
  - 状态：`retained_current_doc`

## 7. Reports

- `reports/` × 1
  - `COMPREHENSIVE_SYSTEM_REVIEW_2026-06-17.md`
  - 状态：`retained_historical_evidence`

## 8. Rules

- `rules/_truth/` × 29
  - `README.md` × 1
  - `national.yaml` × 1
  - `province/*.yaml` × 27
  - 状态：`integrated_source_of_truth`
- `rules/_evidence/` × 316
  - `README.md` × 1
  - `national/` × 2
  - `anhui/` × 12
  - `beijing/` × 12
  - `chongqing/` × 12
  - `fujian/` × 12
  - `gansu/` × 12
  - `guangdong/` × 12
  - `guangxi/` × 12
  - `guizhou/` × 12
  - `hainan/` × 12
  - `hebei/` × 12
  - `heilongjiang/` × 12
  - `henan/` × 12
  - `hubei/` × 12
  - `hunan/` × 1
  - `jiangsu/` × 12
  - `jiangxi/` × 12
  - `jilin/` × 12
  - `liaoning/` × 12
  - `qinghai/` × 12
  - `shandong/` × 12
  - `shanghai/` × 12
  - `sichuan/` × 12
  - `tianjin/` × 12
  - `xinjiang/` × 12
  - `xizang/` × 12
  - `yunnan/` × 12
  - `zhejiang/` × 12
  - 状态：`integrated_source_of_truth`
- `rules/provinces.md` × 1
  - 状态：`retained_current_doc`
- `rules/provinces/README.md` × 1
  - 状态：`retained_current_doc`

说明：

- `rules/_evidence/hunan/` 在这 417 文件里只计入 `INDEX.md`，不是因为湖南证据层无其他文件，而是因为这两个提交的改动并集里只覆盖到 1 个湖南证据文件。
- `rules/_evidence/` 的其余省份大多是 12 个文件：1 个 `INDEX.md` + 11 个规则字段摘录文件。

## 9. Scripts

- `scripts/` × 6
  - `backup_collect_order_artifacts.py`
  - `backup_restore_smoke.py`
  - `backup_snapshot.sh`
  - `backup_verify.sh`
  - `dev-verify.sh`
  - `migrate_province_rules_to_truth.py`
  - 状态：`integrated_runtime_or_test`

## 10. Skills

- `skills/gaokao-spec-checker/scripts/spec_checker_v2.py` × 1
  - 状态：`integrated_runtime_or_test`
- `skills/gaokao-spec-checker/rules/provinces.md` × 1
  - 状态：`archived_duplicate`
  - 已迁移到 `docs/archive/2026-06-18-rules-cleanup/skills-gaokao-spec-checker-rules-provinces.md`

## 11. Tests

- `tests/` × 16
  - `test_audit_cli_major_validation_phase2.py`
  - `test_audit_engine_major_validation_phase2.py`
  - `test_backup_restore_service_level.py`
  - `test_backup_workflow.py`
  - `test_cli_doctor_phase3.py`
  - `test_delivery_notification.py`
  - `test_design_docs_substantive.py`
  - `test_dev_verify_entrypoint.py`
  - `test_legacy_checker_truth_wrapper.py`
  - `test_majors_catalog_phase2.py`
  - `test_majors_cli_phase2.py`
  - `test_majors_school_catalog_phase2.py`
  - `test_majors_school_cli_phase2.py`
  - `test_rules_cli_phase1.py`
  - `test_rules_evidence_layer.py`
  - `test_rules_truth_phase1.py`
  - 状态：`integrated_runtime_or_test`

## 12. 汇总

- `integrated_source_of_truth`: 345
- `integrated_runtime_or_test`: 50
- `retained_current_doc`: 14
- `retained_historical_evidence`: 7
- `archived_duplicate`: 1
- 合计：417

## 13. 使用建议

- 想继续压缩文件量时，先看 `retained_historical_evidence`，但必须先建立统一历史快照索引，再批量迁移。
- 想核实规则相关文件是否还能继续删减时，默认从 `rules/provinces.md`、`rules/provinces/README.md` 和其他二级入口文档入手，不直接碰 `rules/_truth` 与 `rules/_evidence`。
- 想做自动化治理时，以本文件的目录级统计为人工入口，以 `git show --name-only --pretty=format: 246f21c 2252157 | sed '/^$/d' | sort -u` 为机器入口。
