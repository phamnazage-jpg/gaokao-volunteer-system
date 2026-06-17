# hunan-2026-exam_subject_total

> 对应规则: `HUNAN.exam_subject_total`
> 所属: 省级（信息型规则）
> 规则版本: `2026.1`
> 摘录时间: 2026-06-17
> 摘录人: Hermes Agent (主代理)

## 1. 官方原文摘录

> "湖南省 2026 年高考总分为 750 分。其中语文、数学、外语各 150 分（外语含听力 30 分），按原始分计入；首选科目 100 分，再选科目各 100 分，按等级转换分计入。"
> —— 出处: 《湖南省 2026 年普通高校招生工作实施办法》第一章"考试"

## 2. 转写为机读规则

```yaml
HUNAN.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: 2026-01-01
  source_evidence_id: hunan-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：再选科目的等级转换分由省考试院公布，原始分与转换分可能不一致
- 例 2：750 分为最高总分，不含任何加分项

## 4. 后续维护

- 下次复核时间: 2026-09-01
- 复核来源: 湖南省教育考试院
- 复核负责人: 待指派
