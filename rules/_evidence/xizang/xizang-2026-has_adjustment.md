# xizang-2026-has_adjustment

> 对应规则: `XIZANG.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校设置 4 个专业志愿和专业服从调剂志愿，不设院校服从调剂志愿。"
> —— 出处: 《西藏自治区2026年普通高等学校招生规定》
> URL: http://zsks.edu.xizang.gov.cn/71/74/7787.html
> 发布日期: 2026-05-29

## 2. 转写为机读规则

```yaml
XIZANG.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: xizang-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：西藏普通高考主体批次明确存在“专业服从调剂志愿”，因此 `has_adjustment` 必须为 `true`
- 例 2：官方同时明确“不设院校服从调剂志愿”，说明允许的是专业调剂，不是院校调剂

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 西藏教育考试院
- 复核负责人: 待指派
