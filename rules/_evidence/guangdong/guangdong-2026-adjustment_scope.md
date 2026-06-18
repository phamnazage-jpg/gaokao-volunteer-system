# guangdong-2026-adjustment_scope

> 对应规则: `GUANGDONG.adjustment_scope`
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
GUANGDONG.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：调剂选项是挂在单个 `院校专业组` 下的，因此当前机读范围保持为 `组内专业`
- 例 2：官方未给出跨院校专业组调剂路径；平行志愿投档后“其他所填报的院校专业组无效”，即其他院校专业组无效，考生若被某组退档，也不会补投到同批次其他院校专业组

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
