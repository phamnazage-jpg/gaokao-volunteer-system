# guizhou-2026-max_majors_per_group

> 对应规则: `GUIZHOU.max_majors_per_group`
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
GUIZHOU.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 1
  effective_date: '2026-01-01'
  source_evidence_id: guizhou-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：贵州普通类本科批不是“一个院校下挂多个专业”的组内填法，而是单志愿只绑定 `1` 个专业（类）与 `1` 所院校
- 例 2：院校顺序志愿仍然存在“1个院校+6个专业（类）”结构，但那是提前批顺序志愿口径，不能覆盖本科批主体规则

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 贵州省招生考试院
- 复核负责人: 待指派
