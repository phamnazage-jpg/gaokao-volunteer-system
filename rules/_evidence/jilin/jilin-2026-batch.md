# jilin-2026-batch

> 对应规则: `JILIN.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类分为提前批、本科批及专科批三个批次。"
>
> "本科批设50个院校专业组平行志愿。"
> —— 出处: 《吉林省2026年普通高考志愿填报及录取时间安排》
> URL: https://www.jleea.com.cn/front/content/202704
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
JILIN.batch:
  severity: info
  value:
    batch: 本科批
  effective_date: '2026-01-01'
  source_evidence_id: jilin-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：吉林普通类主批次官方名称是 `本科批`，旧值 `普通批` 不是当前官方口径
- 例 2：普通类提前批、专科批也分别独立存在，本规则只记录普通类主批次

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 吉林省教育考试院
- 复核负责人: 待指派
