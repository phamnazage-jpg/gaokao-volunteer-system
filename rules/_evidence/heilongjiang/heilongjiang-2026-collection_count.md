# heilongjiang-2026-collection_count

> 对应规则: `HEILONGJIANG.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "各批次院校专业组常规志愿投档录取结束后，未完成的招生计划将由黑龙江省招生考试院统一整理，在官方网站、黑龙江省招生考试信息港对外公示，开展征集志愿填报工作。"
>
> "2025年黑龙江省普通高校招生普通本科批第二次征集志愿于7月29日进行平行志愿投档，现公布各院校专业组投档分数线。"
> —— 出处: 《2026年黑龙江省普通高校招生网上填报志愿考生须知》 / 《2025年普通高校招生普通本科批第二次征集志愿平行志愿投档分数线现予公布》
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202606/t20260617_19794.htm
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202507/t20250729_19528.htm
> 发布日期: 2026-06-17 / 2025-07-29

## 2. 转写为机读规则

```yaml
HEILONGJIANG.collection_count:
  severity: warning
  value:
    collection_count: 2
  effective_date: '2026-01-01'
  source_evidence_id: heilongjiang-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：`第二次征集志愿` 的官方公告证明普通本科批至少存在两轮征集，因此当前机读值记录为 `2`
- 例 2：2026 须知仍保留统一征集机制，但未在该页承诺固定轮次；后续如出现第三轮或改为动态轮次，需要再更新 truth

## 4. 后续维护

- 下次复核时间: 2026-07-30
- 复核来源: 黑龙江省招生考试信息港
- 复核负责人: 待指派
