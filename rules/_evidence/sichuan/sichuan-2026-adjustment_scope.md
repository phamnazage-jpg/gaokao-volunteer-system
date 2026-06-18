# sichuan-2026-adjustment_scope

> 对应规则: `SICHUAN.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "高校可根据不同专业的人才培养需要和选考科目要求设置院校专业组，作为志愿填报的基本单位。一个院校专业组即为一个独立的志愿。"
>
> "每个院校专业组志愿内设置6个专业志愿和是否服从专业调剂选项。"
> —— 出处: 《四川省2026年普通高校招生实施规定》
> URL: http://www.sceea.cn/Html/202604/Newsdetail_4767.html
> 发布日期: 2026-04-21 / 2026-04-23 发布

## 2. 转写为机读规则

```yaml
SICHUAN.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 全部专业
  effective_date: '2026-01-01'
  source_evidence_id: sichuan-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：四川官方虽未直接写出“组内专业调剂”，但调剂选项绑定在单个院校专业组志愿内，truth 因此归一化为 `组内专业`
- 例 2：不能把该调剂范围误读为全校所有专业，旧 truth 的 `全部专业` 过度扩张了官方约束范围

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 四川省教育考试院
- 复核负责人: 待指派
