# hainan-2026-max_majors_per_group

> 对应规则: `HAINAN.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组内设6个专业志愿和服从专业调剂志愿。"
> —— 出处: 《2026年海南省普通高校招生实施办法》
> URL: http://ea.hainan.gov.cn/ywdt/ptgkyjszsb/202605/t20260528_4083583.html
> 发布日期: 2026-05-28

## 2. 转写为机读规则

```yaml
HAINAN.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: hainan-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：海南 2026 官方直接给出每个院校专业组 `6` 个专业志愿，因此 `max_majors_per_group=6`
- 例 2：本条统计的是组内可填专业志愿数，不把单独的“服从专业调剂志愿”计入专业志愿数量

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 海南省考试局
- 复核负责人: 待指派
