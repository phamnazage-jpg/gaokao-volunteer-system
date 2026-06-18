# hubei-2026-batch

> 对应规则: `HUBEI.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类分为本科提前批、本科普通批、高职高专提前批、高职高专普通批四个批次。"
> "本科普通批包括未列入本科提前批的普通类本科专业。"
> —— 出处: 《各批次志愿结构如何设置的？》
> URL: https://www.hbksw.com/info/41/1047.html
> 发布日期: 页面未标注（湖北省普通高校招生阳光招生问答公开页）

## 2. 转写为机读规则

```yaml
HUBEI.batch:
  severity: info
  value:
    batch: 本科批
  effective_date: '2026-01-01'
  source_evidence_id: hubei-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：官方普通类有四个批次，当前 truth 把规则归一到“本科批”这一项目层统一字段，实际对应主审计对象是本科普通批
- 例 2：`max_volunteers=45` 与 `collection_count=2` 都是围绕本科普通批摘录；高职高专批次的数量和时间安排另有差异

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 湖北招生考试网 / 湖北省教育考试院
- 复核负责人: 待指派
