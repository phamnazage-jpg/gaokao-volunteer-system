# chongqing-2026-adjustment_scope

> 对应规则: `CHONGQING.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "院校顺序志愿以‘1个学校+6个专业（类）’为1个志愿，并设置是否服从专业调剂选项。"
> —— 出处: 《录取批次及志愿设置》
> URL: https://www.cqksy.cn/web/article/2025-06/17/content_6631.html
> 发布日期: 2025-06-17

## 2. 转写为机读规则

```yaml
CHONGQING.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 无
  effective_date: '2026-01-01'
  source_evidence_id: chongqing-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：普通类 `本科批` 属于专业平行志愿，官方未提供组内或全专业调剂入口，故当前口径为 `无`
- 例 2：院校顺序志愿虽有“是否服从专业调剂选项”，但那是另一类志愿结构，不能映射成普通类 `本科批` 的 `组内专业` 或 `全部专业`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 重庆市教育考试院
- 复核负责人: 待指派
