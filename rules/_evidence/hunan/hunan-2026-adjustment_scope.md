# hunan-2026-adjustment_scope

> 对应规则: `HUNAN.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-17
> 摘录人: Hermes Agent (主代理)

## 1. 官方原文摘录

> "考生所填专业志愿不能满足，且服从专业调剂时，仅在所填报的院校专业组内的未录满专业中进行调剂录取。"
> —— 出处: 《湖南省 2026 年普通高校招生工作实施办法》第二章"志愿设置"

## 2. 转写为机读规则

```yaml
HUNAN.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: 2026-01-01
  source_evidence_id: hunan-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：调剂严格限定在本院校专业组内的 6 个专业 + 同组其他可选专业
- 例 2：不向其他院校专业组调剂（这是与老高考"院校调剂"的核心区别）

## 4. 后续维护

- 下次复核时间: 2026-09-01
- 复核来源: 湖南省教育考试院
- 复核负责人: 待指派
