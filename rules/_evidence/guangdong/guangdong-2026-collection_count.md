# guangdong-2026-collection_count

> 对应规则: `GUANGDONG.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每批次录取结束后，视院校未完成招生计划的情况，省招生办公室统一组织征集志愿。"
> "各批次录取过程中，如院校未完成招生计划，且缺额较大的，省招生办公室视情况组织多次征集志愿。"
> —— 出处: 《广东省普通高等学校招生平行志愿投档及录取实施办法》
> URL: https://eea.gd.gov.cn/tzgg/content/post_4896626.html / https://eea.gd.gov.cn/attachment/0/613/613821/4896626.pdf
> 发布日期: 2026-05-13

## 2. 转写为机读规则

```yaml
GUANGDONG.collection_count:
  severity: warning
  value:
    collection_count: null
    collection_arrangement: 各批次录取结束后视缺额情况组织征集志愿
    supplementary_round: 缺额较大时可多次征集志愿
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：广东官方没有给出一个稳定固定的整数轮次，因此继续把 `collection_count` 写死为 `2` 不成立
- 例 2：官方明确保留“缺额较大时可多次征集志愿”，所以这里改成动态机读表达，避免低估真实流程复杂度

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
