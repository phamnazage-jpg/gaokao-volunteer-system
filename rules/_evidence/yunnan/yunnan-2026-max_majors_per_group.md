# yunnan-2026-max_majors_per_group

> 对应规则: `YUNNAN.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿设置10个专业志愿和1个专业服从院校调剂标志。"
> —— 出处: 《云南省2025年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.ynzs.cn/html/content/7511.html
> 发布日期: 2025-01-23

## 2. 转写为机读规则

```yaml
YUNNAN.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 10
  effective_date: '2026-01-01'
  source_evidence_id: yunnan-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：云南普通类本科批每个院校专业组都允许填报 `10` 个专业志愿，旧值 `5` 会直接少算一半容量
- 例 2：艺术类、体育类本科批存在“每组 1 个专业志愿”的特殊场景，但当前省级主规则面向普通类主体规则

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 云南省招生考试院
- 复核负责人: 待指派
