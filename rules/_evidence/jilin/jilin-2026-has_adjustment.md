# jilin-2026-has_adjustment

> 对应规则: `JILIN.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿均设置6个专业志愿和是否服从专业调剂选项。"
>
> "尽量服从调剂：平行志愿实行一轮投档，所报专业无法录取且不服从调剂时，将直接被退档，只能参加征集志愿或下一批次录取。"
> —— 出处: 《吉林省2026年普通高考志愿填报及录取时间安排》 / 《吉林省2026年普通高考志愿填报核心要点问答集锦》
> URL: https://www.jleea.com.cn/front/content/202704
> URL: https://www.jleea.com.cn/front/content/202714
> 发布日期: 2026-06-15 / 2026-06-16

## 2. 转写为机读规则

```yaml
JILIN.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: jilin-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：吉林普通类本科批明确带有“是否服从专业调剂选项”，因此 `has_adjustment` 应为 `true`
- 例 2：考生若不服从调剂且所报专业无法录取，会在一轮投档后直接退档，这一风险是吉林当前规则的关键边界

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 吉林省教育考试院
- 复核负责人: 待指派
