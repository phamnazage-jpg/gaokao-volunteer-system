# chongqing-2026-official_url

> 对应规则: `CHONGQING.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "指定网站（www.cqksy.cn或www.cqzk.com.cn）。"
>
> "考生和家长可通过指定网站登录‘重庆市统一高考志愿填报辅助系统’。"
> —— 出处: 《重庆市2026年普通高校招生统一考试考后主要时间节点安排》
> URL: https://www.cqksy.cn/web/article/2026-06/09/content_6993.html
> 发布日期: 2026-06-09

## 2. 转写为机读规则

```yaml
CHONGQING.official_url:
  severity: info
  value:
    official_url: https://www.cqksy.cn/
  effective_date: '2026-01-01'
  source_evidence_id: chongqing-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：重庆考试院 2026 正文明确把 `www.cqksy.cn` 列为指定网站，项目主锚点继续收口到 `https://www.cqksy.cn/`
- 例 2：`www.cqzk.com.cn` 与辅助系统入口可作为并列指定站点存在，但不替代重庆市教育考试院官网主域名

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 重庆市教育考试院
- 复核负责人: 待指派
