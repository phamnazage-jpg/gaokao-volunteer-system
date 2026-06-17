# hunan-2026-has_adjustment

> 对应规则: `HUNAN.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-17
> 摘录人: Hermes Agent (主代理)

## 1. 官方原文摘录

> "专业调剂志愿设在院校专业组内的 6 个专业之后，单独作为第 7 个选项，由考生选择是否服从专业调剂。"
> —— 出处: 《湖南省 2026 年普通高校招生工作实施办法》第二章"志愿设置"

## 2. 转写为机读规则

```yaml
HUNAN.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: 2026-01-01
  source_evidence_id: hunan-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：调剂范围限定在本院校专业组内（详见 hunan-2026-adjustment_scope）
- 例 2：不设"是否服从专业组调剂"（投档单位即专业组，无跨组调剂）

## 4. 后续维护

- 下次复核时间: 2026-09-01
- 复核来源: 湖南省教育考试院
- 复核负责人: 待指派
