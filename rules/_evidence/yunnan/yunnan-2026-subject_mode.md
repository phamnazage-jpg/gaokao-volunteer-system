# yunnan-2026-subject_mode

> 对应规则: `YUNNAN.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "自2025年起，云南省普通高校招生统一考试（以下简称普通高考）实行“3+1+2”模式。"
>
> "“1”为选择性考试首选科目，考生从物理、历史中选择1门；“2”为选择性考试再选科目，考生从化学、地理、思想政治、生物学中选择2门。"
> —— 出处: 《云南省2025年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.ynzs.cn/html/content/7511.html
> 发布日期: 2025-01-23

## 2. 转写为机读规则

```yaml
YUNNAN.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: yunnan-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：云南从 2025 年起已正式实施新高考 `3+1+2`，`subject_mode=传统` 已与官方口径冲突
- 例 2：这里记录的是选科结构，不展开外语语种选择和赋分换算公式的实现细节

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 云南省招生考试院
- 复核负责人: 待指派
