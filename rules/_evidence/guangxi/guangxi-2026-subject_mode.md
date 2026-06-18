# guangxi-2026-subject_mode

> 对应规则: `GUANGXI.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "2026年，我区高考继续实行“3+1+2”模式，包括3门全国统一考试科目和3门普通高中学业水平选择性考试科目。"
>
> "选择性考试科目由考生从物理和历史2门首选科目中任选1门，从思想政治、地理、化学、生物学4门再选科目中任选2门。"
> —— 出处: 《自治区教育厅关于印发〈广西2026年普通高校招生考试和录取工作方案〉的通知》
> URL: https://www.gxeea.cn/view/content_1013_32810.htm
> 发布日期: 2026-06-03

## 2. 转写为机读规则

```yaml
GUANGXI.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: guangxi-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：广西是标准 `3+1+2` 新高考结构，不是旧文理分科
- 例 2：艺术类、体育类的专业成绩另算，但文化课和选考结构仍基于 `3+1+2`

## 4. 后续维护

- 下次复核时间: 2026-07-10
- 复核来源: 广西招生考试院
- 复核负责人: 待指派
