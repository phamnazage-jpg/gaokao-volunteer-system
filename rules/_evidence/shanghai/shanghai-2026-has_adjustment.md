# shanghai-2026-has_adjustment

> 对应规则: `SHANGHAI.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生在每个院校专业组志愿中均须选择愿否服从专业志愿调剂。"
> —— 出处: 《上海市2025年普通高等学校招生志愿填报与投档录取实施办法》
> URL: https://www.shmeea.edu.cn/page/06300/20250425/19280.html
> 发布日期: 2025-04-25

## 2. 转写为机读规则

```yaml
SHANGHAI.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: shanghai-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：既然每个院校专业组都要求选择“愿否服从专业志愿调剂”，则上海本科普通批存在调剂机制，`has_adjustment=true`
- 例 2：官方要求是逐个院校专业组选择，而不是全局一次性选择

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 上海市教育考试院
- 复核负责人: 待指派
