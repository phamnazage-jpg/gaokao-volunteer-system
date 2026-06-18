# liaoning-2026-subject_mode

> 对应规则: `LIAONING.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "2021年，我省普通高校招生考试实行“3+1+2”模式。"
>
> "考生首先在历史、物理2门科目中自主选择1门作为首选考试科目，然后在化学、生物学、思想政治、地理4门科目中自主选择2门作为再选考试科目。"
> —— 出处: 《辽宁省2021年普通高校招生考试和录取工作实施方案》
> URL: https://www.lnzsks.com/newsinfo/IMS_20201229_40023_h475A2vmua.htm
> 发布日期: 2020-12-29

## 2. 转写为机读规则

```yaml
LIAONING.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁新高考选科结构为 `3+1+2`，不是 `3+3`
- 例 2：首选科目在历史、物理中二选一，再选科目在化学、生物学、思想政治、地理中四选二

## 4. 后续维护

- 下次复核时间: 2026-06-30
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
