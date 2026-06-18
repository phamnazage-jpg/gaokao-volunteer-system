# chongqing-2026-has_adjustment

> 对应规则: `CHONGQING.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "院校顺序志愿以‘1个学校+6个专业（类）’为1个志愿，并设置是否服从专业调剂选项。"
> —— 出处: 《录取批次及志愿设置》
> URL: https://www.cqksy.cn/web/article/2025-06/17/content_6631.html
> 发布日期: 2025-06-17

## 2. 转写为机读规则

```yaml
CHONGQING.has_adjustment:
  severity: warning
  value:
    has_adjustment: false
  effective_date: '2026-01-01'
  source_evidence_id: chongqing-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：官方把“是否服从专业调剂选项”明确限定在院校顺序志愿，不在普通类 `本科批` 的专业平行志愿内
- 例 2：因此重庆普通类 `本科批` 的机读值应为 `has_adjustment: false`，不能把顺序志愿的调剂开关外推到专业平行志愿

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 重庆市教育考试院
- 复核负责人: 待指派
