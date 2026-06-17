# hunan-2026-collection_count

> 对应规则: `HUNAN.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-17
> 摘录人: Hermes Agent (主代理)

## 1. 官方原文摘录

> "本科批投档录取后，如仍有高校招生计划未完成，将组织 2 次征集志愿。"
> —— 出处: 《湖南省 2026 年普通高校招生工作实施办法》第三章"征集志愿"

## 2. 转写为机读规则

```yaml
HUNAN.collection_count:
  severity: warning
  value:
    collection_count: 2
  effective_date: 2026-01-01
  source_evidence_id: hunan-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：本科提前批一般不组织征集志愿
- 例 2：专科批征集志愿次数另定（不在本规则范围内）

## 4. 后续维护

- 下次复核时间: 2026-09-01
- 复核来源: 湖南省教育考试院
- 复核负责人: 待指派
