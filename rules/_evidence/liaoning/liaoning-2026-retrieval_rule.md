# liaoning-2026-retrieval_rule

> 对应规则: `LIAONING.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业平行志愿，是新高考招生同一类别、同一批次中若干具有相对平行关系的专业志愿，以一所院校的一个专业为志愿单位，按照“分数优先、遵循志愿、一轮投档”的原则进行投档。"
>
> "平行志愿依据“分数优先、遵循志愿、一轮投档”的原则，按照考生投档排序位次进行投档。"
> —— 出处: 《辽宁省2024年普通高校招生志愿填报及招生录取问答》
> URL: https://www.lnzsks.com/newsinfo/IMS_20240619_44007_hZ6qDmgcpv.htm
> 发布日期: 2024-06-19

## 2. 转写为机读规则

```yaml
LIAONING.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁普通类本科批应机读为 `分数优先、遵循志愿、一次投档`，这里的“一次投档”来自官方原文“一轮投档”的归一化表达
- 例 2：同分排序细则另有语数和、单科成绩等展开说明，但不影响本字段主原则抽取

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
