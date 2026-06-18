# shandong-2026-subject_mode

> 对应规则: `SHANDONG.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "我省夏季高考实行“3+3”考试模式，包括国家统一高考语文、数学、外语（听力和笔试）等3科，以及考生从普通高中学业水平等级考试思想政治、历史、地理、物理、化学、生物等6科中选报的3科。"
> —— 出处: 《山东省2026年普通高等学校考试招生（夏季高考）工作实施办法》
> URL: https://www.sdzk.cn/NewsInfo.aspx?NewsID=7200 / https://www.sdzk.cn/Floadup/file/20260518/6391471212594395957059302.doc
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
SHANDONG.subject_mode:
  severity: warning
  value:
    subject_mode: 3+3
  effective_date: '2026-01-01'
  source_evidence_id: shandong-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：山东 2026 普通类与艺术类、体育类共用的选科框架都是 `3+3`
- 例 2：本条只描述夏季高考模式，不覆盖中职、春季高考等其它考试体系

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 山东省教育招生考试院
- 复核负责人: 待指派
