# guangxi-2026-max_volunteers

> 对应规则: `GUANGXI.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "2.本科普通批。安排除本科提前批、其他预科批之外的其他本科专业。按首选科目实行平行志愿模式，设置40个院校专业组志愿。"
> —— 出处: 《自治区教育厅关于印发〈广西2026年普通高校招生考试和录取工作方案〉的通知》
> URL: https://www.gxeea.cn/view/content_1013_32810.htm
> 发布日期: 2026-06-03

## 2. 转写为机读规则

```yaml
GUANGXI.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 40
  effective_date: '2026-01-01'
  source_evidence_id: guangxi-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：广西普通类本科普通批官方明确是 `40` 个院校专业组志愿，不是 45 或 50
- 例 2：高职高专普通批也是 `40` 个院校专业组志愿，但本规则只记录本科主批次

## 4. 后续维护

- 下次复核时间: 2026-07-10
- 复核来源: 广西招生考试院
- 复核负责人: 待指派
