# RULES_EVIDENCE_LAYER

> 真相源: `docs/RULES_SOURCE_OF_TRUTH.md` §2 + `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §2.5
> 现状: 2026-06-17 已落 `rules/_evidence/hunan/` 11 条证据摘录（湖南 2026 本科批院校专业组 1 省样本做透）

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

## 当前覆盖（2026-06-17 snapshot）

| province  | coverage | evidence_id 列表                                                                       |
| --------- | -------- | -------------------------------------------------------------------------------------- |
| hunan     | 11/11    | mode / batch / max_volunteers / max_majors_per_group / has_adjustment / adjustment_scope / retrieval_rule / collection_count / subject_mode / official_url / exam_subject_total |
| 其它 26 省 | 0/0      | 待 Phase 4 后续批推进                                                                  |
| national  | 0/0      | 当前 `national-2026-parallel-rule` 是占位；待 Phase 4 补建                              |

## 校验约定

- `gaokao-cli rules verify` 当前**只**校验 `national.yaml` + `province/` 文件存在性
- 不校验 `_evidence/` 存在性（避免阻塞未做证据摘录的省）
- 进阶校验：每条规则的 `source_evidence_id` 必须能找到 `rules/_evidence/<prov>/<id>.md`
  - 计划在 `RuleLoader.from_truth_root(strict_evidence=True)` 模式提供
  - 默认 `strict_evidence=False`，由调用方按需开启
```
