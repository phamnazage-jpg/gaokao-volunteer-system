# zhejiang-2026-max_volunteers

> 对应规则: `ZHEJIANG.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生每次可填报不超过80个志愿。"
> —— 出处: 《浙江2026年高考招生工作通知发布》
> URL: https://www.zjzs.net/art/2026/5/20/art_30_12294.html
> 发布日期: 2026-05-20
>
> "专业平行志愿分两段填报志愿，每段均可填报不超过80个志愿。"
> —— 出处: 《浙江省教育考试院关于做好2026年普通高校招生网上填报志愿工作的通知》
> URL: https://www.zjzs.net/art/2026/6/13/art_156_12376.html
> 发布日期: 2026-06-05

## 2. 转写为机读规则

```yaml
ZHEJIANG.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 80
  effective_date: '2026-01-01'
  source_evidence_id: zhejiang-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：浙江普通类平行志愿按段填报，每一段都允许最多 80 个志愿，因此规则值应是单轮上限 `80`
- 例 2：两段填报不意味着一次能提交 160 个志愿；每次实际提交仍受“每段不超过 80 个”约束

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 浙江省教育考试院
- 复核负责人: 待指派
