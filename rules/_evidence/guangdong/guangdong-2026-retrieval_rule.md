# guangdong-2026-retrieval_rule

> 对应规则: `GUANGDONG.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "院校专业组平行志愿投档是以院校专业组为投档单位，按照“分数优先、遵循志愿”的原则，实行一次性投档。"
> "如果考生档案投档到某院校专业组后，因故被退档，将不再补投到该批次平行志愿的其他院校专业组。"
> —— 出处: 《广东省普通高等学校招生工作规定》 / 《广东省普通高等学校招生平行志愿投档及录取实施办法》
> URL: https://eea.gd.gov.cn/tzgg/content/post_4896626.html / https://eea.gd.gov.cn/attachment/0/613/613821/4896626.pdf
> 发布日期: 2026-05-13

## 2. 转写为机读规则

```yaml
GUANGDONG.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：广东官方对普通类平行志愿直接给出了 `分数优先、遵循志愿、一次性投档`，机读值可原样保持
- 例 2：若考生投档后被退档，不会回补到同批次其他院校专业组，因此不能把流程误写成“退到下一个志愿”

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
