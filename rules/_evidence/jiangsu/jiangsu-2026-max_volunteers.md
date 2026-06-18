# jiangsu-2026-max_volunteers

> 对应规则: `JIANGSU.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "将省控线上的考生，分历史等科目类、物理等科目类，按照总分从高分到低分的顺序，依次检索考生所填20或40个院校专业组志愿。"
> —— 出处: 《2024年高考志愿填报热点问题（三）》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2024-06-26/7211546384258830336.html
> 发布日期: 2024-06-26
>
> "第一阶段：6月28日至7月2日（截止时间为7月2日17:00），填报本科院校专业组志愿。"
> —— 出处: 《2025年高考志愿填报热点问题》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2025-06-25/7343571560269090816.html
> 发布日期: 2025-06-25

## 2. 转写为机读规则

```yaml
JIANGSU.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 40
  effective_date: '2026-01-01'
  source_evidence_id: jiangsu-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：江苏平行志愿原文写的是 “20或40个院校专业组志愿”，其中本科阶段对应 40 个、专科阶段对应 20 个
- 例 2：当前 truth 规则作用域是本科批，因此机读值保留 `max_volunteers: 40`，不把专科阶段的 20 个志愿混入同一条规则

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 江苏省教育考试院
- 复核负责人: 待指派
