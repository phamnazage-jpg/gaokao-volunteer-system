# sichuan-2026-exam_subject_total

> 对应规则: `SICHUAN.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生高考文化成绩由3门全国统考科目成绩和3门选择考科目成绩组成，满分750分。"
>
> "其中，全国统考科目每门满分150分、选择考科目每门满分100分。"
> —— 出处: 《四川省2026年普通高校招生实施规定》
> URL: http://www.sceea.cn/Html/202604/Newsdetail_4767.html
> 发布日期: 2026-04-21 / 2026-04-23 发布

## 2. 转写为机读规则

```yaml
SICHUAN.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: sichuan-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：四川官方已直接写明“满分750分”，并给出 `150*3 + 100*3` 的构成，因此 `exam_subject_total=750`
- 例 2：录取照顾政策加分在投档时另行附加，但不改变高考文化成绩基础量纲上限仍为 `750`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 四川省教育考试院
- 复核负责人: 待指派
