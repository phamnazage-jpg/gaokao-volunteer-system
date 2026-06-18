# anhui-2026-max_volunteers

> 对应规则: `ANHUI.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通本科批次，实行平行志愿，设置45个院校专业组志愿。"
> —— 出处: 《关于做好2026年普通高校招生工作的通知》
> URL: https://www.ahzsks.cn/ptgxzs/8884.htm
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
ANHUI.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 45
  effective_date: '2026-01-01'
  source_evidence_id: anhui-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：`45` 描述的是普通本科批可填报的院校专业组志愿数量上限，不是专业总数
- 例 2：提前批、专项计划、专科批等其它批次有各自的志愿上限，不能把本条误复用到所有批次

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 安徽省教育招生考试院
- 复核负责人: 待指派
