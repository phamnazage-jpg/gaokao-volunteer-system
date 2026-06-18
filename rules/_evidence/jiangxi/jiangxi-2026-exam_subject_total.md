# jiangxi-2026-exam_subject_total

> 对应规则: `JIANGXI.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "答：普通高考考生文化总成绩由语文、数学、外语3门全国统一考试科目成绩和3门选择性考试科目成绩组成，总分为750分。语文、数学、外语卷面满分值各为150分，按卷面原始分直接计入考生总成绩。选择性考试科目卷面满分值各为100分。"
> —— 出处: 《7.普通高考考生文化总成绩是如何组成的？》
> URL: http://www.jxeea.cn/jxsjyksy/gkzhggw5049/content/content_1856054497186877440.html
> 发布日期: 2023-09-14

## 2. 转写为机读规则

```yaml
JIANGXI.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: jiangxi-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：江西普通高考文化总成绩量纲已明确是 `750` 分，不应混入艺体专业统考等其他分值体系
- 例 2：证据层同时保留了 `3门150分 + 3门100分` 的组成说明，避免把 `750` 当成脱离上下文的裸数字

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 江西
- 复核负责人: 待指派
