# anhui-2026-subject_mode

> 对应规则: `ANHUI.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "我省2026年普通高考实行“3+1+2”模式。"
> "“1”为首选科目，即历史、物理中选择的1科；“2”为再选科目，即思想政治、地理、化学、生物学4科中选择的2科。"
> —— 出处: 《关于做好2026年普通高校招生工作的通知》
> URL: https://www.ahzsks.cn/ptgxzs/8884.htm
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
ANHUI.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: anhui-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：安徽 2026 已是 `3+1+2` 新高考结构，不能再按传统文理分科口径处理
- 例 2：`3+1+2` 的 `3` 中外语语种可选，但不影响 `subject_mode` 的总体机读表达

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 安徽省教育招生考试院
- 复核负责人: 待指派
