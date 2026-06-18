# shandong-2026-official_url

> 对应规则: `SHANDONG.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "山东省教育招生考试院官网"
> —— 出处: 网站首页
> URL: https://www.sdzk.cn/
> 发布日期: 页面未标注

## 2. 转写为机读规则

```yaml
SHANDONG.official_url:
  severity: info
  value:
    official_url: https://www.sdzk.cn/
  effective_date: '2026-01-01'
  source_evidence_id: shandong-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：这里固定的是考试院主站根入口，不是某一篇通知页或某个附件页
- 例 2：如果后续官方改站，应以考试院首页标题与正文入口同步复核

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 山东省教育招生考试院
- 复核负责人: 待指派
