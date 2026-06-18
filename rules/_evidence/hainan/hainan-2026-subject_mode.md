# hainan-2026-subject_mode

> 对应规则: `HAINAN.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生的高考总分包括高考综合分和照顾加分之和。其中高考综合分由统一高考的语文、数学、外语3个科目成绩和考生高中学业水平选择性考试3个科目成绩组成。"
> —— 出处: 《2026年海南省普通高校招生实施办法》
> URL: http://ea.hainan.gov.cn/ywdt/ptgkyjszsb/202605/t20260528_4083583.html
> 发布日期: 2026-05-28

## 2. 转写为机读规则

```yaml
HAINAN.subject_mode:
  severity: warning
  value:
    subject_mode: 3+3
  effective_date: '2026-01-01'
  source_evidence_id: hainan-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：海南官方没有直接写出字符串 `3+3`，但已明确“统一高考 3 科 + 选择性考试 3 科”的结构，因此 truth 层归一化为 `subject_mode: 3+3`
- 例 2：这里记录的是结构模式，不展开到具体选考科目名称和赋分细节

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 海南省考试局
- 复核负责人: 待指派
