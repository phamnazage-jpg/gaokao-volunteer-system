# shanghai-2026-max_majors_per_group

> 对应规则: `SHANGHAI.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿内设4个专业志愿。"
> —— 出处: 《上海市2025年普通高等学校招生志愿填报与投档录取实施办法》
> URL: https://www.shmeea.edu.cn/page/06300/20250425/19280.html
> 发布日期: 2025-04-25

## 2. 转写为机读规则

```yaml
SHANGHAI.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 4
  effective_date: '2026-01-01'
  source_evidence_id: shanghai-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：上海以院校专业组为志愿单位，组内最多填报 `4` 个专业志愿，因此 `max_majors_per_group=4`
- 例 2：该规则描述的是组内专业位数，不包含是否服从专业调剂这一独立开关

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 上海市教育考试院
- 复核负责人: 待指派
