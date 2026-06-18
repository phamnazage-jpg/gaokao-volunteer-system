# fujian-2026-max_volunteers

> 对应规则: `FUJIAN.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科批设常规志愿和2次征求志愿。常规志愿设50个平行且有顺序排列的院校专业组志愿，每次征求志愿均设20个平行且有顺序排列的院校专业组志愿。"
> —— 出处: 《2026年福建省普通高等学校招生录取实施办法》
> URL: http://www.eeafj.cn/gkptgkgsgg/20260612/14670.html
> 发布日期: 2026-06-11 / 2026-06-12 发布

## 2. 转写为机读规则

```yaml
FUJIAN.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 50
  effective_date: '2026-01-01'
  source_evidence_id: fujian-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：旧 truth 写成 `40` 与 2026 官方“本科批常规志愿设50个…院校专业组志愿”直接冲突，本次已修正为 `50`
- 例 2：官方同段还给出每次征求志愿 `20` 个院校专业组志愿，因此 `50` 只对应本科批常规志愿主流程，不外推到征求志愿阶段

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 福建省教育考试院
- 复核负责人: 待指派
