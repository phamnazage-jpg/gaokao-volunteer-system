# gansu-2026-has_adjustment

> 对应规则: `GANSU.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类本科批：实行平行志愿投档，每个院校专业组志愿设置45个院校专业组志愿，每个院校专业组志愿设置6个专业选项和1个服从专业调剂选项。未完成招生计划实施2次征集志愿。"
> —— 出处: 《关于做好2026年甘肃省普通高校招生工作的通知》
> URL: https://www.ganseea.cn/gaokaogaozhao/1884.html
> 发布日期: 2026-05-20

## 2. 转写为机读规则

```yaml
GANSU.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: gansu-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：官方已明确存在 `1个服从专业调剂选项`，因此 `has_adjustment` 不能继续保守写成 `false`
- 例 2：该字段只表达“是否允许调剂”，不单独承诺调剂到院校外或专业组外

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 甘肃省教育考试院
- 复核负责人: 待指派
