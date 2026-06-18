# heilongjiang-2026-adjustment_scope

> 对应规则: `HEILONGJIANG.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "实行“院校专业组”投档录取方式，招生院校会将本校招生的专业根据教学培养、学科建设等需要进行分组，一个院校被分成多个院校专业组进行招生。"
>
> "当考生所填专业均已录满时，招生院校依据考生填报的“是否服从专业调剂选项”情况进行专业调剂录取。专业调剂录取只能在考生被投档的院校专业组内未录满专业中按招生院校录取原则进行调剂录取。"
> —— 出处: 《黑龙江省2024年普通高校招生考试和录取工作实施方案解读》 / 《黑龙江省2024年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202401/t20240129_18921.htm
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202401/t20240129_18920.htm
> 发布日期: 2024-01-29

## 2. 转写为机读规则

```yaml
HEILONGJIANG.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: heilongjiang-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：黑龙江调剂明确限制在“被投档的院校专业组内未录满专业”，因此机读范围应是 `组内专业`
- 例 2：该口径排除了跨院校、跨专业组调剂，不能误写成“全部专业”

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 黑龙江省招生考试信息港
- 复核负责人: 待指派
