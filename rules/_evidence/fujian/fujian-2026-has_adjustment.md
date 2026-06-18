# fujian-2026-has_adjustment

> 对应规则: `FUJIAN.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿均设6个专业志愿和是否服从专业调剂栏目。"
> —— 出处: 《2026年福建省普通高等学校招生录取实施办法》
> URL: http://www.eeafj.cn/gkptgkgsgg/20260612/14670.html
> 发布日期: 2026-06-11 / 2026-06-12 发布

## 2. 转写为机读规则

```yaml
FUJIAN.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: fujian-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：福建本科批院校专业组志愿明确带“是否服从专业调剂栏目”，因此 `has_adjustment=true`
- 例 2：调剂属于考生填报时显式选择项，不代表招生院校可在未勾选的情况下自动调剂

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 福建省教育考试院
- 复核负责人: 待指派
