# henan-2026-exam_subject_total

> 对应规则: `HENAN.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生高考文化成绩由全国统考科目成绩和选择性考试科目成绩组成，满分750分。全国统考科目中语文、数学，每门满分150分，使用原始成绩计入考生高考文化成绩；外语满分150分。3门选择性考试科目，每门满分100分。"
> —— 出处: 《河南省2026年普通高等学校招生工作规定》
> URL: https://xcoss.henan.gov.cn/typtfile/20260427/cc9d5c1a332341f0a7d9223f54f0cf62.pdf
> 发布日期: 2026-04-22

## 2. 转写为机读规则

```yaml
HENAN.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: henan-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：总分口径是高考文化成绩 `750` 分，不是旧高考综合分或院校投档特殊加权分
- 例 2：再选科目采用等级赋分后计入总分，但总量纲仍是 `750`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 河南
- 复核负责人: 待指派
