# henan-2026-max_volunteers

> 对应规则: `HENAN.max_volunteers`
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
HENAN.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 48
  effective_date: '2026-01-01'
  source_evidence_id: henan-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：`48` 指普通类 `本科批` 的院校专业组志愿数，不是专业数
- 例 2：每个院校专业组内另设 6 个专业志愿，不能把 `48` 和 `6` 混写

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 河南
- 复核负责人: 待指派
