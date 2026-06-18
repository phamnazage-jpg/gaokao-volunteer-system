# liaoning-2026-collection_count

> 对应规则: `LIAONING.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "2025年辽宁省普通高等学校招生录取普通类本科批第一次“征集志愿”投档最低分"
>
> "2025年辽宁省普通高等学校招生录取普通类本科批第二次“征集志愿”投档最低分"
> —— 出处: 《辽宁招生考试之窗》普通高考-录取分数线列表页 / 同名正文页
> URL: https://www.lnzsks.com/listinfo/NewsList_1104_1.html
> URL: https://www.lnzsks.com/newsinfo/IMS_20250726_45068_Tcqe5rupvh.htm
> URL: https://www.lnzsks.com/newsinfo/IMS_20250730_45083_LdXKut8W21.htm
> 发布日期: 2025-07-26 / 2025-07-30

## 2. 转写为机读规则

```yaml
LIAONING.collection_count:
  severity: warning
  value:
    collection_count: 2
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁官方 2025 普通类本科批已公开出现“第一次”“第二次”征集志愿，旧值 `1` 明显低估，当前应修正为 `2`
- 例 2：这里记录的是辽宁普通类本科批已实际发生的征集轮次，不外推为所有年度固定恒为 `2`

## 4. 后续维护

- 下次复核时间: 2026-07-30
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
