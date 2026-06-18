# chongqing-2026-retrieval_rule

> 对应规则: `CHONGQING.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "实行专业平行志愿的批次依据‘分数优先、遵循志愿、一轮投档’的原则，按照考生投档排序位次进行投档。"
> —— 出处: 《录取顺序是怎样安排的》
> URL: https://www.cqksy.cn/web/article/2025-06/17/content_6632.html
> 发布日期: 2025-06-17

## 2. 转写为机读规则

```yaml
CHONGQING.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: chongqing-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：重庆官方原文使用“一轮投档”，项目统一归一为 `一次投档`，语义保持一致
- 例 2：同页还说明院校顺序志愿采用“志愿优先、遵循分数”，不能误套到普通类 `本科批`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 重庆市教育考试院
- 复核负责人: 待指派
