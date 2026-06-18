# liaoning-2026-batch

> 对应规则: `LIAONING.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类录取批次划分为：本科提前批、本科批、高职（专科）提前批、高职（专科）批。"
>
> "本科批次实行平行志愿投档，设置112个“专业+学校”志愿。"
> —— 出处: 《辽宁省2024年普通高校招生志愿填报及招生录取问答》
> URL: https://www.lnzsks.com/newsinfo/IMS_20240619_44007_hZ6qDmgcpv.htm
> 发布日期: 2024-06-19

## 2. 转写为机读规则

```yaml
LIAONING.batch:
  severity: info
  value:
    batch: 本科批
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁普通类官方批次名称是 `本科批`，旧值 `普通批` 不是官方表述，应修正
- 例 2：本证据针对普通类主批次，不覆盖普通类本科提前批或高职（专科）批

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
