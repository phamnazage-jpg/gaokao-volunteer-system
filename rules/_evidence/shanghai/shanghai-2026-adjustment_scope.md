# shanghai-2026-adjustment_scope

> 对应规则: `SHANGHAI.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业调剂录取只能在考生被投档的院校专业组内进行。"
> —— 出处: 《上海市2025年普通高等学校招生志愿填报与投档录取实施办法》
> URL: https://www.shmeea.edu.cn/page/06300/20250425/19280.html
> 发布日期: 2025-04-25

## 2. 转写为机读规则

```yaml
SHANGHAI.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: shanghai-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：官方把调剂范围明确限制在“被投档的院校专业组内”，因此 `adjustment_scope=组内专业`
- 例 2：上海不会因为服从调剂而把考生调到其他院校专业组，这一点和旧“院校内跨专业大类调剂”口径不同

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 上海市教育考试院
- 复核负责人: 待指派
