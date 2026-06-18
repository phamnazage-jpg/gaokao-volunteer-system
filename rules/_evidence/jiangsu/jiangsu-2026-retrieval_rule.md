# jiangsu-2026-retrieval_rule

> 对应规则: `JIANGSU.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类、体育类各批次以及艺术类使用省统考成绩录取的专业实行平行志愿投档方式，分历史等科目类、物理等科目类，按照“按分排序，遵循志愿”的原则进行投档。"
> —— 出处: 《2024年高考志愿填报热点问题（三）》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2024-06-26/7211546384258830336.html
> 发布日期: 2024-06-26
>
> "如果考生档案投到某院校专业组后，因故被退出，将不再补投到该批次平行志愿的其他后续院校专业组。"
> —— 出处: 《2024年高考志愿填报热点问题（三）》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2024-06-26/7211546384258830336.html
> 发布日期: 2024-06-26

## 2. 转写为机读规则

```yaml
JIANGSU.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: jiangsu-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：江苏官方原文写的是“按分排序，遵循志愿”，机读字段延续项目统一口径转写为“分数优先、遵循志愿”
- 例 2：退档后“不再补投”体现的是同批次只享受一次平行志愿投档机会，因此机读字段保留“一次投档”

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 江苏省教育考试院
- 复核负责人: 待指派
