# heilongjiang-2026-batch

> 对应规则: `HEILONGJIANG.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "2024年，我省对招生批次进行合并。原普通本科一批（A段、B段）和普通本科二批（A段、B段）合并为普通本科批。"
>
> "②普通本科批（实行平行志愿，设40个院校专业组志愿）"
> —— 出处: 《黑龙江省2024年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202401/t20240129_18920.htm
> 发布日期: 2024-01-29

## 2. 转写为机读规则

```yaml
HEILONGJIANG.batch:
  severity: info
  value:
    batch: 本科批
  effective_date: '2026-01-01'
  source_evidence_id: heilongjiang-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：黑龙江新高考后普通本科一批和普通本科二批已合并，机读批次应统一为 `本科批`
- 例 2：本规则针对普通类本科主批次，不覆盖提前批或高职（专科）批

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 黑龙江省招生考试信息港
- 复核负责人: 待指派
