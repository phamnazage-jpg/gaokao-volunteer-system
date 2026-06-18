# xinjiang-2026-exam_subject_total

> 对应规则: `XINJIANG.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生成绩以总分750分，语文、数学、外语三科各150分，文科综合/理科综合科目300分为计分标准。"
> —— 出处: 《新疆维吾尔自治区2026年普通高校招生工作规定》
> URL: http://www.xjzk.gov.cn/c/2026-05-06/495190.shtml
> 发布日期: 2026-05-06

## 2. 转写为机读规则

```yaml
XINJIANG.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: xinjiang-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：新疆 2026 普通类总分仍是 `750`，不是新高考部分省份常见的 `660`、`900` 等口径
- 例 2：外语听力单列计分参考不改变普通高考总分机读值 `750`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 新疆教育考试院
- 复核负责人: 待指派
