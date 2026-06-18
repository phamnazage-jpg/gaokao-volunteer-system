# yunnan-2026-retrieval_rule

> 对应规则: `YUNNAN.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "按照“分数优先、遵循志愿”的原则进行投档。"
>
> "根据考生成绩、志愿顺序和院校专业组招生计划，原则上按照线上生源数和招生计划数1:1的比例，从高分到低分投档给高校。"
> —— 出处: 《云南省2025年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.ynzs.cn/html/content/7511.html
> 发布日期: 2025-01-23

## 2. 转写为机读规则

```yaml
YUNNAN.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿
  effective_date: '2026-01-01'
  source_evidence_id: yunnan-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：云南普通类多志愿批次已经按官方口径切到 `分数优先、遵循志愿` 的平行志愿投档规则，旧规则不能再按传统顺序志愿理解
- 例 2：设置 `1` 个院校专业组志愿的批次适用单志愿投档规则，但本科批主体规则仍以平行志愿为主

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 云南省招生考试院
- 复核负责人: 待指派
