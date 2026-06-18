# hainan-2026-max_volunteers

> 对应规则: `HAINAN.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科普通部分的本科普通批（含本科少数民族班）设30个院校专业组志愿；本科预科班设6个院校专业组志愿，每个院校专业组内设6个专业志愿和服从专业调剂志愿。"
> —— 出处: 《2026年海南省普通高校招生实施办法》
> URL: http://ea.hainan.gov.cn/ywdt/ptgkyjszsb/202605/t20260528_4083583.html
> 发布日期: 2026-05-28

## 2. 转写为机读规则

```yaml
HAINAN.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 30
  effective_date: '2026-01-01'
  source_evidence_id: hainan-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：旧 truth 写成 `24` 与 2026 官方“本科普通批（含本科少数民族班）设30个院校专业组志愿”直接冲突，本次已修正为 `30`
- 例 2：同段还给出了本科预科班 `6` 个院校专业组志愿，因此这里的 `30` 只对应本科普通批主流程，不外推到预科班

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 海南省考试局
- 复核负责人: 待指派
