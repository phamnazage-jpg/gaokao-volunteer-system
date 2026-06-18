# anhui-2026-official_url

> 对应规则: `ANHUI.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生也可自行登录省教育招生考试院网站（www.ahzsks.cn）下载志愿预填表进行预填。"
> "考生可持续关注我院官方网站和微信公众号。"
> —— 出处: 《手把手教你填志愿（一）——带你读懂我省2026年高考考生志愿网上填报办法》
> URL: https://www.ahzsks.cn/ptgxzs/8931.htm
> 发布日期: 2026-06-11

## 2. 转写为机读规则

```yaml
ANHUI.official_url:
  severity: info
  value:
    official_url: https://www.ahzsks.cn/
  effective_date: '2026-01-01'
  source_evidence_id: anhui-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：安徽考试院正文直接把 `www.ahzsks.cn` 作为考生下载预填表和跟踪通知的官方入口，因此 truth 里规范化为 `https://www.ahzsks.cn/`
- 例 2：`xgk.ahzsks.cn` 是志愿服务平台子域，不替代省考试院主站作为 `official_url` 根入口

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 安徽省教育招生考试院
- 复核负责人: 待指派
