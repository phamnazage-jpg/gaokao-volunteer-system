# qinghai-2026-official_url

> 对应规则: `QINGHAI.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "青海省教育考试网是青海省教育招生考试院官方网站，也是我省高考网上填报志愿的唯一网站。"
> —— 出处: 《青海省2026年普通高等学校招生录取工作实施细则》
> URL: https://www.qhjyks.com/ztzl/ptgkz/5807.htm
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
QINGHAI.official_url:
  severity: info
  value:
    official_url: https://www.qhjyks.com/
  effective_date: '2026-01-01'
  source_evidence_id: qinghai-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：青海 2026 官方正文已明确官网主体是 `青海省教育考试网`，truth 应落到当前有效站点 `https://www.qhjyks.com/`
- 例 2：旧的 `http://www.qhzk.com/` 当前已不是官方考试院站点，不能继续作为规则 truth 的官方入口

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 青海省教育考试网
- 复核负责人: 待指派
