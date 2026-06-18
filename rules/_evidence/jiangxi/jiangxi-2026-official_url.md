# jiangxi-2026-official_url

> 对应规则: `JIANGXI.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "江西省教育考试院"
>
> "SiteDomain content=\"http://www.jxeea.cn\""
> —— 出处: 江西省教育考试院首页 / 普通高考栏目源码元信息
> URL: http://www.jxeea.cn/
> URL: http://www.jxeea.cn/ptgk49/list.html
> 发布日期: 访问复核于 2026-06-18 / HtmlGenerateTime 2026-05-13

## 2. 转写为机读规则

```yaml
JIANGXI.official_url:
  severity: info
  value:
    official_url: http://www.jxeea.cn/
  effective_date: '2026-01-01'
  source_evidence_id: jiangxi-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：江西省普通高考专题页、常见问答和高考综合改革问答都挂载在 `jxeea.cn` 主域下，因此 `official_url` 统一指向考试院主站即可
- 例 2：`jxgk.jxeea.cn` 是业务子系统入口，但不是当前省级规则真相源的主入口，不应替代考试院官网主域

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 江西
- 复核负责人: 待指派
