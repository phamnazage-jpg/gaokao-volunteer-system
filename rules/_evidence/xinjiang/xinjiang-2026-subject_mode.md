# xinjiang-2026-subject_mode

> 对应规则: `XINJIANG.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "报考“普通类”和“单列类”招生计划的考生，文化课考试科目均为：语文、数学、文科综合/理科综合、外语。"
>
> "报考普通类或单列类招生计划的考生单科成绩的排列顺序为：文史类按语文、文科综合、数学、外语排序；理工类按数学、理科综合、语文、外语排序。"
> —— 出处: 《新疆维吾尔自治区2026年普通高校招生工作规定》
> URL: http://www.xjzk.gov.cn/c/2026-05-06/495190.shtml
> 发布日期: 2026-05-06

## 2. 转写为机读规则

```yaml
XINJIANG.subject_mode:
  severity: warning
  value:
    subject_mode: 传统
  effective_date: '2026-01-01'
  source_evidence_id: xinjiang-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：新疆 2026 仍按 `文史类 / 理工类` 组织普通类招生和同分排序，机读应保持 `subject_mode: 传统`
- 例 2：未来综合改革 cohort 的选课走班安排不等于 2026 已经切到 `3+1+2`，本字段以当年招生规定正文为准

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 新疆教育考试院
- 复核负责人: 待指派
