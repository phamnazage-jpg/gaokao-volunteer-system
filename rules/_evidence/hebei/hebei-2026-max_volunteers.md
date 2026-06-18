# hebei-2026-max_volunteers

> 对应规则: `HEBEI.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "草表三—平行志愿（96 个“院校+专业（类）”）1/3"
> "草表三—平行志愿（96 个“院校+专业（类）”）2/3"
> "草表三—平行志愿（96 个“院校+专业（类）”）3/3"
> —— 出处: 《2026年河北省普通高校招生考生志愿填报草表使用说明》
> URL: https://file.hebeea.edu.cn/upload/resources/file/2026/06/16/27068.pdf
> 发布日期: 2026-06-16

## 2. 转写为机读规则

```yaml
HEBEI.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 96
  effective_date: '2026-01-01'
  source_evidence_id: hebei-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：官方草表把本科批平行志愿拆成 3 页展示，但总志愿单位明确仍是 96 个
- 例 2：该条证据对应的是“院校+专业（类）”志愿单位总数，不是院校数或专业总数

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 河北省教育考试院
- 复核负责人: 待指派
