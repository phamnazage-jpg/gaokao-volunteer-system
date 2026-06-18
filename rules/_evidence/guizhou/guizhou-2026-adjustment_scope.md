# guizhou-2026-adjustment_scope

> 对应规则: `GUIZHOU.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业（类）平行志愿是指以“1个专业（类）+1个院校”为1个志愿，不设是否服从专业调剂选项。"
> —— 出处: 《贵州省2025年高考填报志愿规定》
> URL: http://zsksy.guizhou.gov.cn/ptgk/qtxx/202506/t20250625_88190180.html
> 发布日期: 2025-06-25

## 2. 转写为机读规则

```yaml
GUIZHOU.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 无
  effective_date: '2026-01-01'
  source_evidence_id: guizhou-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：既然本科批平行志愿不设置调剂选项，项目层应把调剂范围规范化为 `无`，而不是误记为院校内或组内调剂
- 例 2：提前批顺序志愿的调剂范围不应外溢到普通类本科批，否则会把不同投档机制混成一条错误规则

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 贵州省招生考试院
- 复核负责人: 待指派
