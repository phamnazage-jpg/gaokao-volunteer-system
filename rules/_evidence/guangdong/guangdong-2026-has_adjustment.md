# guangdong-2026-has_adjustment

> 对应规则: `GUANGDONG.has_adjustment`
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
GUANGDONG.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：广东普通类平行志愿明确提供 `是否服从专业调剂选项`，因此 `has_adjustment` 必须为 `true`
- 例 2：本条只覆盖普通类院校专业组主流程，不表示所有特殊类型批次都一定提供该选项

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
