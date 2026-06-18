# jilin-2026-exam_subject_total

> 对应规则: `JILIN.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生报名参加我省普通高考，须参加语文、数学、外语3门科目的全国统一考试，还须参加我省普通高中学业水平选择性考试。"
>
> "以750分为高考满分计算。"
> —— 出处: 《吉林省2026年普通高考报名相关事项问答》 / 《2026年吉林省普通高校招生指南下册》
> URL: https://www.jleea.com.cn/front/content/202052
> URL: http://www.jleea.com.cn/u/cms/www/2026/06/16/2066753530684858370.pdf
> 发布日期: 2025-09-08 / 2026-06-16

## 2. 转写为机读规则

```yaml
JILIN.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: jilin-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：吉林报名问答已确认高考成绩由 `3+1+2` 六科结构组成，招生指南附件又明确出现“以750分为高考满分计算”，因此机读总分应保持 `750`
- 例 2：`750` 的直接表述出现在招生指南对招生院校录取说明的满分换算语境中，这里据此与报名问答的六科结构联合归一为全省普通高考总分量纲

## 4. 后续维护

- 下次复核时间: 2026-06-30
- 复核来源: 吉林省教育考试院
- 复核负责人: 待指派
