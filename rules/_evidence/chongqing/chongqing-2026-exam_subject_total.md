# chongqing-2026-exam_subject_total

> 对应规则: `CHONGQING.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "统一高考总成绩由全国统一考试的语文、数学、外语3科成绩和学业水平选择性考试首选科目1科、再选科目2科成绩组成，总分满分为 750 分。"
> —— 出处: 《重庆市2025年普通高等学校招生工作实施办法》
> URL: https://jw.cq.gov.cn/zwxx_209/gggs/202505/t20250512_14601180.html
> 发布日期: 2025-05-12

## 2. 转写为机读规则

```yaml
CHONGQING.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: chongqing-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：重庆统一高考总分满分为 `750` 分，不能误写成上海 `660` 或海南 `900`
- 例 2：`750` 由全国统考 `450` 分和选择性考试 `300` 分共同组成，不是单一考试部分的分值

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 重庆市教育委员会
- 复核负责人: 待指派
