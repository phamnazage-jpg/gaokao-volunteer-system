# hunan-2026-max_majors_per_group

> 对应规则: `HUNAN.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-17
> 摘录人: Hermes Agent (主代理)

## 1. 官方原文摘录

> "每个院校专业组志愿设置 6 个专业志愿和 1 个是否服从专业调剂志愿。"
> —— 出处: 《湖南省 2026 年普通高校招生工作实施办法》第二章"志愿设置"

## 2. 转写为机读规则

```yaml
HUNAN.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: 2026-01-01
  source_evidence_id: hunan-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：不设置"是否服从专业组调剂"（专业组整体作为一个投档单位）
- 例 2：体育类 / 艺术类专业组有特殊上限（不在本规则范围内）

## 4. 后续维护

- 下次复核时间: 2026-09-01
- 复核来源: 湖南省教育考试院
- 复核负责人: 待指派
