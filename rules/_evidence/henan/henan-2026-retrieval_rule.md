# henan-2026-retrieval_rule

> 对应规则: `HENAN.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "平行志愿投档按照'分数优先、遵循志愿、一轮投档'的原则进行。即：将同一类别考生按位次成绩从高到低排序后，依次检索考生志愿，一经检索到计划未满额且符合投档要求的院校专业组，即向该院校专业组投档。"
> —— 出处: 《河南省2026年普通高等学校招生工作规定》
> URL: https://xcoss.henan.gov.cn/typtfile/20260427/cc9d5c1a332341f0a7d9223f54f0cf62.pdf
> 发布日期: 2026-04-22

## 2. 转写为机读规则

```yaml
HENAN.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: henan-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：官方原文使用 `一轮投档`，项目统一归一化为 `一次投档`
- 例 2：一旦检索到符合要求的院校专业组即投档，不再继续检索后续志愿

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 河南
- 复核负责人: 待指派
