# hebei-2026-official_url

> 对应规则: `HEBEI.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "河北省教育考试院"
> "考生在规定时间，登录省教育考试院网站（网址：http://www.hebeea.edu.cn，或直接访问https：//gk.hebeea.edu.cn），通过志愿填报系统进行志愿填报。"
> —— 出处: 河北省教育考试院首页 / 《2026年河北省普通高考志愿填报须知》
> URL: https://www.hebeea.edu.cn/ / https://www.hebeea.edu.cn/c/2026-06-17/493051.html
> 发布日期: 首页实时页 / 2026-06-17

## 2. 转写为机读规则

```yaml
HEBEI.official_url:
  severity: info
  value:
    official_url: https://www.hebeea.edu.cn/
  effective_date: '2026-01-01'
  source_evidence_id: hebei-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：truth 层保留主站 `https://www.hebeea.edu.cn/` 作为 `official_url`，实际填报入口 `https://gk.hebeea.edu.cn` 作为辅助跳转来源保留在摘录中
- 例 2：只接受河北省教育考试院域名作为省级官方入口，不把第三方志愿服务站点并入 `official_url`

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 河北省教育考试院
- 复核负责人: 待指派
