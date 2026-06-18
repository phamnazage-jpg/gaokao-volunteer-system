# chongqing-2026-batch

> 对应规则: `CHONGQING.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "（一）普通类。设置本科提前批、本科批、高职专科提前批、高职专科批4个批次。"
>
> "2.本科批……设置96个专业平行志愿。"
> —— 出处: 《录取批次及志愿设置》
> URL: https://www.cqksy.cn/web/article/2025-06/17/content_6631.html
> 发布日期: 2025-06-17

## 2. 转写为机读规则

```yaml
CHONGQING.batch:
  severity: info
  value:
    batch: 本科批
  effective_date: '2026-01-01'
  source_evidence_id: chongqing-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：重庆普通类主规则对应的是 `本科批`，不能继续沿用泛化旧值 `普通批`
- 例 2：本科提前批和高职专科批是并列批次，不应并入普通类 `本科批` 规则

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 重庆市教育考试院
- 复核负责人: 待指派
