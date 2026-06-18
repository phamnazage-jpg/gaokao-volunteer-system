# hebei-2026-max_majors_per_group

> 对应规则: `HEBEI.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "草表三—平行志愿（96 个“院校+专业（类）”）1/3"
> "序号        院校代号及名称                专业代号及名称"
> —— 出处: 《2026年河北省普通高校招生考生志愿填报草表使用说明》
> URL: https://file.hebeea.edu.cn/upload/resources/file/2026/06/16/27068.pdf
> 发布日期: 2026-06-16

## 2. 转写为机读规则

```yaml
HEBEI.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 1
  effective_date: '2026-01-01'
  source_evidence_id: hebei-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：河北本科批平行志愿的每一行只对应 1 个“院校+专业（类）”组合，因此机读上限是 `max_majors_per_group: 1`
- 例 2：这里的“1”是每个志愿单位内可填的专业（类）数，不代表总志愿只能填 1 个

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 河北省教育考试院
- 复核负责人: 待指派
