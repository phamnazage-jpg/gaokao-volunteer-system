# qinghai-2026-max_majors_per_group

> 对应规则: `QINGHAI.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业（类）平行志愿是指以“1个专业（类）+1个院校”为1个志愿，不设是否服从院校专业调剂选项。"
> —— 出处: 《青海省2025年普通高等学校考试招生录取工作实施方案》
> URL: https://www.qhjyks.com/gkzhgg/zcwj/5153.htm
> 发布日期: 2025-02-17

## 2. 转写为机读规则

```yaml
QINGHAI.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 1
  effective_date: '2026-01-01'
  source_evidence_id: qinghai-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：青海每个平行志愿单位就是 `1个专业（类）+1个院校`，因此项目层归一化为 `max_majors_per_group: 1`
- 例 2：这里没有院校专业组内多个专业的结构，不能按院校专业组省份的 `6` 个专业口径去套

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 青海省教育考试网
- 复核负责人: 待指派
