# henan-2026-official_url

> 对应规则: `HENAN.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "正式填报志愿时，仍须登录河南省教育考试院网站（https://www.haeea.cn），点击“河南省普通高校招生考生服务平台”（https://pzwb.haeea.cn），按有关规定和时间进行填报。"
> —— 出处: 《2026年普通高招网上填报志愿二次模拟演练期间我省将开放高考志愿填报辅助系统》
> URL: https://www.haeea.cn/a/202606/43688_93a78308.shtml
> 发布日期: 2026-06-12

## 2. 转写为机读规则

```yaml
HENAN.official_url:
  severity: info
  value:
    official_url: https://www.haeea.cn/
  effective_date: '2026-01-01'
  source_evidence_id: henan-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：官方正文直接把 `https://www.haeea.cn` 作为正式填报志愿的入口站点
- 例 2：`pzwb.haeea.cn` 是考生服务平台子域，不应替代省教育考试院主站作为省级 `official_url`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 河南
- 复核负责人: 待指派
