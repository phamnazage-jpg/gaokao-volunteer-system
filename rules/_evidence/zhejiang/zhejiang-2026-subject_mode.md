# zhejiang-2026-subject_mode

> 对应规则: `ZHEJIANG.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类考试科目为语文、数学、外语3门必考科目和3门选考科目。"
> "选考科目由考生根据本人兴趣特长和拟报考学校及专业的要求，从思想政治、历史、地理、物理、化学、生物学、技术（含通用技术和信息技术）等7门科目中，选择3门作为高考选考科目。"
> —— 出处: 《浙江2026年高考招生工作通知发布》
> URL: https://www.zjzs.net/art/2026/5/20/art_30_12294.html
> 发布日期: 2026-05-20

## 2. 转写为机读规则

```yaml
ZHEJIANG.subject_mode:
  severity: warning
  value:
    subject_mode: 3+3
  effective_date: '2026-01-01'
  source_evidence_id: zhejiang-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：浙江普通类由 3 门统考必考科目和 3 门自选科目组成，因此 `subject_mode` 应表达为 `3+3`
- 例 2：选考范围虽有 7 门，但最终计入录取的是其中选择的 3 门，不应误写为 `3+7`

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 浙江省教育考试院
- 复核负责人: 待指派
