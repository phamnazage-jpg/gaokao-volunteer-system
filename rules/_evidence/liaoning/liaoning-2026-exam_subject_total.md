# liaoning-2026-exam_subject_total

> 对应规则: `LIAONING.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生总成绩由统一高考的语文、数学、外语成绩和选择性考试科目成绩构成，总分为 750分。"
>
> "语文和数学以原始分计入总成绩，满分均为150分。"
> —— 出处: 《辽宁省2021年普通高校招生考试和录取工作实施方案》
> URL: https://www.lnzsks.com/newsinfo/IMS_20201229_40023_h475A2vmua.htm
> 发布日期: 2020-12-29

## 2. 转写为机读规则

```yaml
LIAONING.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁新高考总分量纲为 `750`，不是旧高考文理分科口径之外的其它分值
- 例 2：外语听力单列组织，但总分机读字段仍应记录总成绩上限 `750`

## 4. 后续维护

- 下次复核时间: 2026-06-30
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
