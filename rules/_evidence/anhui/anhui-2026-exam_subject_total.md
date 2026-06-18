# anhui-2026-exam_subject_total

> 对应规则: `ANHUI.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生的成绩由语文、数学、外语3门统考科目成绩和考生自主选择的3门选考科目成绩组成，满分为750分。"
> "选考科目满分均为100分，历史和物理科目以原始分计入总分，其他科目以等级分计入总分。"
> —— 出处: 《关于做好2026年普通高校招生工作的通知》
> URL: https://www.ahzsks.cn/ptgxzs/8884.htm
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
ANHUI.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: anhui-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：安徽 2026 高考总分仍是 `750`，其中语文、数学、外语各 `150` 分，选考科目各 `100` 分
- 例 2：再选科目存在等级分转换，但不改变总分上限，因此 `exam_subject_total` 仍机读为 `750`

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 安徽省教育招生考试院
- 复核负责人: 待指派
