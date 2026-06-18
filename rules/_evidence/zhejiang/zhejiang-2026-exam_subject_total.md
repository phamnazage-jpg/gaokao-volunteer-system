# zhejiang-2026-exam_subject_total

> 对应规则: `ZHEJIANG.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "语文、数学、外语每门满分150分，按得分计入考生总成绩；选考科目按等级赋分，每门满分100分，"
> "考生满分750分。"
> —— 出处: 《浙江2026年高考招生工作通知发布》
> URL: https://www.zjzs.net/art/2026/5/20/art_30_12294.html
> 发布日期: 2026-05-20

## 2. 转写为机读规则

```yaml
ZHEJIANG.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: zhejiang-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：浙江总分由语数外 3 门原始分和 3 门选考赋分组成，因此 `exam_subject_total=750` 可以直接由官方总分表述闭环
- 例 2：选考科目采用等级赋分，但总分上限仍明确是 750，这一点与是否原始分计入无冲突

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 浙江省教育考试院
- 复核负责人: 待指派
