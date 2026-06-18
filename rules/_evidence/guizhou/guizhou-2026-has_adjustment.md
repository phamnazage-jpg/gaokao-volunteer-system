# guizhou-2026-has_adjustment

> 对应规则: `GUIZHOU.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "专业（类）平行志愿是指以“1个专业（类）+1个院校”为1个志愿，不设是否服从专业调剂选项。"
> —— 出处: 《贵州省2025年高考填报志愿规定》
> URL: http://zsksy.guizhou.gov.cn/ptgk/qtxx/202506/t20250625_88190180.html
> 发布日期: 2025-06-25

## 2. 转写为机读规则

```yaml
GUIZHOU.has_adjustment:
  severity: warning
  value:
    has_adjustment: false
  effective_date: '2026-01-01'
  source_evidence_id: guizhou-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：普通类本科批平行志愿明确“不设是否服从专业调剂选项”，所以项目层不能继续保留旧的 `true`
- 例 2：顺序志愿批次仍然设有调剂栏，但那是提前批顺序志愿的例外，不适合作为普通类本科批主体规则

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 贵州省招生考试院
- 复核负责人: 待指派
