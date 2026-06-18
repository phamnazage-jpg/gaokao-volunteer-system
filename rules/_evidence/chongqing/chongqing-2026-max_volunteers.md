# chongqing-2026-max_volunteers

> 对应规则: `CHONGQING.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "2.本科批……设置96个专业平行志愿。"
> —— 出处: 《录取批次及志愿设置》
> URL: https://www.cqksy.cn/web/article/2025-06/17/content_6631.html
> 发布日期: 2025-06-17

## 2. 转写为机读规则

```yaml
CHONGQING.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 96
  effective_date: '2026-01-01'
  source_evidence_id: chongqing-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：重庆普通类 `本科批` 官方明确为 `96` 个专业平行志愿，不是 `45` 或其他院校专业组口径
- 例 2：该上限对应普通类 `本科批`，不外推到提前批、专科批或高职分类考试

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 重庆市教育考试院
- 复核负责人: 待指派
