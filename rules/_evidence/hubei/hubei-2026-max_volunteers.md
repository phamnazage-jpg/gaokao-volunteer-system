# hubei-2026-max_volunteers

> 对应规则: `HUBEI.max_volunteers`
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
HUBEI.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 45
  effective_date: '2026-01-01'
  source_evidence_id: hubei-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：45 个是湖北普通类本科普通批的院校专业组志愿上限，不是本科提前批或高职高专批的统一上限
- 例 2：同页明确高职高专普通批为 20 个院校专业组志愿，因此当前 truth 的 `45` 只绑定本科主流程

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 湖北招生考试网 / 湖北省教育考试院
- 复核负责人: 待指派
