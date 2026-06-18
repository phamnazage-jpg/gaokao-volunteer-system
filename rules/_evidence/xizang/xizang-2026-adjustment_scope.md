# xizang-2026-adjustment_scope

> 对应规则: `XIZANG.adjustment_scope`
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
XIZANG.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 全部专业
  effective_date: '2026-01-01'
  source_evidence_id: xizang-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：西藏只设置“专业服从调剂志愿”，不设置院校服从调剂，因此项目层继续归一为 `全部专业`
- 例 2：这里的 `全部专业` 指当前院校内可调剂专业范围，不是跨院校调剂

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 西藏教育考试院
- 复核负责人: 待指派
