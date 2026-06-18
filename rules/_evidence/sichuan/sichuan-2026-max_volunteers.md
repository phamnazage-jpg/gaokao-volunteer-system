# sichuan-2026-max_volunteers

> 对应规则: `SICHUAN.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科批次B段为本科提前批次及本科批次A段以外的本科招生高校（专业）……实行平行志愿，设置45个院校专业组志愿，每个院校专业组志愿内设置6个专业志愿和是否服从专业调剂选项。"
> —— 出处: 《四川省2026年普通高校招生实施规定》
> URL: http://www.sceea.cn/Html/202604/Newsdetail_4767.html
> 发布日期: 2026-04-21 / 2026-04-23 发布

## 2. 转写为机读规则

```yaml
SICHUAN.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 45
  effective_date: '2026-01-01'
  source_evidence_id: sichuan-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：旧 truth 写成 `9` 与 2026 官方“本科批次B段…设置45个院校专业组志愿”直接冲突，本次已修正为 `45`
- 例 2：四川本科批还含 A 段的专项计划与高水平运动队等特殊子流程，因此这里的 `45` 仅对应普通本科主流程 B 段，不外推到所有本科子段

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 四川省教育考试院
- 复核负责人: 待指派
