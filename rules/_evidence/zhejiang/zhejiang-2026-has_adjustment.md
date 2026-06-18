# zhejiang-2026-has_adjustment

> 对应规则: `ZHEJIANG.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "以1所学校的1个专业（类）作为1个志愿单位。"
> —— 出处: 《浙江2026年高考招生工作通知发布》
> URL: https://www.zjzs.net/art/2026/5/20/art_30_12294.html
> 发布日期: 2026-05-20
>
> "专业平行志愿投档时，直接投档到某院校某专业（类），不存在专业服从调剂，考生也不用担心被调剂到自己不喜欢的专业。"
> —— 出处: 《浙江省2026年高考招生志愿填报百问百答》
> URL: https://www.zjzs.net/art/2026/6/17/art_45_12386.html
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
ZHEJIANG.has_adjustment:
  severity: warning
  value:
    has_adjustment: false
  effective_date: '2026-01-01'
  source_evidence_id: zhejiang-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：浙江普通类平行录取直接以“学校 + 专业（类）”为独立志愿单位，因此没有组内再调剂空间
- 例 2：提前录取传统志愿仍有“专业服从调剂志愿”，但当前 province truth 的 `has_adjustment=false` 只描述普通类平行录取主模式

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 浙江省教育考试院
- 复核负责人: 待指派
