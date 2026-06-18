# hebei-2026-has_adjustment

> 对应规则: `HEBEI.has_adjustment`
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
HEBEI.has_adjustment:
  severity: warning
  value:
    has_adjustment: false
  effective_date: '2026-01-01'
  source_evidence_id: hebei-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：河北官方草表对顺序志愿单列“专业调剂”选项，但本科批平行志愿草表没有对应栏位；`has_adjustment: false` 是基于官方表单结构的直接归纳
- 例 2：这条规则只约束“院校+专业（类）”平行志愿，不外推到提前批顺序志愿

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 河北省教育考试院
- 复核负责人: 待指派
