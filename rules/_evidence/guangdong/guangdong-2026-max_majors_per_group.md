# guangdong-2026-max_majors_per_group

> 对应规则: `GUANGDONG.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组设 6 个专业志愿和 1 个是否服从专业调剂选项。"
> —— 出处: 《广东省普通高等学校招生平行志愿投档及录取实施办法》
> URL: https://eea.gd.gov.cn/tzgg/content/post_4896626.html / https://eea.gd.gov.cn/attachment/0/613/613821/4896626.pdf
> 发布日期: 2026-05-13

## 2. 转写为机读规则

```yaml
GUANGDONG.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：广东普通类每个院校专业组固定是 6 个专业志愿，因此 `max_majors_per_group` 为 `6`
- 例 2：同页把“是否服从专业调剂”单独列项，说明它不是第 7 个专业志愿

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
