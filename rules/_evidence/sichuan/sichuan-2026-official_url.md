# sichuan-2026-official_url

> 对应规则: `SICHUAN.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "四川省教育考试院"
>
> "关于做好我省2026年普通高校招生工作的通知"
> —— 出处: 四川省教育考试院官网首页
> URL: http://www.sceea.cn/
> 发布日期: 2026-04-23（首页所列通知时间）

## 2. 转写为机读规则

```yaml
SICHUAN.official_url:
  severity: info
  value:
    official_url: https://www.sceea.cn/
  effective_date: '2026-01-01'
  source_evidence_id: sichuan-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：本条校验的是四川省教育考试院官方入口域名 `sceea.cn`，不将具体通知路径固化到 truth 层
- 例 2：首页可直接抵达 2026 高招通知，因此 `https://www.sceea.cn/` 仍足以作为四川规则入口根地址

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 四川省教育考试院
- 复核负责人: 待指派
