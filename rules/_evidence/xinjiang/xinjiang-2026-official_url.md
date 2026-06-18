# xinjiang-2026-official_url

> 对应规则: `XINJIANG.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生务必在规定时间内按要求登录新疆教育考试院官方网站（https://www.xjzk.gov.cn），在“普通高考网上志愿填报系统”中完成志愿填报。"
>
> "考生登录新疆教育考试院官网 https://www.xjzk.gov.cn"
> —— 出处: 《新疆维吾尔自治区2026年普通高校招生工作规定》；《2026年新疆高考志愿填报系统操作手册》
> URL: http://www.xjzk.gov.cn/c/2026-05-06/495190.shtml ; http://www.xjzk.gov.cn/upload/resources/file/2026/06/12/30062.pdf
> 发布日期: 2026-05-06 ; 2026-06-12

## 2. 转写为机读规则

```yaml
XINJIANG.official_url:
  severity: info
  value:
    official_url: https://www.xjzk.gov.cn/
  effective_date: '2026-01-01'
  source_evidence_id: xinjiang-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：新疆 2026 官方新文和志愿填报手册都直接把 `https://www.xjzk.gov.cn` 当作官网入口，旧的 `http` 口径应升级到当前显式 HTTPS 入口
- 例 2：本字段记录的是考试院官网根地址，不是某篇具体通知正文页 URL

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 新疆教育考试院
- 复核负责人: 待指派
