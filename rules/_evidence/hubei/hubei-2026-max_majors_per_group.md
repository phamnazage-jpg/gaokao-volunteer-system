# hubei-2026-max_majors_per_group

> 对应规则: `HUBEI.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科普通批包括未列入本科提前批的普通类本科专业。考生可填报不超过45个院校专业组志愿，每个院校专业组志愿内可以选报不超过6个专业及是否服从专业调剂。"
> —— 出处: 《各批次志愿结构如何设置的？》
> URL: https://www.hbksw.com/info/41/1047.html
> 发布日期: 页面未标注（湖北省普通高校招生阳光招生问答公开页）

## 2. 转写为机读规则

```yaml
HUBEI.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: hubei-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：每组上限是“6 个专业 + 是否服从专业调剂”这一组合，布尔调剂选项不计入 6 个专业名额
- 例 2：湖北的 6 个专业是组内专业上限，不意味着考生只能填报 6 个总志愿；总志愿单位仍是院校专业组

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 湖北招生考试网 / 湖北省教育考试院
- 复核负责人: 待指派
