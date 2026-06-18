# guizhou-2026-max_volunteers

> 对应规则: `GUIZHOU.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "2.本科批。除本科提前批以外的其他本科招生专业（含预科、民族班、国家专项计划和地方专项计划），设置96个专业（类）平行志愿。"
> —— 出处: 《贵州省2025年高考填报志愿规定》
> URL: http://zsksy.guizhou.gov.cn/ptgk/qtxx/202506/t20250625_88190180.html
> 发布日期: 2025-06-25

## 2. 转写为机读规则

```yaml
GUIZHOU.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 96
  effective_date: '2026-01-01'
  source_evidence_id: guizhou-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：这里的 `96` 对应普通类本科批的专业（类）平行志愿数量，不包含本科提前批 A/B 段的单院校顺序志愿
- 例 2：高职（专科）批同样也是 `96`，但项目层以本科批主流程做省级归一，不应混淆不同批次的准入条件

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 贵州省招生考试院
- 复核负责人: 待指派
