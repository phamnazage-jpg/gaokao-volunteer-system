# jilin-2026-max_volunteers

> 对应规则: `JILIN.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类：设提前批（分A、B段，顺序志愿，各设1个院校专业组志愿）、本科批（50个院校专业组平行志愿）、专科批（40个院校专业组平行志愿）。"
>
> "本科批设50个院校专业组平行志愿。"
> —— 出处: 《吉林省2026年普通高考志愿填报核心要点问答集锦》 / 《吉林省2026年普通高考志愿填报及录取时间安排》
> URL: https://www.jleea.com.cn/front/content/202714
> URL: https://www.jleea.com.cn/front/content/202704
> 发布日期: 2026-06-16 / 2026-06-15

## 2. 转写为机读规则

```yaml
JILIN.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 50
  effective_date: '2026-01-01'
  source_evidence_id: jilin-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：吉林普通类本科批志愿上限是 `50` 个院校专业组，不是旧高考口径或单专业直投口径
- 例 2：专科批另有 `40` 个院校专业组平行志愿，本规则只记录普通类本科批主口径

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 吉林省教育考试院
- 复核负责人: 待指派
