# zhejiang-2026-adjustment_scope

> 对应规则: `ZHEJIANG.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业平行志愿投档时，直接投档到某院校某专业（类），不存在专业服从调剂，考生也不用担心被调剂到自己不喜欢的专业。"
> —— 出处: 《浙江省2026年高考招生志愿填报百问百答》
> URL: https://www.zjzs.net/art/2026/6/17/art_45_12386.html
> 发布日期: 2026-06-17
>
> "若投档后被退档，说明一轮一次的机会已经使用，其他专业平行志愿也不能再投档，只能参加剩余计划的下一轮志愿填报和投档。"
> —— 出处: 《浙江省2026年高考招生志愿填报百问百答》
> URL: https://www.zjzs.net/art/2026/6/17/art_45_12386.html
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
ZHEJIANG.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 无
  effective_date: '2026-01-01'
  source_evidence_id: zhejiang-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：浙江普通类平行录取不存在专业服从调剂，因此 `adjustment_scope` 应写为 `无`
- 例 2：一旦已投档又被退档，后续平行志愿也不会补投，这说明不仅没有调剂范围，连同轮补救空间也没有

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 浙江省教育考试院
- 复核负责人: 待指派
