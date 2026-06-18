# guangxi-2026-exam_subject_total

> 对应规则: `GUANGXI.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生总成绩由3门全国统考科目成绩和3门选择性考试科目成绩组成，满分750分。"
>
> "其中，全国统考科目每门满分150分，选择性考试科目每门满分100分。"
> —— 出处: 《自治区教育厅关于印发〈广西2026年普通高校招生考试和录取工作方案〉的通知》
> URL: https://www.gxeea.cn/view/content_1013_32810.htm
> 发布日期: 2026-06-03

## 2. 转写为机读规则

```yaml
GUANGXI.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: guangxi-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：广西普通高考文化总分是 `750`，该值同时被艺术类和体育类综合分公式作为换算基准
- 例 2：外语口试成绩不计入高考总分，不能把口试等级混入 `exam_subject_total`

## 4. 后续维护

- 下次复核时间: 2026-07-10
- 复核来源: 广西招生考试院
- 复核负责人: 待指派
