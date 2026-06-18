# xizang-2026-max_majors_per_group

> 对应规则: `XIZANG.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个批次设置 A、B、C、D、E、F、G、H、I、J 共 10 个并列的院校志愿，每个院校设置 4 个专业志愿和专业服从调剂志愿，不设院校服从调剂志愿。"
> —— 出处: 《西藏自治区2026年普通高等学校招生规定》
> URL: http://zsks.edu.xizang.gov.cn/71/74/7787.html
> 发布日期: 2026-05-29

## 2. 转写为机读规则

```yaml
XIZANG.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 4
  effective_date: '2026-01-01'
  source_evidence_id: xizang-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：西藏每个院校志愿下是 `4` 个专业志愿，不是多数传统省份常见的 `5` 或 `6`
- 例 2：这里的 `4` 不含后面的“专业服从调剂志愿”，两者不能混算

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 西藏教育考试院
- 复核负责人: 待指派
