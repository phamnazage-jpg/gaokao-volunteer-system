# guizhou-2026-retrieval_rule

> 对应规则: `GUIZHOU.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "依据“分数优先、遵循志愿、一轮投档”的原则，按照考生投档排序位次和高校确定的投档比例进行投档。"
> —— 出处: 《贵州省2025年高考填报志愿规定》
> URL: http://zsksy.guizhou.gov.cn/ptgk/qtxx/202506/t20250625_88190180.html
> 发布日期: 2025-06-25

## 2. 转写为机读规则

```yaml
GUIZHOU.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: guizhou-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：官方原文写的是“一轮投档”，项目层延续既有归一化词表记为 `一次投档`，语义等价
- 例 2：顺序志愿批次采用“志愿优先、遵循分数”，因此这里必须锚定专业（类）平行志愿主流程，不能混用顺序志愿规则

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 贵州省招生考试院
- 复核负责人: 待指派
