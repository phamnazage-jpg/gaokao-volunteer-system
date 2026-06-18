# guangdong-2026-mode

> 对应规则: `GUANGDONG.mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "我省高考志愿填报实行院校专业组模式，采取网上填报的方式。"
> "考生须在认真阅读高校招生章程和我省招生工作规定后，选择报考高校、院校专业组及组内专业志愿。"
> —— 出处: 《广东省普通高等学校招生工作规定》
> URL: https://eea.gd.gov.cn/tzgg/content/post_4896626.html / https://eea.gd.gov.cn/attachment/0/613/613821/4896626.pdf
> 发布日期: 2026-05-13

## 2. 转写为机读规则

```yaml
GUANGDONG.mode:
  severity: fatal
  value:
    mode: 院校专业组
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-mode
  status: active
```

## 3. 关键边界与例外

- 例 1：广东 2026 普通高考明确采用 `院校专业组` 作为志愿单位，不能再按“学校+专业”旧模式理解
- 例 2：同一院校可拆分多个院校专业组，但不改变 `mode` 的机读值

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
