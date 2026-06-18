# hainan-2026-mode

> 对应规则: `HAINAN.mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "院校专业组是志愿填报与投档录取的基本单位。"
> —— 出处: 《2026年海南省普通高校招生实施办法》
> URL: http://ea.hainan.gov.cn/ywdt/ptgkyjszsb/202605/t20260528_4083583.html
> 发布日期: 2026-05-28

## 2. 转写为机读规则

```yaml
HAINAN.mode:
  severity: fatal
  value:
    mode: 院校专业组
  effective_date: '2026-01-01'
  source_evidence_id: hainan-2026-mode
  status: active
```

## 3. 关键边界与例外

- 例 1：海南 2026 普通高考已明确以 `院校专业组` 作为填报与投档基本单元，truth 不再沿用旧的“院校”或“专业+学校”表述
- 例 2：这里记录的是本科普通批主流程的志愿单元，不展开到提前批、专科批等其他批次差异

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 海南省考试局
- 复核负责人: 待指派
