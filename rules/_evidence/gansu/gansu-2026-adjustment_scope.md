# gansu-2026-adjustment_scope

> 对应规则: `GANSU.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "院校招生计划可设置一个或多个院校专业组，每个院校专业组内可包含数量不等的专业。"
>
> "普通类本科批：实行平行志愿投档，每个院校专业组志愿设置45个院校专业组志愿，每个院校专业组志愿设置6个专业选项和1个服从专业调剂选项。未完成招生计划实施2次征集志愿。"
> —— 出处: 《关于做好2026年甘肃省普通高校招生工作的通知》
> URL: https://www.ganseea.cn/gaokaogaozhao/1884.html
> 发布日期: 2026-05-20

## 2. 转写为机读规则

```yaml
GANSU.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: gansu-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：甘肃原文没有直接写出“组内专业调剂”四个字，但调剂选项绑定在单个院校专业组志愿内，因此项目层归一化为 `组内专业`
- 例 2：不能把该调剂范围误读为全校任意专业，否则会高估考生被调剂的实际边界

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 甘肃省教育考试院
- 复核负责人: 待指派
