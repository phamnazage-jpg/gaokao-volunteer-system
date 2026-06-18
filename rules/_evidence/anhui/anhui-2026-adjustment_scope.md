# anhui-2026-adjustment_scope

> 对应规则: `ANHUI.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "选择“服从”：录取时，当自己填报的专业志愿均无法满足时，可调剂录取到该院校专业组内有缺额且符合录取要求的专业。"
> —— 出处: 《手把手教你填志愿（三）——志愿填报辅助系统使用说明》
> URL: https://www.ahzsks.cn/ptgxzs/8939.htm
> 发布日期: 2026-06-14

## 2. 转写为机读规则

```yaml
ANHUI.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: anhui-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：安徽官方把调剂范围明确限定在 `该院校专业组内`，因此不能扩写成“全校任意专业调剂”
- 例 2：即使考生勾选服从，也仍然要求目标专业 `有缺额且符合录取要求`，并不是无条件调剂

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 安徽省教育招生考试院
- 复核负责人: 待指派
