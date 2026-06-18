# gansu-2026-max_majors_per_group

> 对应规则: `GANSU.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类本科批：实行平行志愿投档，每个院校专业组志愿设置45个院校专业组志愿，每个院校专业组志愿设置6个专业选项和1个服从专业调剂选项。未完成招生计划实施2次征集志愿。"
> —— 出处: 《关于做好2026年甘肃省普通高校招生工作的通知》
> URL: https://www.ganseea.cn/gaokaogaozhao/1884.html
> 发布日期: 2026-05-20

## 2. 转写为机读规则

```yaml
GANSU.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: gansu-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：甘肃 2026 每个院校专业组志愿内固定是 `6` 个专业选项，不应误读成整批 6 个志愿位
- 例 2：`6` 个专业选项与后面的 `1` 个服从专业调剂选项是并列配置，不能把调剂位计入专业数量上限

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 甘肃省教育考试院
- 复核负责人: 待指派
