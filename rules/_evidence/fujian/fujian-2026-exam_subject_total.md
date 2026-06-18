# fujian-2026-exam_subject_total

> 对应规则: `FUJIAN.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生高考总成绩由语文、数学、外语3门全国统一考试科目成绩和3门全省普通高中学业水平选择性考试科目成绩构成，文考总分满分750分；如有政策性加分，则一并计入考生高考总成绩。"
> —— 出处: 《2026年福建省普通高等学校招生录取实施办法》
> URL: http://www.eeafj.cn/gkptgkgsgg/20260612/14670.html
> 发布日期: 2026-06-11 / 2026-06-12 发布

## 2. 转写为机读规则

```yaml
FUJIAN.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: fujian-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：福建官方已直接写明“文考总分满分750分”，因此 `exam_subject_total=750`
- 例 2：政策性加分会计入高考总成绩，但不改变文考总分基础量纲上限仍为 `750`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 福建省教育考试院
- 复核负责人: 待指派
