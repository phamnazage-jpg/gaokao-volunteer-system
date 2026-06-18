# shanghai-2026-collection_count

> 对应规则: `SHANGHAI.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科普通批次录取完毕后开展两次征求志愿。"
> "两次征求志愿均可填报24个院校专业组志愿，每个院校专业组志愿内最多可填4个专业志愿和1个愿否调剂专业选项。"
> —— 出处: 《上海市2025年普通高等学校招生志愿填报与投档录取实施办法》 / 《2024年上海市普通高校招生本科普通批次征求志愿问答》
> URL: https://www.shmeea.edu.cn/page/06300/20250425/19280.html / https://www.shmeea.edu.cn/page/08000/20240722/18696.html
> 发布日期: 2025-04-25 / 2024-07-22

## 2. 转写为机读规则

```yaml
SHANGHAI.collection_count:
  severity: warning
  value:
    collection_count: 2
  effective_date: '2026-01-01'
  source_evidence_id: shanghai-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：上海本科普通批主流程明确是 `两次征求志愿`，因此旧值 `1` 不符合官方口径，需修正为 `2`
- 例 2：该整数只描述本科普通批主流程，不包含艺体类乙批次或专科阶段各批次的后续志愿安排

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 上海市教育考试院
- 复核负责人: 待指派
