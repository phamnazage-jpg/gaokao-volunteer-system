# xizang-2026-subject_mode

> 对应规则: `XIZANG.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "我区普通高等学校招生全国统一考试科目设置为 3＋文科综合/理科综合。"
>
> "3＋文科综合简称文史类，3＋理科综合简称理工类。考生必须从文史类和理工类中选择一类填报，不得兼报。"
> —— 出处: 《西藏自治区2026年普通高等学校招生规定》
> URL: http://zsks.edu.xizang.gov.cn/71/74/7787.html
> 发布日期: 2026-05-29

## 2. 转写为机读规则

```yaml
XIZANG.subject_mode:
  severity: warning
  value:
    subject_mode: 传统
  effective_date: '2026-01-01'
  source_evidence_id: xizang-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：西藏 2026 仍按文史类 / 理工类组织普通高考，主体选科模式应继续记为 `传统`
- 例 2：藏语文加试、艺术体育专业考试是附加考试要求，不改变普通高考主体科类结构

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 西藏教育考试院
- 复核负责人: 待指派
