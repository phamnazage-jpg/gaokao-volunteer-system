# xinjiang-2026-adjustment_scope

> 对应规则: `XINJIANG.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "进行以上操作后，系统会提示需要在“统招调剂”或“定向调剂”选项中选择“服从”或“不服从”。"
> —— 出处: 《2026年新疆高考志愿填报系统操作手册》
> URL: http://www.xjzk.gov.cn/upload/resources/file/2026/06/12/30062.pdf
> 发布日期: 2026-06-12

## 2. 转写为机读规则

```yaml
XINJIANG.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 全部专业
  effective_date: '2026-01-01'
  source_evidence_id: xinjiang-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：系统给的是“统招调剂 / 定向调剂”整体开关，没有细分到单个专业，因此项目继续按院校内可调剂专业整体机读为 `全部专业`
- 例 2：这里的 `全部专业` 不是跨院校调剂，而是对当前已填报院校对应计划内专业的统招或定向调剂开关归一化表达

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 新疆教育考试院
- 复核负责人: 待指派
