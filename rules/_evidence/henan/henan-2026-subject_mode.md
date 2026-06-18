# henan-2026-subject_mode

> 对应规则: `HENAN.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "全国统考科目为语文、数学、外语3门，外语科目考试含笔试和听力两个部分；选择性考试科目由考生从历史和物理2门首选科目中任选1门，从思想政治、地理、化学、生物学4门再选科目中任选2门。"
> —— 出处: 《河南省2026年普通高等学校招生工作规定》
> URL: https://xcoss.henan.gov.cn/typtfile/20260427/cc9d5c1a332341f0a7d9223f54f0cf62.pdf
> 发布日期: 2026-04-22

## 2. 转写为机读规则

```yaml
HENAN.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: henan-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：河南 2026 已明确进入 `3+1+2` 新高考模式，不能继续保留 `传统`
- 例 2：`3+1+2` 中的 `1` 为历史/物理首选，`2` 为思想政治、地理、化学、生物学中的再选科目

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 河南
- 复核负责人: 待指派
