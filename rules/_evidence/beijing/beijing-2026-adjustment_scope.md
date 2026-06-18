# beijing-2026-adjustment_scope

> 对应规则: `BEIJING.adjustment_scope`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个志愿一般设置6个志愿专业和一个“是否服从专业组内调剂”选项。"
> —— 出处: 《本科普通批志愿填报政策早了解》
> URL: https://www.bjeea.cn/html/ksb/gaozhaozhuanban/2022/0330/81257.html
> 发布日期: 2022-03-30
>
> "是否服从院校内专业调剂"
> —— 出处: 《北京市2026年普通高等学校招生志愿填报须知》附件《志愿样表》
> URL: https://www.bjeea.cn/uploads/soft/260614/%E9%99%84%E4%BB%B6%EF%BC%9A%E5%BF%97%E6%84%BF%E6%A0%B7%E8%A1%A8.docx
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
BEIJING.adjustment_scope:
  severity: fatal
  value:
    adjustment_scope: 组内专业
  effective_date: '2026-01-01'
  source_evidence_id: beijing-2026-adjustment_scope
  status: active
```

## 3. 关键边界与例外

- 例 1：2022 年官方解读使用“专业组内调剂”表述，说明调剂范围在当前志愿所属专业组内
- 例 2：2026 年样表写法为“院校内专业调剂”，但它挂在单个院校专业组志愿格内，当前 truth 仍按 `组内专业` 落模

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 北京教育考试院 / 北京考试报
- 复核负责人: 待指派
