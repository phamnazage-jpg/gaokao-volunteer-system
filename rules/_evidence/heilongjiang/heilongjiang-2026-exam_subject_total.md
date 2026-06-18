# heilongjiang-2026-exam_subject_total

> 对应规则: `HEILONGJIANG.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生总成绩由3门全国统考科目成绩和3门选择性考试科目成绩组成，满分750分。"
>
> "其中，全国统考科目每门满分150分，选择性考试科目每门满分100分。"
> —— 出处: 《黑龙江省2024年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202401/t20240129_18920.htm
> 发布日期: 2024-01-29

## 2. 转写为机读规则

```yaml
HEILONGJIANG.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: heilongjiang-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：黑龙江普通高考文化总分量纲为 `750`，不是旧表述中的单科等第或综合分换算值
- 例 2：艺术类、体育类综合分公式中也会出现 `×750` 的换算，但基础文化总分口径仍是 `750`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 黑龙江省招生考试信息港
- 复核负责人: 待指派
