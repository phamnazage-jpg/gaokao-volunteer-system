# jiangxi-2026-has_adjustment

> 对应规则: `JIANGXI.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "新高考按照“院校专业组”模式设置志愿，每个“院校专业组”即为一个独立的志愿，内设6个专业志愿和是否服从专业调剂志愿。"
>
> "我省新高考录取按照“院校专业组”模式设置志愿，每个“院校专业组”即为一个独立的志愿，内设6个专业志愿，考生在每个院校专业组志愿中均须选择是否服从专业调剂。"
> —— 出处: 《十六、新高考志愿如何设置？》 / 《二十三、什么是“院校专业组”模式？》
> URL: http://www.jxeea.cn/jxsjyksy/cjwd22/content/content_1856071455097688064.html
> URL: http://www.jxeea.cn/jxsjyksy/cjwd22/content/content_1856080743677497344.html
> 发布日期: 2024-06-21 / 2024-06-21

## 2. 转写为机读规则

```yaml
JIANGXI.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: jiangxi-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：江西官方问答明确保留 `是否服从专业调剂`，因此 `has_adjustment` 不能写成 `false`
- 例 2：调剂选项是逐个院校专业组选择，不是整张志愿表一次性总开关

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 江西
- 复核负责人: 待指派
