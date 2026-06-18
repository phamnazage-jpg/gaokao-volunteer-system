# xinjiang-2026-max_volunteers

> 对应规则: `XINJIANG.max_volunteers`
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
XINJIANG.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 18
  effective_date: '2026-01-01'
  source_evidence_id: xinjiang-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：新疆普通类 `本科一批次` 2026 官方已明确是 `18` 个平行志愿，不再是旧规则表里的 `9`
- 例 2：这里锚定的是省级主规则使用的 `本科一批`，不是提前批或专项批的较小志愿数

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 新疆教育考试院
- 复核负责人: 待指派
