# guizhou-2026-official_url

> 对应规则: `GUIZHOU.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "贵州省招生考试院"
>
> "负责普通高校和成人高校的招生、考试、录取工作及统筹中等职业教育招生工作。"
> —— 出处: 《贵州省招生考试院》站点首页 / 单位简介
> URL: https://zsksy.guizhou.gov.cn/
> 发布日期: 站点首页，无单独发布日期

## 2. 转写为机读规则

```yaml
GUIZHOU.official_url:
  severity: info
  value:
    official_url: https://zsksy.guizhou.gov.cn/
  effective_date: '2026-01-01'
  source_evidence_id: guizhou-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：项目层记录的是考试院门户根地址 `https://zsksy.guizhou.gov.cn/`，因为政策通知、征集志愿和报名问答均从该域名发布
- 例 2：具体业务系统如志愿填报平台 `gkks.eaagz.org.cn` 只是子系统入口，不替代考试院门户作为规则真相源主链接

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 贵州省招生考试院
- 复核负责人: 待指派
