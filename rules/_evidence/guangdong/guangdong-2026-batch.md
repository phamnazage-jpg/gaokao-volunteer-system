# guangdong-2026-batch

> 对应规则: `GUANGDONG.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "本科和专科录取批次普通类（物理、历史）均设 1 个平行志愿组。"
> —— 出处: 《广东省普通高等学校招生平行志愿投档及录取实施办法》
> URL: https://eea.gd.gov.cn/tzgg/content/post_4896626.html / https://eea.gd.gov.cn/attachment/0/613/613821/4896626.pdf
> 发布日期: 2026-05-13

## 2. 转写为机读规则

```yaml
GUANGDONG.batch:
  severity: info
  value:
    batch: 本科批
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：官方原文覆盖本科和专科两层次，truth 为便于跨省对比仍聚焦普通类 `本科批`
- 例 2：艺体类和平行志愿之外的顺序志愿批次不纳入本条机读范围

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
