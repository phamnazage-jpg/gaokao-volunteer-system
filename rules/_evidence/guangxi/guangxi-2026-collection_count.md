# guangxi-2026-collection_count

> 对应规则: `GUANGXI.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "部分批次将预留征集志愿时间，并根据录取时计划完成情况确定是否征集志愿。各批次征集志愿的填报时间将在“广西招生考试院”网站公布。"
>
> "未完成的招生计划，自治区招生考试院统一向社会公布，公开征集志愿。"
> —— 出处: 《自治区招生考试院关于做好我区2026年普通高校招生统一考试志愿填报工作的通知》 / 《广西2026年普通高等学校招生工作实施细则》
> URL: https://www.gxeea.cn/view/content_1013_32855.htm
> URL: https://www.gxeea.cn/view/content_619_32717.htm
> 发布日期: 2026-06-17 / 2026-05-14

## 2. 转写为机读规则

```yaml
GUANGXI.collection_count:
  severity: warning
  value:
    collection_count: null
  effective_date: '2026-01-01'
  source_evidence_id: guangxi-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：广西 2026 官方只明确“预留征集志愿时间”且“根据录取时计划完成情况确定是否征集志愿”，未承诺固定轮次，因此应记为动态口径 `null`
- 例 2：不能拿 2025 高职高专批的第一轮/第二轮征集公告，直接硬推普通类本科普通批也是 `2` 次

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广西招生考试院
- 复核负责人: 待指派
