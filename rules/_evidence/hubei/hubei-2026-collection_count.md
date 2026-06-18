# hubei-2026-collection_count

> 对应规则: `HUBEI.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科普通批（第一次） 7月27日8:00—7月28日12:00"
> "本科普通批（第二次） 8月1日8:00—17:00"
> "考生须在规定时间内参加模拟志愿填报、集中填报志愿和征集志愿。"
> —— 出处: 《2022年普通高校招生什么时候征集志愿？》 / 《湖北省2026年普通高校招生网上填报志愿时间安排》
> URL: https://www.hbksw.com/info/41/1026.html / https://www.hbksw.com/info/6/2270.html
> 发布日期: 页面未标注（阳光招生问答公开页） / 2026-06-11

## 2. 转写为机读规则

```yaml
HUBEI.collection_count:
  severity: warning
  value:
    collection_count: 2
  effective_date: '2026-01-01'
  source_evidence_id: hubei-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：当前 `collection_count: 2` 对应的是湖北普通类本科普通批主流程；2022 官方问答明确存在本科普通批第一次和第二次征集志愿
- 例 2：并非所有批次都固定两次，同页可见部分批次只有一次征集；因此该值不应外推为“湖北所有批次统一两次”

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 湖北招生考试网 / 湖北省教育考试院
- 复核负责人: 待指派
