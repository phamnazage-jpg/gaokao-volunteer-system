# heilongjiang-2026-subject_mode

> 对应规则: `HEILONGJIANG.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "2024年，我省统一普通高校招生考试实行“3+1+2”模式，包括3门普通高等学校招生全国统一考试科目和3门普通高中学业水平选择性考试科目。"
>
> "选择性考试科目由考生从物理和历史2门首选科目中任选1门，从思想政治、地理、化学、生物学4门再选科目中任选2门。"
> —— 出处: 《黑龙江省2024年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202401/t20240129_18920.htm
> 发布日期: 2024-01-29

## 2. 转写为机读规则

```yaml
HEILONGJIANG.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: heilongjiang-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：黑龙江选科结构是统一高考 `3` 门加选择性考试 `1+2`，不是旧文理分科
- 例 2：艺术类、体育类仍共享该文化课与选考结构，只是在录取排序公式上另有专业成绩权重

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 黑龙江省招生考试信息港
- 复核负责人: 待指派
