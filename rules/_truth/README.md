# rules/\_truth

本目录由 `python -m scripts.migrate_province_rules_to_truth` 生成并作为 Phase 1 的规则真相源基线。

结构:

- `national.yaml` — 全国通用规则基线
- `province/*.yaml` — 各省 2026 规则基线

当前策略:

- 先从旧 `scripts/gaokao-checker` 的 `PROVINCE_RULES` 一次性迁移
- 后续每次规则更新都必须同步 `source_evidence_id`、`last_verified_at` 与版本号
