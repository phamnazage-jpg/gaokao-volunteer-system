# henan-2026-max_majors_per_group

> 对应规则: `HENAN.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通本科批和高职（专科）批均实行平行志愿投档，普通本科批实行院校专业组平行志愿，设置48个院校专业组志愿。每个院校专业组设6个专业志愿及是否同意专业调剂选项。"
> —— 出处: 《河南省2026年普通高等学校招生工作规定》
> URL: https://xcoss.henan.gov.cn/typtfile/20260427/cc9d5c1a332341f0a7d9223f54f0cf62.pdf
> 发布日期: 2026-04-22

## 2. 转写为机读规则

```yaml
HENAN.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: henan-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：每个院校专业组内固定为 `6` 个专业志愿，不是旧口径的 `5`
- 例 2：`是否同意专业调剂选项` 是额外选项，不计入 6 个专业志愿数量

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 河南
- 复核负责人: 待指派
