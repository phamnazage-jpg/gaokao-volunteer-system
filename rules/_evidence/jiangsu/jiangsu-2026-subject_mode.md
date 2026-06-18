# jiangsu-2026-subject_mode

> 对应规则: `JIANGSU.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "江苏省2022年普通高考实行“3+1+2”模式，与2021年相同。"
> —— 出处: 《我省2022年普通高考报名即将开始》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2021-10-25/25887.html
> 发布日期: 2021-10-25
>
> "（一）历史等科目类（首选科目为历史、再选科目必选思想政治）513分。"
> "（二）物理等科目类（首选科目为物理、再选科目必选化学，或首选科目为物理、再选科目必选思想政治）543分。"
> —— 出处: 《江苏省2025年报考公安院校公安专业面试体检和体能测评资格分数线》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2025-06-24/7343283115256713216.html
> 发布日期: 2025-06-24

## 2. 转写为机读规则

```yaml
JIANGSU.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: jiangsu-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：2022 报名通知给出了江苏新高考的制度口径，即“3+1+2”模式
- 例 2：2025 公安院校资格线继续按“首选科目 / 再选科目”区分历史类与物理类，证明该模式在当前招生季仍在生效

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 江苏省教育考试院
- 复核负责人: 待指派
