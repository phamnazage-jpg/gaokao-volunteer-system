# xinjiang-2026-collection_count

> 对应规则: `XINJIANG.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "在国家及地方专项、南疆单列和对口援疆计划本科一批次，本科一批次及本科二批次录取结束后，各安排一次征集志愿；在高职（专科）批次录取结束后，安排两次征集志愿。"
> —— 出处: 《新疆维吾尔自治区2026年普通高校招生工作规定》
> URL: http://www.xjzk.gov.cn/c/2026-05-06/495190.shtml
> 发布日期: 2026-05-06

## 2. 转写为机读规则

```yaml
XINJIANG.collection_count:
  severity: warning
  value:
    collection_count: 1
  effective_date: '2026-01-01'
  source_evidence_id: xinjiang-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：省级主规则锚定 `本科一批`，因此这里记录的是对应批次 `各安排一次征集志愿` 的 `1`
- 例 2：新疆并非所有批次都只有 `1` 次征集志愿，高职（专科）批次官方明确是 `2` 次，不能错误外推到全省所有批次

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 新疆教育考试院
- 复核负责人: 待指派
