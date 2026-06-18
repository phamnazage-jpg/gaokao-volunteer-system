# liaoning-2026-max_volunteers

> 对应规则: `LIAONING.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "以上三种组合形式，共同组成112个志愿（普通类本科批）。"
>
> "本科批次实行平行志愿投档，设置112个“专业+学校”志愿，1个“专业+学校”为1个志愿，考生可填报的志愿最大数量为112个。"
> —— 出处: 《辽宁省2024年普通高校招生志愿填报及招生录取问答》
> URL: https://www.lnzsks.com/newsinfo/IMS_20240619_44007_hZ6qDmgcpv.htm
> 发布日期: 2024-06-19

## 2. 转写为机读规则

```yaml
LIAONING.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 112
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁普通类本科批志愿上限是 `112`，不是旧值或其它省常见的 `45`、`60`
- 例 2：高职（专科）批另有 `60` 个“专业+学校”志愿，本规则只记录普通类本科批主口径

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
