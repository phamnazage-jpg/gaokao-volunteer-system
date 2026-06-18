# RULES_EVIDENCE_LAYER

> 真相源: `docs/RULES_SOURCE_OF_TRUTH.md` §2 + `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §2.5
> 现状: 2026-06-18 已落 `rules/_evidence/hunan/`、`beijing/`、`jiangsu/`、`zhejiang/`、`shanghai/`、`anhui/`、`shandong/`、`guangdong/`、`hubei/`、`hebei/`、`hainan/`、`fujian/`、`sichuan/`、`jiangxi/`、`gansu/`、`guizhou/`、`yunnan/`、`liaoning/`、`jilin/`、`heilongjiang/`、`guangxi/`、`qinghai/`、`xizang/`、`xinjiang/`、`tianjin/`、`henan/`、`chongqing/` 各 11 条证据摘录，以及 `national/` 1 条国家级样本

## 目录约定

```
rules/_evidence/
├── README.md                          # 本文件
├── <prov-slug>/
│   ├── <year>-<topic-slug>.md         # 一条 evidence 摘录
│   ├── ...
│   └── INDEX.md                       # 省级索引（可选）
└── national/
    ├── <year>-<topic-slug>.md
    └── ...
```

- `<prov-slug>` 沿用 `data/rules/loader.py` 的 `PROVINCE_SLUGS` slug（如 `hunan` / `beijing`）
- `<topic-slug>` 一律小写 + `-` 连接（与 `source_evidence_id` 的 `<rule_key>` 部分对齐）
- 文件名 = `<source_evidence_id>.md`（一对一命名，避免歧义）

## evidence 摘录模板

每个 evidence 文件必须包含四段：

````markdown
# <source_evidence_id>

> 对应规则: `<rule_id>`（如 `HUNAN.max_volunteers`）
> 所属: 省级 / 国家级
> 规则版本: `<year>.<version>`（如 `2026.1`）
> 摘录时间: YYYY-MM-DD
> 摘录人: <name>
> 证据状态: `complete`

## 1. 官方原文摘录

> "……原文片段……" —— 出处: <官方文件名>，<官方 URL>，<发布日期>

## 2. 转写为机读规则

```yaml
<rule_id>:
  severity: <fatal|critical|warning|info>
  value:
    <key>: <value>
  effective_date: YYYY-MM-DD
  source_evidence_id: <source_evidence_id>
  status: active
```
````

## 3. 关键边界与例外

- 例 1：……
- 例 2：……

## 4. 后续维护

- 下次复核时间: YYYY-MM-DD
- 复核来源: <URL>
- 复核负责人: <name>

```

## 当前覆盖（2026-06-18 snapshot）

| province   | coverage | evidence_id 列表 |
| ---------- | -------- | ---------------- |
| anhui      | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| beijing    | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| hunan      | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| jiangsu    | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| guangdong  | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| hubei      | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| hebei      | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| hainan     | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| fujian     | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| sichuan    | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| jiangxi    | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| gansu      | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| guizhou    | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| heilongjiang | 11/11  | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| jilin      | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| liaoning   | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| yunnan     | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| shanghai   | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| shandong   | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| zhejiang   | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| guangxi    | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| qinghai    | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| xizang     | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| xinjiang   | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| tianjin    | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| henan      | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| chongqing  | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| national   | 1/1      | `national-2026-parallel-volunteer-principle` |

## 模板脚手架

- `python scripts/gaokao-cli rules scaffold-evidence --json`
  - 为缺失证据的 active 规则生成 `draft_template` 模板与 `INDEX.md`
  - 仅用于后续人工摘录，不会被 loader 计入 evidence 覆盖
- `draft_template` 文件至少包含以下占位符之一：
  - `证据状态: draft_template`
  - `TODO_OFFICIAL_EXCERPT`

## 校验约定

- `gaokao-cli rules verify` 当前**只**校验 `national.yaml` + `province/` 文件存在性
- 不校验 `_evidence/` 存在性（避免阻塞未做证据摘录的省）
- 进阶校验：每条规则的 `source_evidence_id` 必须能找到 `rules/_evidence/<prov>/<id>.md`
  - 计划在 `RuleLoader.from_truth_root(strict_evidence=True)` 模式提供
  - 默认 `strict_evidence=False`，由调用方按需开启
- evidence 完成态要求：
  - 文件存在
  - 包含四段标准 section
  - 不包含 `draft_template` / `TODO_OFFICIAL_EXCERPT` 占位符
```
