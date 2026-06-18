# jilin-2026-official_url

> 对应规则: `JILIN.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "# 吉林省教育考试院"
>
> "吉林省教育考试院官方网站"
> —— 出处: 吉林省教育考试院官网首页 / 《吉林省2026年普通高考志愿填报核心要点问答集锦》
> URL: https://www.jleea.com.cn/
> URL: https://www.jleea.com.cn/front/content/202714
> 发布日期: 2026-06-16（问答页）

## 2. 转写为机读规则

```yaml
JILIN.official_url:
  severity: info
  value:
    official_url: https://www.jleea.com.cn/
  effective_date: '2026-01-01'
  source_evidence_id: jilin-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：吉林志愿填报与公告发布均指向 `https://www.jleea.com.cn/` 这一省级官方站点，`official_url` 应绑定该入口
- 例 2：`https://gk.jleea.com.cn` 是考生服务平台子入口，用于报名、填报与查询，不替代考试院主站

## 4. 后续维护

- 下次复核时间: 2026-06-30
- 复核来源: 吉林省教育考试院
- 复核负责人: 待指派
