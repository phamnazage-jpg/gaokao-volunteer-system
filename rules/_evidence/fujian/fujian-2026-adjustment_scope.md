# fujian-2026-adjustment_scope

> 对应规则: `FUJIAN.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "常规志愿为院校专业组志愿，每个院校专业组志愿设6个专业志愿和是否服从专业调剂栏目。"
>
> "每个院校专业组志愿均设6个专业志愿和是否服从专业调剂栏目。"
> —— 出处: 《2026年福建省普通高等学校招生录取实施办法》
> URL: http://www.eeafj.cn/gkptgkgsgg/20260612/14670.html
> 发布日期: 2026-06-11 / 2026-06-12 发布

## 2. 转写为机读规则

```yaml
FUJIAN.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: fujian-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：福建官方虽然没有直接写出“组内专业调剂”，但调剂栏目被绑定在单个“院校专业组志愿”上，truth 据此归一化为 `组内专业`
- 例 2：本条不支持跨院校专业组调剂，避免把“是否服从专业调剂栏目”误读成全校任意专业调剂

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 福建省教育考试院
- 复核负责人: 待指派
