# guizhou-2026-exam_subject_total

> 对应规则: `GUIZHOU.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "播音与主持类综合成绩=高考总成绩×60%+（专业省级统考成绩÷专业省级统考成绩满分×750）×40%"
>
> "美术与设计类、音乐类、舞蹈类、表（导）演类、书法类综合成绩=高考总成绩×50%+（专业省级统考成绩÷专业省级统考成绩满分×750）×50%"
> —— 出处: 《贵州省2025年高考填报志愿规定》
> URL: http://zsksy.guizhou.gov.cn/ptgk/qtxx/202506/t20250625_88190180.html
> 发布日期: 2025-06-25

## 2. 转写为机读规则

```yaml
GUIZHOU.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: guizhou-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：官方在艺术类综合成绩公式中直接使用 `×750` 作为高考总成绩量纲，项目层据此记录普通高考文化总分标尺 `exam_subject_total: 750`
- 例 2：这里采用的是对官方公式的结构化归纳，不把专业统考分值体系混进 `exam_subject_total`，仅保留高考总成绩统一量纲

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 贵州省招生考试院
- 复核负责人: 待指派
