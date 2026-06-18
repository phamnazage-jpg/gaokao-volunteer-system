# beijing-2026-exam_subject_total

> 对应规则: `BEIJING.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "参加本科招生录取的考生总成绩由3门统一高考成绩和考生选考的3门学考等级考成绩构成，总成绩满分值为750分。"
> —— 出处: 《北京市2026年普通高等学校招生工作规定》
> URL: https://www.bjeea.cn/html/gkgz/tzgg/2026/0505/88114.html
> 发布日期: 2026-05-08
>
> "语文、数学、外语满分均为150分。"
> "学考等级考科目成绩按照《北京市教育委员会关于普通高中等级性学业水平考试成绩计入高考总成绩方式的通知》（京教计〔2018〕21号）要求进行折算，每科目满分100分。"
> —— 出处: 《北京市2026年普通高等学校招生工作规定》
> URL: https://www.bjeea.cn/html/gkgz/tzgg/2026/0505/88114.html
> 发布日期: 2026-05-08

## 2. 转写为机读规则

```yaml
BEIJING.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: beijing-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：`750` 适用于北京本科录取总成绩，由 `3` 门统一高考成绩与 `3` 门学考等级考成绩共同构成
- 例 2：专科（高职）录取总成绩不按 `750` 计，而是仅由语文、数学、外语 `3` 门统一高考成绩组成

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 北京
- 复核负责人: 待指派
