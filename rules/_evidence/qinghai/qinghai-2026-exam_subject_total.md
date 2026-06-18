# qinghai-2026-exam_subject_total

> 对应规则: `QINGHAI.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生高考文化课成绩由全国统考科目成绩和选考科目成绩组成，满分750分。"
>
> "其中，3门全国统考科目每科满分150分……考生自主选择的3门选考科目每科满分100分。"
> —— 出处: 《青海省2025年普通高等学校考试招生录取工作实施方案》
> URL: https://www.qhjyks.com/gkzhgg/zcwj/5153.htm
> 发布日期: 2025-02-17

## 2. 转写为机读规则

```yaml
QINGHAI.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: qinghai-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：青海高考文化课总分是 `750`，由 `3*150 + 3*100` 组成
- 例 2：民族语文成绩和艺术体育专业成绩有独立使用场景，但不改写普通高考文化课总分量纲

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 青海省教育考试网
- 复核负责人: 待指派
