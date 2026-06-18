# shanghai-2026-official_url

> 对应规则: `SHANGHAI.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "上海市教育考试院官方网站“上海招考热线”（www.shmeea.edu.cn）；"
> —— 出处: 《上海市2025年普通高校招生本科阶段志愿填报即将开始》
> URL: https://www.shmeea.edu.cn/page/08000/20250623/19544.html
> 发布日期: 2025-06-23
>
> "<li><a href=\"/page/24400/index.html\" title=\"志愿填报\"><i class=\"iconfont icon-kaoshixinxi\"></i>志愿填报</a></li>"
> —— 出处: 上海市教育考试院首页
> URL: https://www.shmeea.edu.cn/page/index.html
> 发布日期: 页面抓取时间 2026-06-18

## 2. 转写为机读规则

```yaml
SHANGHAI.official_url:
  severity: info
  value:
    official_url: https://www.shmeea.edu.cn/
  effective_date: '2026-01-01'
  source_evidence_id: shanghai-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：官方已明确 `www.shmeea.edu.cn` 是上海市教育考试院“上海招考热线”官网，因此 `official_url` 指向该站点首页
- 例 2：首页导航直接暴露“志愿填报”入口，说明该 URL 既是官方信息发布入口，也是考生使用入口的根节点

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 上海市教育考试院
- 复核负责人: 待指派
