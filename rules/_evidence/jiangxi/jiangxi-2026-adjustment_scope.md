# jiangxi-2026-adjustment_scope

> 对应规则: `JIANGXI.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "我省新高考录取按照“院校专业组”模式设置志愿，每个“院校专业组”即为一个独立的志愿，内设6个专业志愿，考生在每个院校专业组志愿中均须选择是否服从专业调剂。"
>
> "“院校专业组”是将一所院校选择性考试科目要求相同的若干个专业合成一个组，每个组内包含数量不等的专业。"
> —— 出处: 《二十三、什么是“院校专业组”模式？》
> URL: http://www.jxeea.cn/jxsjyksy/cjwd22/content/content_1856080743677497344.html
> 发布日期: 2024-06-21

## 2. 转写为机读规则

```yaml
JIANGXI.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: jiangxi-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：江西官方虽然没有逐字写出“组内专业调剂”，但调剂动作绑定在单个院校专业组志愿上，机读口径应归一化为 `组内专业`
- 例 2：不能把调剂范围误解为同校全部专业或跨院校专业组调剂，否则会扩大官方未授予的范围

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 江西
- 复核负责人: 待指派
