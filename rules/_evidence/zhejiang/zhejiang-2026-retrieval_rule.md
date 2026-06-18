# zhejiang-2026-retrieval_rule

> 对应规则: `ZHEJIANG.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "以一所院校的一个专业（类）为志愿单位，按照“分数优先、遵循志愿”进行投档。"
> —— 出处: 《浙江省2026年高考招生志愿填报百问百答》
> URL: https://www.zjzs.net/art/2026/6/17/art_45_12386.html
> 发布日期: 2026-06-17
>
> "每一段专业平行志愿均实行一轮投档，考生只有一次投档机会，一旦被投档到其中一个专业志愿，其余专业志愿即失效。"
> —— 出处: 《浙江省2026年高考招生志愿填报百问百答》
> URL: https://www.zjzs.net/art/2026/6/17/art_45_12386.html
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
ZHEJIANG.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: zhejiang-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：浙江普通类平行录取的检索顺序是“分数优先、遵循志愿”，并非先按院校志愿排序
- 例 2：每段只投 1 轮且只给 1 次投档机会，因此当前 truth 将规则概括为 `分数优先、遵循志愿、一次投档`

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 浙江省教育考试院
- 复核负责人: 待指派
