# henan-2026-adjustment_scope

> 对应规则: `HENAN.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通本科批和高职（专科）批均实行平行志愿投档，普通本科批实行院校专业组平行志愿，设置48个院校专业组志愿。每个院校专业组设6个专业志愿及是否同意专业调剂选项。"
>
> "平行志愿投档时，考生位次成绩达到某院校专业组投档要求的，即被投档到该院校专业组。"
> —— 出处: 《河南省2026年普通高等学校招生工作规定》
> URL: https://xcoss.henan.gov.cn/typtfile/20260427/cc9d5c1a332341f0a7d9223f54f0cf62.pdf
> 发布日期: 2026-04-22

## 2. 转写为机读规则

```yaml
HENAN.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: henan-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：录取和投档单位是 `院校专业组`，调剂只能在已投档的同一院校专业组内理解和执行
- 例 2：官方未给出跨院校专业组调剂的表述，因此不能机读成 `全部专业`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 河南
- 复核负责人: 待指派
