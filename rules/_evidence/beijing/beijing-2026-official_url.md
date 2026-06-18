# beijing-2026-official_url

> 对应规则: `BEIJING.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生须在规定的时间内登录北京教育考试院网站（www.bjeea.cn）进行志愿填报。"
> —— 出处: 《北京市2026年普通高等学校招生志愿填报须知》
> URL: https://www.bjeea.cn/html/gkgz/tzgg/2026/0614/88216.html
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
BEIJING.official_url:
  severity: info
  value:
    official_url: https://www.bjeea.cn/
  effective_date: '2026-01-01'
  source_evidence_id: beijing-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：该条仅校验北京 2026 志愿填报官方入口域名，不替代更细粒度的业务页面路径
- 例 2：样表附件、计划查询、选考查询等功能页仍可能挂在 `bjeea.cn` 下的不同子路径

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 北京教育考试院
- 复核负责人: 待指派
