# xizang-2026-exam_subject_total

> 对应规则: `XIZANG.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "语文、数学、外语各科满分为 150 分，文科综合/理科综合满分为 300 分，高考卷面总分 750 分。"
> —— 出处: 《西藏自治区2026年普通高等学校招生规定》
> URL: http://zsks.edu.xizang.gov.cn/71/74/7787.html
> 发布日期: 2026-05-29

## 2. 转写为机读规则

```yaml
XIZANG.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: xizang-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：西藏普通高考卷面总分为 `750`，由 `150+150+150+300` 组成
- 例 2：藏语文加试满分 `150` 仅供相关高校录取时参考，不计入高考卷面总分

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 西藏教育考试院
- 复核负责人: 待指派
