# qinghai-2026-max_volunteers

> 对应规则: `QINGHAI.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "（二）本科批次。设置⑦段。包含计划类型和志愿数分别为：除本科提前批次外的其他本科招生专业及计划……填报96个专业（类）平行志愿。"
> —— 出处: 《青海省2026年普通高等学校招生录取工作实施细则》
> URL: https://www.qhjyks.com/ztzl/ptgkz/5807.htm
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
QINGHAI.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 96
  effective_date: '2026-01-01'
  source_evidence_id: qinghai-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：青海普通类本科批是 `96` 个专业（类）平行志愿，不是旧高考常见的 6 个或 9 个院校志愿
- 例 2：这里的 `96` 适用于普通类本科批主体规则，不应与提前批各段的 `60` 个平行志愿混算

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 青海省教育考试网
- 复核负责人: 待指派
