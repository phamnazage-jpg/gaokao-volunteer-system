# chongqing-2026-max_majors_per_group

> 对应规则: `CHONGQING.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业平行志愿以‘1个专业（类）+1个学校’为1个志愿。"
> —— 出处: 《录取批次及志愿设置》
> URL: https://www.cqksy.cn/web/article/2025-06/17/content_6631.html
> 发布日期: 2025-06-17

## 2. 转写为机读规则

```yaml
CHONGQING.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 1
  effective_date: '2026-01-01'
  source_evidence_id: chongqing-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：专业平行志愿的最小填报单位就是 `1个专业（类）+1个学校`，因此 `max_majors_per_group` 应为 `1`
- 例 2：`1个学校+6个专业（类）` 属于院校顺序志愿，不适用于普通类 `本科批`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 重庆市教育考试院
- 复核负责人: 待指派
