# jiangsu-2026-collection_count

> 对应规则: `JIANGSU.collection_count`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "各批次（艺术类本科提前批次第1小批除外）录取结束后，省教育考试院将公布未完成招生计划的院校专业组、专业（类）及计划数。未被录取且符合填报条件的考生可在规定时间内填报征求志愿。"
> —— 出处: 《江苏省2026年普通高考考后提醒》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2026-06-10/7470370318775750656.html
> 发布日期: 2026-06-10
>
> "各批次（艺术类本科提前批次第1小批除外）录取结束后，省教育考试院将公布未完成招生计划的院校专业组、专业（类）及计划数。未被录取且符合填报条件的考生可在规定时间内填报征求志愿。"
> "（三）专科补录志愿填报时间为8月8日9:00至15:00。"
> —— 出处: 《2025年高考志愿填报热点问题》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2025-06-25/7343571560269090816.html
> 发布日期: 2025-06-25

## 2. 转写为机读规则

```yaml
JIANGSU.collection_count:
  severity: warning
  value:
    collection_count: null
    collection_arrangement: 各批次录取结束后按缺额公布征求志愿
    supplementary_round: 专科补录
  effective_date: '2026-01-01'
  source_evidence_id: jiangsu-2026-collection_count
  status: active
```

## 3. 关键边界与例外

- 例 1：江苏官方说明的是“各批次录取结束后按缺额征求志愿”，并未给出一个可稳定核实的固定整数次数
- 例 2：除批次征求志愿外，江苏还单列了专科补录时间，因此继续把 `collection_count` 写死为 `1` 会低估真实流程复杂度

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 江苏省教育考试院
- 复核负责人: 待指派
