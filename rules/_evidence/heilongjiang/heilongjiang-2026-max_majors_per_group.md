# heilongjiang-2026-max_majors_per_group

> 对应规则: `HEILONGJIANG.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "填报志愿采取“院校专业组”方式，一个院校专业组为一个志愿单位，每个院校专业组志愿下设6个专业志愿和是否服从专业调剂选项。"
>
> "2024年，高校将根据所列招生专业的选考科目要求及特征条件不同，将招生的专业分列到1个或多个院校专业组中，即每个专业组内设置多个专业（类），考生在志愿填报时，只能填报该院校专业组内的6个专业（类）志愿和是否服从专业调剂选项。"
> —— 出处: 《黑龙江省2024年普通高校招生考试和录取工作实施方案解读》
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202401/t20240129_18921.htm
> 发布日期: 2024-01-29

## 2. 转写为机读规则

```yaml
HEILONGJIANG.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 6
  effective_date: '2026-01-01'
  source_evidence_id: heilongjiang-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：黑龙江的 6 个专业志愿是“每个院校专业组志愿”下的组内上限，不是全批次总专业数
- 例 2：专业志愿之外还存在“是否服从专业调剂选项”，两者应分别建模

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 黑龙江省招生考试信息港
- 复核负责人: 待指派
