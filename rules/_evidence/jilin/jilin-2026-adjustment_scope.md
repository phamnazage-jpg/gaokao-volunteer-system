# jilin-2026-adjustment_scope

> 对应规则: `JILIN.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿均设置6个专业志愿和是否服从专业调剂选项。"
>
> "服从调剂，需确认该专业组内所有专业均可接受。"
> —— 出处: 《吉林省2026年普通高考志愿填报及录取时间安排》 / 《吉林省2026年普通高考志愿填报核心要点问答集锦》
> URL: https://www.jleea.com.cn/front/content/202704
> URL: https://www.jleea.com.cn/front/content/202714
> 发布日期: 2026-06-15 / 2026-06-16

## 2. 转写为机读规则

```yaml
JILIN.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: jilin-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：吉林普通类本科批明确存在“是否服从专业调剂”选项，调剂范围应限定在当前院校专业组内，而不是写成 `无`
- 例 2：这里记录的是普通类院校专业组口径，不外推到提前批顺序志愿中单独院校的特殊录取规则

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 吉林省教育考试院
- 复核负责人: 待指派
