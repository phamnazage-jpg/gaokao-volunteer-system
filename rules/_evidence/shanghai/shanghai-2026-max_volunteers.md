# shanghai-2026-max_volunteers

> 对应规则: `SHANGHAI.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科普通批次设置24个平行志愿。"
> —— 出处: 《上海市2025年普通高等学校招生志愿填报与投档录取实施办法》
> URL: https://www.shmeea.edu.cn/page/06300/20250425/19280.html
> 发布日期: 2025-04-25

## 2. 转写为机读规则

```yaml
SHANGHAI.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 24
  effective_date: '2026-01-01'
  source_evidence_id: shanghai-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：`24` 明确对应上海本科普通批次的平行志愿数量，因此 `max_volunteers=24`
- 例 2：该整数不适用于综合评价、零志愿或艺体类批次，这些批次的志愿数量由同一实施办法另行规定

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 上海市教育考试院
- 复核负责人: 待指派
