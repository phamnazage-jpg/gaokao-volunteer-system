# guangxi-2026-has_adjustment

> 对应规则: `GUANGXI.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "填报时需填写院校专业组志愿和专业志愿、选择“是否服从专业组内专业调剂”。"
>
> "当考生所填专业均已录满时，招生院校依据考生填报的“是否服从专业组内专业调剂”情况进行专业调剂录取。"
> —— 出处: 《自治区招生考试院关于做好我区2026年普通高校招生统一考试志愿填报工作的通知》 / 《自治区教育厅关于印发〈广西2026年普通高校招生考试和录取工作方案〉的通知》
> URL: https://www.gxeea.cn/view/content_1013_32855.htm
> URL: https://www.gxeea.cn/view/content_1013_32810.htm
> 发布日期: 2026-06-17 / 2026-06-03

## 2. 转写为机读规则

```yaml
GUANGXI.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: guangxi-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：广西本科普通批志愿填报界面明确要求选择“是否服从专业组内专业调剂”，因此 `has_adjustment` 应为 `true`
- 例 2：存在调剂入口不代表能跨院校或跨专业组调剂

## 4. 后续维护

- 下次复核时间: 2026-07-10
- 复核来源: 广西招生考试院
- 复核负责人: 待指派
