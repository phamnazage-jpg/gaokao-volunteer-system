# hubei-2026-adjustment_scope

> 对应规则: `HUBEI.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生填报了一个院校专业组内的多个专业志愿，且服从专业调剂，投档到该院校专业组后，就只能在这个院校专业组所包含的专业中进行调剂，不能跨院校专业组调剂专业。"
> —— 出处: 《填报的院校专业组中，对选择了“服从专业调剂”的考生如何调剂录取？》
> URL: https://www.hbksw.com/info/41/1053.html
> 发布日期: 页面未标注（湖北省普通高校招生阳光招生问答公开页）

## 2. 转写为机读规则

```yaml
HUBEI.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: hubei-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：湖北调剂是严格的组内专业调剂，不能跨院校专业组调剂专业
- 例 2：即使同一高校还有其他院校专业组空位，只要不在当前投档组内，也不能转移过去

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 湖北招生考试网 / 湖北省教育考试院
- 复核负责人: 待指派
