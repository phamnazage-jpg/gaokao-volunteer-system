# jiangsu-2026-adjustment_scope

> 对应规则: `JIANGSU.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业调剂只在考生被投档进的院校专业组内进行，考生不会被录取到其他院校专业组内的专业。"
> —— 出处: 《2024年高考志愿填报热点问题（四）》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2024-06-29/7212827085415387136.html
> 发布日期: 2024-06-29
>
> "在每个院校专业组志愿中，均设有1个专业服从调剂志愿。"
> —— 出处: 《2024年高考志愿填报热点问题（四）》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2024-06-29/7212827085415387136.html
> 发布日期: 2024-06-29

## 2. 转写为机读规则

```yaml
JIANGSU.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: jiangsu-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：官方明确“只在...院校专业组内进行”，因此机读规则收敛为 `adjustment_scope: 组内专业`
- 例 2：该规则同时排除了跨院校专业组和跨院校的调剂想象空间，避免把“服从调剂”误读为全校统配

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 江苏省教育考试院
- 复核负责人: 待指派
