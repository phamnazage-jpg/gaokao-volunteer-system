# xizang-2026-max_volunteers

> 对应规则: `XIZANG.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "除全国计划自主批次外，我区其他批次均实行平行志愿投档模式，每个批次设置 A、B、C、D、E、F、G、H、I、J 共 10 个并列的院校志愿。"
> —— 出处: 《西藏自治区2026年普通高等学校招生规定》
> URL: http://zsks.edu.xizang.gov.cn/71/74/7787.html
> 发布日期: 2026-05-29

## 2. 转写为机读规则

```yaml
XIZANG.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 10
  effective_date: '2026-01-01'
  source_evidence_id: xizang-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：西藏普通高考主体批次是 `10` 个并列院校志愿，不是旧 truth 常见的 `6` 或 `9`
- 例 2：这里记录的是除全国计划自主批次外的普通批次共性规则，因此可作为西藏省级主规则的志愿上限

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 西藏教育考试院
- 复核负责人: 待指派
