# hebei-2026-adjustment_scope

> 对应规则: `HEBEI.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "草表二—顺序志愿（1 所院校）"
> "专业调剂          服从专业调剂    不服从专业调剂"
> "草表三—平行志愿（96 个“院校+专业（类）”）1/3"
> "序号        院校代号及名称                专业代号及名称"
> —— 出处: 《2026年河北省普通高校招生考生志愿填报草表使用说明》
> URL: https://file.hebeea.edu.cn/upload/resources/file/2026/06/16/27068.pdf
> 发布日期: 2026-06-16

## 2. 转写为机读规则

```yaml
HEBEI.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 无
  effective_date: '2026-01-01'
  source_evidence_id: hebei-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：本科批平行志愿草表没有任何“服从专业调剂”输入位，因此机读层将 `adjustment_scope` 明确记为 `无`
- 例 2：这里的“无”表示不存在可申报的调剂范围，不是“存在调剂但范围未公布”

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 河北省教育考试院
- 复核负责人: 待指派
