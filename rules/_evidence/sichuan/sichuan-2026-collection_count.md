# sichuan-2026-collection_count

> 对应规则: `SICHUAN.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "未完成的招生计划向符合条件的考生公开征集志愿，征集志愿的填报办法根据录取实际情况另文通知。"
>
> "经征集志愿后，若仍有高校完不成计划，经省招考委研究，确需降分的，可在相应批次录取控制分数线下适当降分。"
> —— 出处: 《四川省2026年普通高校招生实施规定》
> URL: http://www.sceea.cn/Html/202604/Newsdetail_4767.html
> 发布日期: 2026-04-21 / 2026-04-23 发布

## 2. 转写为机读规则

```yaml
SICHUAN.collection_count:
  severity: warning
  value:
    collection_count: null
    collection_arrangement: 根据录取实际情况公开征集志愿
    collection_timing: 征集志愿填报办法另文通知
  effective_date: '2026-01-01'
  source_evidence_id: sichuan-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：四川官方没有承诺固定征集轮次，只明确“根据录取实际情况另文通知”，因此继续写死 `1` 不可靠，改为 `collection_count: null`
- 例 2：同页还明确征集后仍可能降分补充生源，所以项目层需保留动态安排信息，而不是伪造一个稳定整数

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 四川省教育考试院
- 复核负责人: 待指派
