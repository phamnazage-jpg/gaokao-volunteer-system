# shandong-2026-retrieval_rule

> 对应规则: `SHANDONG.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "各类型各批次实行平行志愿投档录取的专业，考生成绩相同时，依次按语文数学总成绩、语文或数学单科最高成绩、外语单科成绩、等级考试选考科目单科最高成绩、等级考试选考科目单科次高成绩由高到低排序；如仍相同，比较考生志愿顺序，顺序在前者优先投档，志愿顺序相同则全部投档。"
> —— 出处: 《山东省2026年普通高等学校考试招生（夏季高考）工作实施办法》
> URL: https://www.sdzk.cn/NewsInfo.aspx?NewsID=7200 / https://www.sdzk.cn/Floadup/file/20260518/6391471212594395957059302.doc
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
SHANDONG.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿；同分按单科顺序比较，志愿顺序前者优先投档
  effective_date: '2026-01-01'
  source_evidence_id: shandong-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：官方原文把平行志愿的排序规则写得很细，但并没有直接用“一次投档”这类简化表述
- 例 2：本条只覆盖夏季高考普通类平行志愿主流程，不替代特殊类型批次的顺序志愿规则

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 山东省教育招生考试院
- 复核负责人: 待指派
