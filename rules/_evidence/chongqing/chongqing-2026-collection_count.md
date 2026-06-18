# chongqing-2026-collection_count

> 对应规则: `CHONGQING.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "重庆市教育考试院负责公布普通高校在渝招生各类政策、招生计划、各批次录取控制分数线、各批次未完成招生计划并组织进行征集志愿。"
> —— 出处: 《重庆市2025年普通高等学校招生工作实施办法》
> URL: https://jw.cq.gov.cn/zwxx_209/gggs/202505/t20250512_14601180.html
> 发布日期: 2025-05-12

## 2. 转写为机读规则

```yaml
CHONGQING.collection_count:
  severity: warning
  value:
    collection_count: null
  effective_date: '2026-01-01'
  source_evidence_id: chongqing-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：重庆官方只说明“各批次未完成招生计划并组织进行征集志愿”，未对普通类 `本科批` 承诺固定征集次数，因此字段应归一为动态机读值 `null`
- 例 2：后续若重庆市教育考试院发布明确到普通类 `本科批` 的征集时间表，可再把 `null` 收紧为具体次数

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 重庆市教育委员会 / 重庆市教育考试院
- 复核负责人: 待指派
