# liaoning-2026-max_majors_per_group

> 对应规则: `LIAONING.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业平行志愿，是新高考招生同一类别、同一批次中若干具有相对平行关系的专业志愿，以一所院校的一个专业为志愿单位。"
>
> "本科批次实行平行志愿投档，设置112个“专业+学校”志愿，1个“专业+学校”为1个志愿。"
> —— 出处: 《辽宁省2024年普通高校招生志愿填报及招生录取问答》
> URL: https://www.lnzsks.com/newsinfo/IMS_20240619_44007_hZ6qDmgcpv.htm
> 发布日期: 2024-06-19

## 2. 转写为机读规则

```yaml
LIAONING.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 1
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁普通类本科批以 `1个“专业+学校”为1个志愿`，因此每组专业上限应记为 `1`
- 例 2：这不是院校专业组模式，不存在组内多个专业可填的情况

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
