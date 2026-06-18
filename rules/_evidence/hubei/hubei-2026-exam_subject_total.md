# hubei-2026-exam_subject_total

> 对应规则: `HUBEI.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生总成绩由全国统考的语文、数学、外语科目成绩和考生选择的3门普通高中学业水平选择性考试科目成绩组成，满分750分。"
> "其中全国统考的语文、数学、外语3门科目，每科满分150分。"
> —— 出处: 《湖北省2026年普通高等学校招生考试报名须知》
> URL: https://www.hbksw.com/info/5/2034.html
> 发布日期: 2025-11-01（页面公开时间）

## 2. 转写为机读规则

```yaml
HUBEI.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: hubei-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：750 分是湖北普通高校全国统考主流程总分，不适用于技能高考 700 分体系
- 例 2：选择性考试科目单科满分 100 分，但再选科目按等级分计入总成绩，不能简单理解为所有 6 科都按原始分相加

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 湖北招生考试网 / 湖北省教育考试院
- 复核负责人: 待指派
