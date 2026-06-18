# beijing-2026-retrieval_rule

> 对应规则: `BEIJING.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "平行志愿按照“分数优先，遵循志愿”的原则。"
> —— 出处: 《本科普通批志愿填报政策早了解》
> URL: https://www.bjeea.cn/html/ksb/gaozhaozhuanban/2022/0330/81257.html
> 发布日期: 2022-03-30
>
> "对分数线上未被录取的考生按录取总成绩从高分到低分排序进行一次性投档。"
> —— 出处: 《本科普通批志愿填报政策早了解》
> URL: https://www.bjeea.cn/html/ksb/gaozhaozhuanban/2022/0330/81257.html
> 发布日期: 2022-03-30

## 2. 转写为机读规则

```yaml
BEIJING.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: beijing-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：原文分两句给出“分数优先、遵循志愿、一次性投档”，机读规则合并为 `分数优先、遵循志愿、一次投档`
- 例 2：这是北京本科普通批平行志愿投档原则，不覆盖艺术类顺序志愿等特殊场景

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 北京考试报
- 复核负责人: 待指派
