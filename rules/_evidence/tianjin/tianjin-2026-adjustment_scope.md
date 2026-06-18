# tianjin-2026-adjustment_scope

> 对应规则: `TIANJIN.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类本科院校以“院校专业组”为单位进行招生录取。"
>
> "普通本科批次A阶段……每个院校专业组设置6个专业志愿和1个服从调剂专业志愿。"
> —— 出处: 《2026年天津市普通高校招生工作规定》 / 《热点问答①|天津高考生志愿填报之整体安排》
> URL: http://www.zhaokao.net/zwgk/doc/003/000/114/00300011419_edf58f9e.pdf / http://www.zhaokao.net/gkck/system/2026/06/16/030009834.shtml
> 发布日期: 2026-04-29 / 2026-06-17

## 2. 转写为机读规则

```yaml
TIANJIN.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: tianjin-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：天津普通类本科是按 `院校专业组` 作为录取单位，服从调剂自然限定在组内专业，不能扩展为跨组或跨校
- 例 2：项目将这一口径归一为 `组内专业`，便于与其他院校专业组省份保持一致

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 天津教育招生考试院
- 复核负责人: 待指派
