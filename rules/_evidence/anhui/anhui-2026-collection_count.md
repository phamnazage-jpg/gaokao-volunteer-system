# anhui-2026-collection_count

> 对应规则: `ANHUI.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "安徽省2026年普通高校招生各科类各批次志愿（含录取期间征集志愿）均通过网络分时段填报。各批次志愿填报时间段如下。"
> "普通本科批 7月31日10:00至16:00。"
> —— 出处: 《手把手教你填志愿（一）——带你读懂我省2026年高考考生志愿网上填报办法》正文及配图《征集志愿填报时间表》
> URL: https://www.ahzsks.cn/ptgxzs/8931.htm / https://www.ahzsks.cn/pic/image/20260612/20260612093346_537.png
> 发布日期: 2026-06-11 / 2026-06-12

## 2. 转写为机读规则

```yaml
ANHUI.collection_count:
  severity: warning
  value:
    collection_count: 1
  effective_date: '2026-01-01'
  source_evidence_id: anhui-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：按安徽考试院当前公布的 2026 `征集志愿填报时间表`，普通本科批只出现 1 个正式征集时段，因此旧值 `2` 不成立
- 例 2：正文同时说明征集志愿时间如受录取进度影响可调整；若后续另发公告新增本科批征集轮次，应重新复核并更新本条

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 安徽省教育招生考试院
- 复核负责人: 待指派
