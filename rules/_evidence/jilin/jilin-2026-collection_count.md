# jilin-2026-collection_count

> 对应规则: `JILIN.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "说明：每个批次未完成招生计划均采取公开征集志愿的办法补充生源。"
>
> "吉林省2025年高考征集志愿：本科批征集志愿（第一轮）考生须知"
>
> "吉林省2025年高考征集志愿：本科批征集志愿（第二轮）考生须知"
> —— 出处: 《吉林省2026年普通高考志愿填报及录取时间安排》 / 吉林省教育考试院普通高考栏目页
> URL: https://www.jleea.com.cn/front/content/202704
> URL: https://www.jleea.com.cn/site1/ksxm_gdjyks/9942/page/1/
> 发布日期: 2026-06-15 / 2025-07-18 / 2025-07-22

## 2. 转写为机读规则

```yaml
JILIN.collection_count:
  severity: warning
  value:
    collection_count: 2
  effective_date: '2026-01-01'
  source_evidence_id: jilin-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：吉林 2025 普通类本科批已公开出现“第一轮”“第二轮”征集志愿，旧值 `1` 明显低估，当前应修正为 `2`
- 例 2：这里记录的是吉林普通类本科批已实际发生的征集轮次，不外推为所有年度固定恒为 `2`

## 4. 后续维护

- 下次复核时间: 2026-07-25
- 复核来源: 吉林省教育考试院
- 复核负责人: 待指派
