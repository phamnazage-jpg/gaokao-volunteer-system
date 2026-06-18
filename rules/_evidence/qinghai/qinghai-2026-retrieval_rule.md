# qinghai-2026-retrieval_rule

> 对应规则: `QINGHAI.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业（类）平行志愿，依据“分数优先、遵循志愿、一轮投档”的原则投档。"
> —— 出处: 《青海省2026年普通高等学校招生录取工作实施细则》
> URL: https://www.qhjyks.com/ztzl/ptgkz/5807.htm
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
QINGHAI.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: qinghai-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：官方原文写法是 `一轮投档`，项目层沿用既有归一化词表，记为 `一次投档`
- 例 2：青海顺序志愿段采用的是 `志愿优先、遵循分数`，这里必须锚定专业（类）平行志愿主流程，不能混用

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 青海省教育考试网
- 复核负责人: 待指派
