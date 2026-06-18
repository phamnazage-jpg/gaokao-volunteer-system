# liaoning-2026-has_adjustment

> 对应规则: `LIAONING.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业平行志愿投档时，直接投档到某院校某专业，不存在专业服从调剂。"
>
> "“专业+学校”模式取消了专业调剂，考生不必担心被调剂到不喜欢的专业了。"
> —— 出处: 《辽宁省2024年普通高校招生志愿填报及招生录取问答》
> URL: https://www.lnzsks.com/newsinfo/IMS_20240619_44007_hZ6qDmgcpv.htm
> 发布日期: 2024-06-19

## 2. 转写为机读规则

```yaml
LIAONING.has_adjustment:
  severity: warning
  value:
    has_adjustment: false
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁普通类本科批 `专业+学校` 单志愿直投，不存在“是否服从专业调剂”选项，因此 `has_adjustment` 应为 `false`
- 例 2：普通类本科提前批属于院校志愿，不应直接套用本科批这条 `false` 口径

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
