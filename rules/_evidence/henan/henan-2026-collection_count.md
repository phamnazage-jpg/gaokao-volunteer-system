# henan-2026-collection_count

> 对应规则: `HENAN.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "平行志愿投档录取结束后，根据计划余额和生源情况进行补档。计划余额大的院校（专业组）按计划余额公开征集志愿。征集志愿后，根据计划余额和生源情况进行补档。"
>
> "如仍有院校（专业）未完成招生计划，在符合条件的考生范围内征集志愿。"
> —— 出处: 《河南省2026年普通高等学校招生工作规定》
> URL: https://xcoss.henan.gov.cn/typtfile/20260427/cc9d5c1a332341f0a7d9223f54f0cf62.pdf
> 发布日期: 2026-04-22

## 2. 转写为机读规则

```yaml
HENAN.collection_count:
  severity: warning
  value:
    collection_count: null
  effective_date: '2026-01-01'
  source_evidence_id: henan-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：官方明确存在公开征集志愿和补档流程，但未对普通类 `本科批` 承诺固定征集次数，因此当前字段应归一化为动态机读值 `null`
- 例 2：后续若河南省教育考试院发布明确到某一批次的征集时间表，可再把 `null` 收紧为具体次数

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 河南
- 复核负责人: 待指派
