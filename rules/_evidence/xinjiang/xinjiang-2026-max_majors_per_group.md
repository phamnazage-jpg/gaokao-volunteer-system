# xinjiang-2026-max_majors_per_group

> 对应规则: `XINJIANG.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "（4）本科一批次：经批准参加本批次录取的本科高校（专业）及具备高校专项计划招生资格的高校（专业）。设置一个志愿组18个平行志愿，每个志愿可填报6个专业。"
> —— 出处: 《新疆维吾尔自治区2026年普通高校招生工作规定》
> URL: http://www.xjzk.gov.cn/c/2026-05-06/495190.shtml
> 发布日期: 2026-05-06

## 2. 转写为机读规则

```yaml
XINJIANG.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: xinjiang-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：新疆普通类 `本科一批次` 每个平行志愿下都可填 `6` 个专业，不能误读成 `1` 个专业或 `5` 个专业
- 例 2：同一条官方句子同时约束志愿数和专业数，因此这里与 `max_volunteers` 共同引用主规定正文

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 新疆教育考试院
- 复核负责人: 待指派
