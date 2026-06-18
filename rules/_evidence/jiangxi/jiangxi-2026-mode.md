# jiangxi-2026-mode

> 对应规则: `JIANGXI.mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "新高考按照“院校专业组”模式设置志愿，每个“院校专业组”即为一个独立的志愿，内设6个专业志愿和是否服从专业调剂志愿。"
> —— 出处: 《十六、新高考志愿如何设置？》
> URL: http://www.jxeea.cn/jxsjyksy/cjwd22/content/content_1856071455097688064.html
> 发布日期: 2024-06-21

## 2. 转写为机读规则

```yaml
JIANGXI.mode:
  severity: fatal
  value:
    mode: 院校专业组
  effective_date: '2026-01-01'
  source_evidence_id: jiangxi-2026-mode
  status: active
```

## 3. 关键边界与例外

- 例 1：江西普通类志愿的基本单位已经明确切换为 `院校专业组`，不能再按旧高考的院校志愿或传统文理批次去解释
- 例 2：同一院校可拆分多个院校专业组，因此 `mode` 必须保留为 `院校专业组`，不能退化成笼统的“平行志愿”

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 江西
- 复核负责人: 待指派
