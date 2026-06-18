# zhejiang-2026-max_majors_per_group

> 对应规则: `ZHEJIANG.max_majors_per_group`
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
> "普通类平行录取实行专业平行志愿，以1所高校的1个专业（类）作为1个独立的志愿单位，考生每次可填报不超过80个志愿。"
> —— 出处: 《浙江省2026年高考招生志愿填报百问百答》
> URL: https://www.zjzs.net/art/2026/6/17/art_45_12386.html
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
ZHEJIANG.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 1
  effective_date: '2026-01-01'
  source_evidence_id: zhejiang-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：浙江普通类平行录取没有“专业组”概念，每个志愿单位只对应 1 个专业（类），因此 `max_majors_per_group=1`
- 例 2：这里的 `1` 描述的是单个志愿单位内可承载的专业数，不是考生总可填报专业数；考生总量仍由 `max_volunteers=80` 控制

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 浙江省教育考试院
- 复核负责人: 待指派
