# yunnan-2026-adjustment_scope

> 对应规则: `YUNNAN.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业调剂录取只能在考生被投档的院校专业组内进行。"
> —— 出处: 《云南省2025年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.ynzs.cn/html/content/7511.html
> 发布日期: 2025-01-23

## 2. 转写为机读规则

```yaml
YUNNAN.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: yunnan-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：云南调剂范围被官方明确限制在 `院校专业组内`，旧的 `全部专业` 会越过选科与组别边界
- 例 2：即使同一院校设置多个专业组，调剂也不能跨组进行

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 云南省招生考试院
- 复核负责人: 待指派
