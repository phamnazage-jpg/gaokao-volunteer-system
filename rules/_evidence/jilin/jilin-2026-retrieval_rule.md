# jilin-2026-retrieval_rule

> 对应规则: `JILIN.retrieval_rule`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "尽量服从调剂：平行志愿实行一轮投档，所报专业无法录取且不服从调剂时，将直接被退档，只能参加征集志愿或下一批次录取。"
>
> "考生依据本人高考成绩、排位信息，选择招生院校专业组进行填报。"
> —— 出处: 《吉林省2026年普通高考志愿填报核心要点问答集锦》 / 《吉林省2026年普通高考志愿填报及录取时间安排》
> URL: https://www.jleea.com.cn/front/content/202714
> URL: https://www.jleea.com.cn/front/content/202704
> 发布日期: 2026-06-16 / 2026-06-15

## 2. 转写为机读规则

```yaml
JILIN.retrieval_rule:
  severity: critical
  value:
    retrieval_rule: 分数优先、遵循志愿、一次投档
  effective_date: '2026-01-01'
  source_evidence_id: jilin-2026-retrieval_rule
  status: active
```

## 3. 关键边界与例外

- 例 1：官方已明确“依据高考成绩、排位信息”并对平行志愿实行“一轮投档”，这里将其归一为机读规则 `分数优先、遵循志愿、一次投档`
- 例 2：当前摘录未展开吉林同分排序细则，若后续发现官方单列同分规则文件，应补充到本证据卡

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 吉林省教育考试院
- 复核负责人: 待指派
