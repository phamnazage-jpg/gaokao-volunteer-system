# beijing-2026-max_volunteers

> 对应规则: `BEIJING.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科普通批填报实行平行志愿，共设置30个志愿。"
> —— 出处: 《本科普通批志愿填报政策早了解》
> URL: https://www.bjeea.cn/html/ksb/gaozhaozhuanban/2022/0330/81257.html
> 发布日期: 2022-03-30
>
> "统考考生填报本科提前批志愿、特殊类型招生志愿、本科普通批志愿。"
> —— 出处: 《北京市2026年普通高等学校招生志愿填报须知》
> URL: https://www.bjeea.cn/html/gkgz/tzgg/2026/0614/88216.html
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
BEIJING.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 30
  effective_date: '2026-01-01'
  source_evidence_id: beijing-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：`30 个志愿` 的明确数字来自北京考试报官方解读，2026 志愿填报须知用于确认本科普通批仍是当前招生季实际批次
- 例 2：2026 年样表与须知没有在正文中重复写出“30”，后续仍应优先用当年正式政策文件替换为更直接的年度证据

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 北京教育考试院 / 北京考试报
- 复核负责人: 待指派
