# shandong-2026-adjustment_scope

> 对应规则: `SHANDONG.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "常规批。包括教育部高校专项计划、地方专项计划以及未列入提前批的其他本、专科招生。安排3次志愿填报，均实行以“专业（专业类）+学校”为单位的平行志愿模式，1个“专业（专业类）+学校”为1个志愿。"
> —— 出处: 《山东省2026年普通高等学校考试招生（夏季高考）工作实施办法》
> URL: https://www.sdzk.cn/NewsInfo.aspx?NewsID=7200 / https://www.sdzk.cn/Floadup/file/20260518/6391471212594395957059302.doc
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
SHANDONG.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 无
  effective_date: '2026-01-01'
  source_evidence_id: shandong-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：常规批的志愿颗粒已经细化到单个专业（专业类）+学校，因此没有“组内专业调剂”这个落点
- 例 2：若后续特殊类型批次另有专业服从条款，应单独建证据，不沿用本条

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 山东省教育招生考试院
- 复核负责人: 待指派
