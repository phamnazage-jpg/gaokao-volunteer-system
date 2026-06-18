# tianjin-2026-has_adjustment

> 对应规则: `TIANJIN.has_adjustment`
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
TIANJIN.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: tianjin-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：天津普通类本科批 A/B 两阶段都显式提供 `1个服从调剂专业志愿`，因此 `has_adjustment` 为 `true`
- 例 2：是否服从调剂只影响院校专业组内的专业分配，不代表可以跨院校专业组调剂

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 天津教育招生考试院
- 复核负责人: 待指派
