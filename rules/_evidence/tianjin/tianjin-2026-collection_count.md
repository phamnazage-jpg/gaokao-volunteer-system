# tianjin-2026-collection_count

> 对应规则: `TIANJIN.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "我市实行两次填报、四次征询的志愿填报方式。"
>
> "7月21日，第二次征询志愿，普通本科批次A阶段征询志愿。"
>
> "7月26日至27日，第三次征询志愿，普通本科批次B阶段征询志愿。"
> —— 出处: 《热点问答①|天津高考生志愿填报之整体安排》
> URL: http://www.zhaokao.net/gkck/system/2026/06/16/030009834.shtml
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
TIANJIN.collection_count:
  severity: warning
  value:
    collection_count: 2
  effective_date: '2026-01-01'
  source_evidence_id: tianjin-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：天津全市总口径是 `四次征询`，但其中普通类 `本科批` 只对应 `A阶段` 与 `B阶段` 各一次，因此当前字段应取 `2`
- 例 2：艺体本科、提前本科和高职（专科）的征询不应混入普通本科批主规则计数

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 天津教育招生考试院
- 复核负责人: 待指派
