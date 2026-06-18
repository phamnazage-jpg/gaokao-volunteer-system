# jiangsu-2026-official_url

> 对应规则: `JIANGSU.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "江苏省教育考试院"
> "普通高考"
> —— 出处: 江苏省教育考试院首页
> URL: https://www.jseea.cn/
> 发布日期: 2026-06-17
>
> "考生在获知高考成绩、各批次录取控制分数线、逐分段统计数据后，登录省教育考试院网站（www.jseea.cn）或江苏省2025年普通高考考生服务平台（gk.jseea.cn，以下简称考生服务平台）填报高考志愿。"
> —— 出处: 《2025年高考志愿填报热点问题》
> URL: https://www.jseea.cn/webfile/index/index_zkxx/2025-06-25/7343571560269090816.html
> 发布日期: 2025-06-25

## 2. 转写为机读规则

```yaml
JIANGSU.official_url:
  severity: info
  value:
    official_url: https://www.jseea.cn/
  effective_date: '2026-01-01'
  source_evidence_id: jiangsu-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：首页标题和栏目结构可以直接确认 `https://www.jseea.cn/` 是江苏省教育考试院门户，而不是第三方镜像
- 例 2：志愿填报热点问题再次把 `www.jseea.cn` 作为考生获取成绩、分数线和志愿填报入口的官方站点引用，适合固化为 canonical `official_url`

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 江苏省教育考试院
- 复核负责人: 待指派
