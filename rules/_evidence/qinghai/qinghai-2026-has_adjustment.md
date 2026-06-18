# qinghai-2026-has_adjustment

> 对应规则: `QINGHAI.has_adjustment`
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
QINGHAI.has_adjustment:
  severity: warning
  value:
    has_adjustment: false
  effective_date: '2026-01-01'
  source_evidence_id: qinghai-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：青海普通类本科批专业（类）平行志愿官方明确 `不设是否服从院校专业调剂选项`，因此 truth 必须记为 `false`
- 例 2：院校顺序志愿段虽有“是否服从校内专业调剂”选项，但那是①段、⑧段的顺序志愿规则，不代表本科批主体规则

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 青海省教育考试网
- 复核负责人: 待指派
