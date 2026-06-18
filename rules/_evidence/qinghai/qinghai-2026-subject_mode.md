# qinghai-2026-subject_mode

> 对应规则: `QINGHAI.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "我省普通高考采用“3+1+2”考试模式。"
>
> "考生首先在历史、物理2科中自主选择1科作为首选考试科目，然后在思想政治、地理、化学、生物学4科中自主选择2科作为再选考试科目。"
> —— 出处: 《青海省2025年普通高等学校考试招生录取工作实施方案》
> URL: https://www.qhjyks.com/gkzhgg/zcwj/5153.htm
> 发布日期: 2025-02-17

## 2. 转写为机读规则

```yaml
QINGHAI.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: qinghai-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：青海新高考主体选科结构已经明确切到 `3+1+2`，不能再沿用旧文理分科思维
- 例 2：民族语文考试、艺术体育省级统考是附加要求，不改变普通高考主体 `3+1+2` 结构

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 青海省教育考试网
- 复核负责人: 待指派
