# tianjin-2026-exam_subject_total

> 对应规则: `TIANJIN.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "高考总成绩满分值为750分。其中，统一高考各科目成绩均以原始分数的方式呈现，语文、数学、外语科目成绩满分均为150分。考生自主选择的3门等级性考试成绩以等级方式呈现，在计入高校招生录取总成绩时，每门科目成绩满分均为100分。"
> —— 出处: 《2026年天津市普通高校招生工作规定》
> URL: http://www.zhaokao.net/zwgk/doc/003/000/114/00300011419_edf58f9e.pdf
> 发布日期: 2026-04-29

## 2. 转写为机读规则

```yaml
TIANJIN.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: tianjin-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：天津 `3+3` 模式下统一高考三科各 `150分`，等级考三科折算后各 `100分`，总分仍为 `750`
- 例 2：不能把等级性考试误解为原始分累加，官方明确是“以等级方式呈现”后计入总分

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 天津教育招生考试院
- 复核负责人: 待指派
