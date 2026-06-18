# jiangxi-2026-max_majors_per_group

> 对应规则: `JIANGXI.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "新高考按照“院校专业组”模式设置志愿，每个“院校专业组”即为一个独立的志愿，内设6个专业志愿和是否服从专业调剂志愿。"
> —— 出处: 《十六、新高考志愿如何设置？》
> URL: http://www.jxeea.cn/jxsjyksy/cjwd22/content/content_1856071455097688064.html
> 发布日期: 2024-06-21

## 2. 转写为机读规则

```yaml
JIANGXI.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: jiangxi-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：江西单个院校专业组内可填 `6` 个专业志愿，不是 1 个专业也不是无限展开
- 例 2：`max_majors_per_group` 描述的是单个志愿组内部专业位数量，不是整张志愿表的院校专业组数量

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 江西
- 复核负责人: 待指派
