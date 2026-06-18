# beijing-2026-collection_count

> 对应规则: `BEIJING.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "征集志愿：根据各批次实时录取进程动态安排，以北京教育考试院官网即时通知为准。"
> —— 出处: 《常见问题》
> URL: https://www.bjeea.cn/html/2026gz/cjwt/2026/0612/88212.html
> 发布日期: 2026-06-12
>
> "录取期间，按考生已填报志愿录取结束时，如当前批次高校计划未完成，将根据情况征集考生志愿。"
> "录取过程中，首先在批次分数线上进行考生已填报志愿的录取，如有高校招生计划未完成，将根据情况依次进行批次分数线上征集志愿录取和降分征集志愿录取。"
> —— 出处: 《北京市2026年普通高等学校招生工作规定》
> URL: https://www.bjeea.cn/html/gkgz/tzgg/2026/0505/88114.html
> 发布日期: 2026-05-08

## 2. 转写为机读规则

```yaml
BEIJING.collection_count:
  severity: warning
  value:
    collection_count: null
    collection_arrangement: 动态安排
    collection_timing: 下一批次录取开始前
  effective_date: '2026-01-01'
  source_evidence_id: beijing-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：北京官方文件当前没有承诺固定征集次数，机读值用 `collection_count: null` 表示“无可核实固定次数”
- 例 2：补充 `collection_arrangement` 和 `collection_timing`，用于保留“动态安排”“下一批次录取开始前完成”的官方约束，而不是伪造一个固定整数

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 北京
- 复核负责人: 待指派
