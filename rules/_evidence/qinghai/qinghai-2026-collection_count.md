# qinghai-2026-collection_count

> 对应规则: `QINGHAI.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "各段第一次投档录取结束后，未完成的招生计划可实行多次志愿征集、投档录取。"
>
> "各批次征集志愿填报时间以青海省教育考试网发布的公告为准。"
> —— 出处: 《青海省2026年普通高等学校招生录取工作实施细则》
> URL: https://www.qhjyks.com/ztzl/ptgkz/5807.htm
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
QINGHAI.collection_count:
  severity: warning
  value:
    collection_count: null
  effective_date: '2026-01-01'
  source_evidence_id: qinghai-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：青海 2026 官方明确写的是 `可实行多次志愿征集`，没有承诺固定轮次，因此应记录为动态口径 `null`
- 例 2：不能把“第一次投档录取结束后”误读成“只会有 1 次征集志愿”

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 青海省教育考试网
- 复核负责人: 待指派
