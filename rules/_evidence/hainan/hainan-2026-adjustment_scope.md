# hainan-2026-adjustment_scope

> 对应规则: `HAINAN.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "在填报志愿时，考生须表明所填报的院校专业组未按本人所选报的专业志愿录取时是否愿意服从该校录取到该院校专业组的其他专业，服从者按填报志愿系统的要求进行相应的操作。"
> —— 出处: 《2026年海南省普通高校招生实施办法》
> URL: http://ea.hainan.gov.cn/ywdt/ptgkyjszsb/202605/t20260528_4083583.html
> 发布日期: 2026-05-28

## 2. 转写为机读规则

```yaml
HAINAN.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: hainan-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：官方原文已把调剂范围限定为“该院校专业组的其他专业”，因此 truth 归一化为 `组内专业`
- 例 2：本条不支持跨学校或跨院校专业组调剂，避免把“服从调剂”误读为全校任意专业调剂

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 海南省考试局
- 复核负责人: 待指派
