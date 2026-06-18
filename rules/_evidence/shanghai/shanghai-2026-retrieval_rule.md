# shanghai-2026-retrieval_rule

> 对应规则: `SHANGHAI.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科普通批次按各院校专业组实到计划1:1的比例向高校投档，采用平行志愿的投档方式，执行“分数优先、遵循志愿、一轮投档”原则，将考生按照高考总分由高到低进行排序，然后由投档系统逐一检索考生的志愿。"
> —— 出处: 《上海市教育考试院负责人就本科普通批次投档线公布答记者问》
> URL: https://www.shmeea.edu.cn/page/08000/20240719/18690.html
> 发布日期: 2024-07-19

## 2. 转写为机读规则

```yaml
SHANGHAI.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: shanghai-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：官方直接给出“分数优先、遵循志愿、一轮投档”，因此 `retrieval_rule` 可原样机读
- 例 2：同页还说明本科普通批按 `1:1` 正式投档，这与“一轮投档”一起构成上海普通批的主检索规则

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 上海市教育考试院
- 复核负责人: 待指派
