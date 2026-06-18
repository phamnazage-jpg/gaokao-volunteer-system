# guangdong-2026-exam_subject_total

> 对应规则: `GUANGDONG.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "高考文化总成绩卷面满分值为 750 分，由考生相关考试科目的成绩组成。"
> —— 出处: 《广东省普通高等学校招生工作规定》
> URL: https://eea.gd.gov.cn/tzgg/content/post_4896626.html / https://eea.gd.gov.cn/attachment/0/613/613821/4896626.pdf
> 发布日期: 2026-05-13

## 2. 转写为机读规则

```yaml
GUANGDONG.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：750 分对应文化总成绩卷面满分值，不是单科满分
- 例 2：普通类总成绩由语文、数学、外语、首选科目和两门再选科目共同组成

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
