# sichuan-2026-max_majors_per_group

> 对应规则: `SICHUAN.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿内设置6个专业志愿和是否服从专业调剂选项。"
> —— 出处: 《四川省2026年普通高校招生实施规定》
> URL: http://www.sceea.cn/Html/202604/Newsdetail_4767.html
> 发布日期: 2026-04-21 / 2026-04-23 发布

## 2. 转写为机读规则

```yaml
SICHUAN.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: sichuan-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：四川 2026 各主要院校专业组志愿均明确设置 `6` 个专业志愿，因此 `max_majors_per_group=6`
- 例 2：本条只统计组内专业志愿数量，不把单独的“是否服从专业调剂选项”计入专业志愿数

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 四川省教育考试院
- 复核负责人: 待指派
