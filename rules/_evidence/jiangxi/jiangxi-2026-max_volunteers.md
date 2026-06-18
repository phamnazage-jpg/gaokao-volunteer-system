# jiangxi-2026-max_volunteers

> 对应规则: `JIANGXI.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "（2）本科批次。设特殊选拔单志愿和平行志愿2个志愿栏，特殊选拔单志愿栏设1个“院校专业组”，平行志愿栏设45个“院校专业组”。"
>
> "（4）高职（专科）批次。设平行志愿，45个“院校专业组”。"
> —— 出处: 《十七、普通类（历史、物理科目组）志愿如何设置？》
> URL: http://www.jxeea.cn/jxsjyksy/cjwd22/content/content_1856071499628613632.html
> 发布日期: 2024-06-21

## 2. 转写为机读规则

```yaml
JIANGXI.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 45
  effective_date: '2026-01-01'
  source_evidence_id: jiangxi-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：江西普通类本科批平行志愿栏已明确是 `45` 个院校专业组志愿，旧值若小于 45 会直接低估用户可填报上限
- 例 2：提前本科批次中的单志愿栏和特殊选拔单志愿栏都是单独志愿位，不应误读成普通本科批上限

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 江西
- 复核负责人: 待指派
