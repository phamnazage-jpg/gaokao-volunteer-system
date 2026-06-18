# hebei-2026-collection_count

> 对应规则: `HEBEI.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科批第一次志愿征集"
> "7月24日12时至7月26日17时"
> "本科批第二次志愿征集"
> "7月29日12时至8月1日17时"
> —— 出处: 《2026年河北省普通高考志愿填报须知》
> URL: https://www.hebeea.edu.cn/c/2026-06-17/493051.html
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
HEBEI.collection_count:
  severity: warning
  value:
    collection_count: 2
  effective_date: '2026-01-01'
  source_evidence_id: hebei-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：旧 truth 写成 `1` 与 2026 官方时间表直接冲突，本次已按“第一次/第二次志愿征集”修正为 `2`
- 例 2：本条只统计本科批征集次数，不把专科批三次征集混入普通本科批规则

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 河北省教育考试院
- 复核负责人: 待指派
