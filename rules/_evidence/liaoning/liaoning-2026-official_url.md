# liaoning-2026-official_url

> 对应规则: `LIAONING.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "“辽宁招生考试之窗”为志愿填报的唯一网站。"
>
> "考生可在规定时间内，使用高考报名时的账号和密码通过“辽宁招生考试之窗”网站（https://www.lnzsks.com/）进入“网报中心”。"
> —— 出处: 《辽宁省2024年普通高校招生志愿填报及招生录取问答》
> URL: https://www.lnzsks.com/newsinfo/IMS_20240619_44007_hZ6qDmgcpv.htm
> 发布日期: 2024-06-19

## 2. 转写为机读规则

```yaml
LIAONING.official_url:
  severity: info
  value:
    official_url: https://www.lnzsks.com/
  effective_date: '2026-01-01'
  source_evidence_id: liaoning-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：辽宁官方已明确 `https://www.lnzsks.com/` 是唯一志愿填报入口，`official_url` 应绑定该根站点
- 例 2：直接登录地址 `https://gkzy.lnzsks.com` 属于网报中心子入口，不替代省级官方主站

## 4. 后续维护

- 下次复核时间: 2026-06-30
- 复核来源: 辽宁招生考试之窗
- 复核负责人: 待指派
