# hainan-2026-official_url

> 对应规则: `HAINAN.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "海南省考试局"
>
> "高考信息专栏"
> —— 出处: 海南省考试局官网首页 / 高考信息专栏
> URL: http://ea.hainan.gov.cn/ / http://ea.hainan.gov.cn/ywdt/ztzl/2021gkxxzl/index.html
> 发布日期: 页面未标注

## 2. 转写为机读规则

```yaml
HAINAN.official_url:
  severity: info
  value:
    official_url: https://ea.hainan.gov.cn/
  effective_date: '2026-01-01'
  source_evidence_id: hainan-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：本条校验的是海南省考试局官方入口域名 `ea.hainan.gov.cn`，不把具体业务页路径固化到 truth 层
- 例 2：高考信息专栏、实施办法、录取公告等页面都挂在同一官方域名下，因此 `official_url` 统一收敛为官网根地址

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 海南省考试局
- 复核负责人: 待指派
