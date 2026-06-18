# fujian-2026-max_majors_per_group

> 对应规则: `FUJIAN.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿均设6个专业志愿和是否服从专业调剂栏目。"
> —— 出处: 《2026年福建省普通高等学校招生录取实施办法》
> URL: http://www.eeafj.cn/gkptgkgsgg/20260612/14670.html
> 发布日期: 2026-06-11 / 2026-06-12 发布

## 2. 转写为机读规则

```yaml
FUJIAN.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: fujian-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：福建官方直接给出每个院校专业组 `6` 个专业志愿，因此 `max_majors_per_group=6`
- 例 2：本条只统计组内专业志愿位，不把单独的“是否服从专业调剂栏目”计入专业志愿数量

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 福建省教育考试院
- 复核负责人: 待指派
