# hainan-2026-collection_count

> 对应规则: `HAINAN.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科普通批进行平行志愿投档后，根据录取情况，组织二轮征集志愿；其他每批平行志愿和征集志愿的投档一般只进行一轮，一轮投档后再根据各院校完成计划情况决定是否继续征集志愿。"
> —— 出处: 《2026年海南省普通高校招生实施办法》
> URL: http://ea.hainan.gov.cn/ywdt/ptgkyjszsb/202605/t20260528_4083583.html
> 发布日期: 2026-05-28

## 2. 转写为机读规则

```yaml
HAINAN.collection_count:
  severity: warning
  value:
    collection_count: 2
  effective_date: '2026-01-01'
  source_evidence_id: hainan-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：旧 truth 写成 `1` 与 2026 官方“本科普通批…组织二轮征集志愿”直接冲突，本次已修正为 `2`
- 例 2：同句也明确“其他每批…一般只进行一轮”，因此该值只对应海南本科普通批主流程，不外推为全省全部批次统一两轮

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 海南省考试局
- 复核负责人: 待指派
