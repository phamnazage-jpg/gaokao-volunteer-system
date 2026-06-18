# jilin-2026-max_majors_per_group

> 对应规则: `JILIN.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿均设置6个专业志愿和是否服从专业调剂选项。"
>
> "考生须在该批次志愿填报界面按提示逐条录入志愿的院校专业组代码（4位院校代号+3位专业组代码）、专业代码（3位），并确认是否服从专业调剂。"
> —— 出处: 《吉林省2026年普通高考志愿填报及录取时间安排》
> URL: https://www.jleea.com.cn/front/content/202704
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
JILIN.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: jilin-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：吉林按院校专业组填报，每个组固定带 `6` 个专业志愿，不是 `1` 个单专业直投模式
- 例 2：同一院校不同专业组是不同志愿单位，`6` 的上限只作用于当前专业组内

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 吉林省教育考试院
- 复核负责人: 待指派
