# yunnan-2026-exam_subject_total

> 对应规则: `YUNNAN.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生高考文化成绩（以下简称文化成绩）由3门全国统考科目成绩和3门选择性考试科目成绩构成，总分为750分。"
>
> "全国统考科目语文、数学、外语卷面满分均为150分……选择性考试科目各科卷面满分均为100分。"
> —— 出处: 《云南省2025年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.ynzs.cn/html/content/7511.html
> 发布日期: 2025-01-23

## 2. 转写为机读规则

```yaml
YUNNAN.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: yunnan-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：云南普通高考文化成绩量纲已明确是 `750` 分，不应与艺体专业统考或其他附加考试分值体系混淆
- 例 2：证据层保留了 `3门150分 + 3门100分` 的构成说明，避免把 `750` 当成脱离结构的裸数字

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 云南省招生考试院
- 复核负责人: 待指派
