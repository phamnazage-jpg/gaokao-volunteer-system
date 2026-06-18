# shanghai-2026-subject_mode

> 对应规则: `SHANGHAI.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生高考成绩由语文、数学、外语3门统一高考科目成绩和学生自主选择的3门普通高中学业水平等级性考试科目成绩构成。"
> "考生可根据高校招生要求和自身兴趣特长，在6门等级性考试科目中自主选择3门参加考试。"
> —— 出处: 《上海市2025年普通高等学校招生志愿填报与投档录取实施办法》 / 《上海市普通高中学业水平考试实施办法（试行）》
> URL: https://www.shmeea.edu.cn/page/06300/20250425/19280.html / http://www.shmeea.edu.cn/page/17112/20160914/3521.html
> 发布日期: 2025-04-25 / 2016-09-14

## 2. 转写为机读规则

```yaml
SHANGHAI.subject_mode:
  severity: warning
  value:
    subject_mode: 3+3
  effective_date: '2026-01-01'
  source_evidence_id: shanghai-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：上海本科录取总成绩由 `3` 门统一高考科目加 `3` 门等级性考试科目组成，因此 `subject_mode=3+3`
- 例 2：等级性考试可从 6 门科目中自主选择 3 门，但这一选择空间不改变整体结构仍是固定的 `3+3`

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 上海市教育考试院 / 上海市教委
- 复核负责人: 待指派
