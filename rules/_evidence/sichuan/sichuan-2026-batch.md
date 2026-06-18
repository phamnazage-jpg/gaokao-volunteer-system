# sichuan-2026-batch

> 对应规则: `SICHUAN.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类共设置4个批次，包括本科提前批次、本科批次、高职（专科）提前批次和高职（专科）批次，按顺序依次录取。"
> —— 出处: 《四川省2026年普通高校招生实施规定》
> URL: http://www.sceea.cn/Html/202604/Newsdetail_4767.html
> 发布日期: 2026-04-21 / 2026-04-23 发布

## 2. 转写为机读规则

```yaml
SICHUAN.batch:
  severity: info
  value:
    batch: 本科一批
  effective_date: '2026-01-01'
  source_evidence_id: sichuan-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：四川 2026 已使用新高考分段批次，本科主流程归一化为 `本科批`，不能继续沿用旧的 `本科一批`
- 例 2：官方实际细分为本科批次 A 段、B 段，但 province-level truth 这里只保留高层批次标签，不把分段拆成单独字段

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 四川省教育考试院
- 复核负责人: 待指派
