# zhejiang-2026-official_url

> 对应规则: `ZHEJIANG.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "浙江省教育考试院网站（www.zjzs.net）为填报志愿的唯一网站。"
> —— 出处: 《浙江省教育考试院关于做好2026年普通高校招生网上填报志愿工作的通知》
> URL: https://www.zjzs.net/art/2026/6/13/art_156_12376.html
> 发布日期: 2026-06-05
>
> "考生填报志愿时需了解详尽内容，可查询浙江省教育考试院网站（www.zjzs.net）发布的各类政策规定和高考相关权威信息。"
> "考生还可以通过“浙江考试”官方微信公众号实时了解相关信息。"
> —— 出处: 《浙江省2026年高考招生志愿填报百问百答》
> URL: https://www.zjzs.net/art/2026/6/17/art_45_12386.html
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
ZHEJIANG.official_url:
  severity: info
  value:
    official_url: https://www.zjzs.net/
  effective_date: '2026-01-01'
  source_evidence_id: zhejiang-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：浙江普通高考志愿填报的唯一官方 Web 入口是 `www.zjzs.net`，因此 `official_url` 锁定到该根站点
- 例 2：官方微信公众号属于辅助信息渠道，不替代正式填报和政策发布网站

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 浙江省教育考试院
- 复核负责人: 待指派
