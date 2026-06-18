# shanghai-2026-exam_subject_total

> 对应规则: `SHANGHAI.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "从2017年起，高考总成绩将由统一高考成绩和学生自主选择的普通高中学业水平等级性考试科目成绩组成，总成绩为660分。其中，语文、数学、外语每门满分150分；普通高中学业水平等级考每门满分70分，成绩将按照等第呈现。"
> —— 出处: 《高考“3+3” 成绩怎么算？》
> URL: http://www.shmeea.edu.cn/page/17410/20160913/5770.html
> 发布日期: 2016-09-13
>
> "等级性考试成绩折算成相应分数计入秋季高考总成绩，作为高校招生录取的依据之一。其中，A+为满分70分，E计40分；相邻两级之间的分差均为3分。"
> —— 出处: 《上海市普通高中学业水平考试实施办法（试行）》
> URL: http://www.shmeea.edu.cn/page/17112/20160914/3521.html
> 发布日期: 2016-09-14

## 2. 转写为机读规则

```yaml
SHANGHAI.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 660
  effective_date: '2026-01-01'
  source_evidence_id: shanghai-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：上海官方直接写明“总成绩为660分”，且同时给出 `150*3 + 70*3` 的构成，因此 `exam_subject_total=660`
- 例 2：等级性考试以等第呈现并折算为分值计入总分，但这不会改变总分上限仍为 `660`

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 上海市教育考试院 / 上海市教委
- 复核负责人: 待指派
