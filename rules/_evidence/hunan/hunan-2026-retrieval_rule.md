# hunan-2026-retrieval_rule

> 对应规则: `HUNAN.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-17
> 摘录人: Hermes Agent (主代理)

## 1. 官方原文摘录

> "湖南省普通高校招生实行'分数优先、遵循志愿、一次投档'的平行志愿投档原则。"
> —— 出处: 《湖南省 2026 年普通高校招生工作实施办法》第三章"投档与录取"

## 2. 转写为机读规则

```yaml
HUNAN.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: 2026-01-01
  source_evidence_id: hunan-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：本科批 / 专科批按院校专业组平行投档
- 例 2：本科提前批部分特殊类型（军事、公安等）按顺序志愿投档，不适用本规则

## 4. 后续维护

- 下次复核时间: 2026-09-01
- 复核来源: 湖南省教育考试院
- 复核负责人: 待指派
