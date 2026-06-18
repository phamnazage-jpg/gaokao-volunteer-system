# anhui-2026-max_majors_per_group

> 对应规则: `ANHUI.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通本科批次，实行平行志愿，设置45个院校专业组志愿，每个院校专业组设6个专业志愿及专业服从志愿。"
> —— 出处: 《关于做好2026年普通高校招生工作的通知》
> URL: https://www.ahzsks.cn/ptgxzs/8884.htm
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
ANHUI.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: anhui-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：`6` 描述的是单个院校专业组内的专业志愿数量上限，不是整个本科批的可选专业总数
- 例 2：个别提前批类型若需要超过 6 个专业，官方要求通过重复填报同一院校专业组等特殊方式处理，不适用于普通本科批主规则

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 安徽省教育招生考试院
- 复核负责人: 待指派
