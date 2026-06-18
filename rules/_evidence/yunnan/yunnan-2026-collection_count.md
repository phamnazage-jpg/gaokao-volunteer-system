# yunnan-2026-collection_count

> 对应规则: `YUNNAN.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "各批次原始志愿录取结束后，结合实际安排征集志愿，征集志愿设置与相应批次原始志愿设置规则一致。"
>
> "投档完成后，未完成的招生计划将统一公布，重新公开征集志愿，并按征集志愿进行投档。"
> —— 出处: 《云南省2025年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.ynzs.cn/html/content/7511.html
> 发布日期: 2025-01-23

## 2. 转写为机读规则

```yaml
YUNNAN.collection_count:
  severity: warning
  value:
    collection_count: null
    collection_arrangement: 根据录取实际情况公开征集志愿
    collection_timing: 结合实际另行安排
  effective_date: '2026-01-01'
  source_evidence_id: yunnan-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：云南官方没有承诺固定征集轮次，只说明“结合实际安排”，因此继续写死 `1` 会伪造稳定整数
- 例 2：征集志愿仍然保留，但应以动态机读表达记录是否安排、何时安排和按何规则安排

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 云南省招生考试院
- 复核负责人: 待指派
