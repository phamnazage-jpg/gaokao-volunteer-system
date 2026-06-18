# heilongjiang-2026-has_adjustment

> 对应规则: `HEILONGJIANG.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "填报志愿采取“院校专业组”方式，一个院校专业组为一个志愿单位，每个院校专业组志愿下设6个专业志愿和是否服从专业调剂选项。"
>
> "当考生所填专业均已录满时，招生院校依据考生填报的“是否服从专业调剂选项”情况进行专业调剂录取。"
> —— 出处: 《黑龙江省2024年普通高校招生考试和录取工作实施方案解读》 / 《黑龙江省2024年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202401/t20240129_18921.htm
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202401/t20240129_18920.htm
> 发布日期: 2024-01-29

## 2. 转写为机读规则

```yaml
HEILONGJIANG.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: heilongjiang-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：黑龙江普通类院校专业组志愿明确带有“是否服从专业调剂选项”，因此 `has_adjustment` 应为 `true`
- 例 2：是否服从调剂只表示存在调剂入口，不代表一定会跨院校或跨专业组调剂

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 黑龙江省招生考试信息港
- 复核负责人: 待指派
