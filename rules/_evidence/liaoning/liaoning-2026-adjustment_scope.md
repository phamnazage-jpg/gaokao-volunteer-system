# liaoning-2026-adjustment_scope

> 对应规则: `LIAONING.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "“专业+学校”模式取消了专业调剂，考生不必担心被调剂到不喜欢的专业了，考生也因此不会存在“因不服从专业调剂而退档”的情况。"
>
> "专业平行志愿投档时，直接投档到某院校某专业，不存在专业服从调剂。"
> —— 出处: 《辽宁省2024年普通高校招生志愿填报及招生录取问答》
> URL: https://www.lnzsks.com/newsinfo/IMS_20240619_44007_hZ6qDmgcpv.htm
> 发布日期: 2024-06-19

## 2. 转写为机读规则

```yaml
LIAONING.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 无
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁普通类本科批采用 `专业+学校` 单志愿直投，官方明确“不存在专业服从调剂”，因此 `adjustment_scope` 应记为 `无`
- 例 2：这里描述的是普通类本科批规则，不外推到普通类本科提前批。提前批仍按院校志愿设置专业志愿与专业服从

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
