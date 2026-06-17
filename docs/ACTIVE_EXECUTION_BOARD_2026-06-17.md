# ACTIVE_EXECUTION_BOARD_2026-06-17

> 真相源: `docs/CURRENT_STATE.md` §0
> 设计快照: `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md`
> 优化计划: `docs/plans/2026-06-16-optimization-program.md`
> 状态: 已收口 / 未启动 两段式

---

## 1. 已收口（执行 Phase 1 / 1.5 / 2）

### 1.1 执行 Phase 1 + 1.5 — 规则真相源化

- 已落地:
  - `rules/_truth/national.yaml`（国家级规则）
  - `rules/_truth/province/*.yaml`（27 省，2026 版）
  - `data/rules/loader.py` `RuleLoader.from_truth_root`
  - `data/rules/audit_engine.py` `AuditEngine.audit_plan`
  - `data/rules/cli.py` `rules {status,verify}`
  - `scripts/migrate_province_rules_to_truth.py`（从 `PROVINCE_RULES` 一次性迁移）
  - `tests/test_rules_truth_phase1.py` + `tests/test_audit_cli_major_validation_phase2.py`
- 提交链:
  - `ae4835e` rules truth source loader + rules CLI
  - `8a61b8f` phase1.5 verify 收口 + 旧 checker 迁移
- 三仓: gitea / origin / tksea 同步至 `edc5b11`

### 1.2 执行 Phase 2 Batch 1 — 国家级专业目录 MVP

- 已落地:
  - `data/majors_catalog/models.py` `NationalMajor`
  - `data/majors_catalog/loader.py` `MajorsCatalogLoader`
  - `data/majors_catalog/national/2024.json` + `national/latest.json`（13 个 curated subset）
  - `data/majors_catalog/cli.py` `majors {status,lookup,verify,changes}`
  - `tests/test_majors_catalog_phase2.py` + `tests/test_majors_cli_phase2.py`
- 提交: `36ad58a feat(majors): add phase2 national catalog mvp`

### 1.3 执行 Phase 2 Batch 2 — 校级招生目录骨架

- 已落地:
  - `data/majors_catalog/schools/2026/10001.json`（1 所校级骨架样本）
  - `data/majors_catalog/cli.py` `majors school-status / school-verify --year`
  - `tests/test_majors_school_catalog_phase2.py` + `tests/test_majors_school_cli_phase2.py`
- 提交: `6b1157f feat(majors): add school catalog skeleton and verification`

### 1.4 执行 Phase 2 Batch 3 — audit_engine 接入 major_validation

- 已落地:
  - `data/rules/audit_engine.py` `_validate_majors` 接入 `audit_plan`
  - `data/rules/cli.py` `audit run --province --plan --truth-root --catalog-root --json`
  - 输出口径: `MAJORS.not_found` / `MAJORS.non_active`
  - `tests/test_audit_engine_major_validation_phase2.py` + `tests/test_audit_cli_major_validation_phase2.py`
- 提交: `edc5b11 feat(audit): validate majors in structured audit flow`

---

## 2. 未启动（执行 Phase 3 = 统一 CLI 命令面）

> 这是当前唯一未启动且**不依赖外部前置**的 P1 主目标。
> Lane D（设计）的 Phase 4 = Lane E（执行）的 Phase 3，请勿混淆。

### 2.1 范围

按 6/16 优化计划 Phase 4 / 设计层 Phase 4 收敛：

- `gaokao-cli {order,share,delivery,retention,payment,backup,channel,doctor}` 收纳
- `gaokao-cli doctor` 最小自检（已有 loader / engine / CLI 调用面，不依赖 `gaokato/`）
- 旧 `scripts/gaokao-*` wrapper 的 deprecation warning
- `docs/CLI_API_MAPPING.md` 同步"已落地命令清单"节

### 2.2 暂不进入本轮

- `gaokato/services/*` 与 `gaokato/transport/*`（设计层 Phase 5 = 执行层 Phase 4）
- `gaokato/capabilities/registry.py`（等 doctor 落地后再用其 JSON 输出作为初版源）
- 退出码统一改写（沿用各子 CLI 现状，不与 Lane D 退出码收口任务冲突）

### 2.3 不可触发的真源改动

- 不改 `data/rules/loader.py` 字段
- 不改 `data/majors_catalog/*` 数据契约
- 不改 `rules/_truth/*` yaml
- 不重写 `data/orders/cli.py` 状态机

---

## 3. 收口规则（防止 4 条线再漂）

1. 状态查询一律走本文件 + `docs/CURRENT_STATE.md` §0
2. 设计层 Phase 编号不等于执行层 Phase 编号；引用必须带"执行/设计"前缀
3. 新写"待做"必须指明属于哪个执行 Phase
4. 历史评审/历史快照/历史整改计划三类文件不再进入本板追踪
5. docs-only commit 必须在 commit message 标注"docs-only"，避免与代码 commit 混轨

---

## 4. 与本板同步的当前任务文档

- `/home/long/.hermes/docs/tasks/current/TASK-20260617-gaokao-optimization-batch2.md`
