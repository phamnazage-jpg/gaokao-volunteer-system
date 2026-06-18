# xizang-2026-collection_count

> 对应规则: `XIZANG.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "院校未完成计划，通过公开征集志愿的方式完成，征集志愿采用平行志愿方式，视情况进行一次或多次。"
>
> "平行志愿进行一轮投档录取后，未录满的计划向社会公开征集志愿，征集志愿视情况可进行一次或多次。"
> —— 出处: 《西藏自治区2026年普通高等学校招生规定》
> URL: http://zsks.edu.xizang.gov.cn/71/74/7787.html
> 发布日期: 2026-05-29

## 2. 转写为机读规则

```yaml
XIZANG.collection_count:
  severity: warning
  value:
    collection_count: null
  effective_date: '2026-01-01'
  source_evidence_id: xizang-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：西藏 2026 官方写法是“视情况进行一次或多次”，未承诺固定轮次，因此应记录为动态口径 `null`
- 例 2：不能因为正文里出现“一次或多次”就简化为固定 `1` 次

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 西藏教育考试院
- 复核负责人: 待指派
