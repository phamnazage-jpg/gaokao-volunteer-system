# tianjin-2026-max_volunteers

> 对应规则: `TIANJIN.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通本科批次A阶段……其他院校，平行志愿，50个院校专业组。"
>
> "普通本科批次B阶段……平行志愿，25个院校专业组。"
> —— 出处: 《热点问答①|天津高考生志愿填报之整体安排》
> URL: http://www.zhaokao.net/gkck/system/2026/06/16/030009834.shtml
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
TIANJIN.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 50
  effective_date: '2026-01-01'
  source_evidence_id: tianjin-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：当前省级主规则锚定普通类 `本科批A阶段` 的主填报面，因此 `max_volunteers` 继续取 `50`
- 例 2：本科批 `B阶段` 仅有 `25个院校专业组`，不能把 A/B 两阶段简单相加

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 天津教育招生考试院
- 复核负责人: 待指派
