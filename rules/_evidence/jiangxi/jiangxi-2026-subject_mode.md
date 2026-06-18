# jiangxi-2026-subject_mode

> 对应规则: `JIANGXI.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "答：“3+1+2”的模式和传统的文理分科有着本质上的区别。"
>
> "首选科目历史、物理以卷面原始分直接计入考生总成绩，再选科目思想政治、地理、化学、生物学以等级转换分计入考生总成绩。"
> —— 出处: 《10.普通高考实施“3+1+2”模式和传统的文理分科有何区别？》 / 《7.普通高考考生文化总成绩是如何组成的？》
> URL: http://www.jxeea.cn/jxsjyksy/gkzhggw5049/content/content_1856054454090403840.html
> URL: http://www.jxeea.cn/jxsjyksy/gkzhggw5049/content/content_1856054497186877440.html
> 发布日期: 2023-09-14 / 2023-09-14

## 2. 转写为机读规则

```yaml
JIANGXI.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: jiangxi-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：江西新高考选科结构已经明确是 `3+1+2`，不能再按传统文理分科处理
- 例 2：证据层同时保留了 `首选科目 / 再选科目` 的官方表述，避免把 `3+1+2` 简化成无语义的数字标签

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 江西
- 复核负责人: 待指派
