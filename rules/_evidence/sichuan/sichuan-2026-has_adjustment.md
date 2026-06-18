# sichuan-2026-has_adjustment

> 对应规则: `SICHUAN.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿内设置6个专业志愿和是否服从专业调剂选项。"
> —— 出处: 《四川省2026年普通高校招生实施规定》
> URL: http://www.sceea.cn/Html/202604/Newsdetail_4767.html
> 发布日期: 2026-04-21 / 2026-04-23 发布

## 2. 转写为机读规则

```yaml
SICHUAN.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: sichuan-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：四川本科与专科的院校专业组志愿都带有“是否服从专业调剂选项”，因此 `has_adjustment=true`
- 例 2：调剂是填报时显式选择项，不代表招生院校可以在未勾选时默认跨志愿调剂

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 四川省教育考试院
- 复核负责人: 待指派
