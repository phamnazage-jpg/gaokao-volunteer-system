# anhui-2026-has_adjustment

> 对应规则: `ANHUI.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通本科批次，实行平行志愿，设置45个院校专业组志愿，每个院校专业组设6个专业志愿及专业服从志愿。"
> —— 出处: 《关于做好2026年普通高校招生工作的通知》
> URL: https://www.ahzsks.cn/ptgxzs/8884.htm
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
ANHUI.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: anhui-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：官方对普通本科批明确设置 `专业服从志愿`，因此 `has_adjustment` 必须为 `true`
- 例 2：并非所有提前批子类型都一定设置专业服从，证据文件中的这条结论只绑定普通本科批主流程

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 安徽省教育招生考试院
- 复核负责人: 待指派
