# tianjin-2026-max_majors_per_group

> 对应规则: `TIANJIN.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通本科批次A阶段……每个院校专业组设置6个专业志愿和1个服从调剂专业志愿。"
>
> "普通本科批次B阶段……每个院校专业组设置6个专业志愿和1个服从调剂专业志愿。"
> —— 出处: 《热点问答①|天津高考生志愿填报之整体安排》
> URL: http://www.zhaokao.net/gkck/system/2026/06/16/030009834.shtml
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
TIANJIN.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: tianjin-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：天津普通类本科批 A/B 两阶段每个院校专业组都明确是 `6个专业志愿`
- 例 2：`1个服从调剂专业志愿` 是额外调剂位，不应并入 `max_majors_per_group`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 天津教育招生考试院
- 复核负责人: 待指派
