# heilongjiang-2026-official_url

> 对应规则: `HEILONGJIANG.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生可登录黑龙江省招生考试院官方网站（https://www.hljea.org.cn）或黑龙江省招生考试信息港网站（https://www.lzk.hl.cn），点击页面“网报中心”栏目，选择“2026年黑龙江省高考网上填报志愿入口”，输入个人信息登录志愿填报系统。"
> —— 出处: 《2026年黑龙江省普通高校招生网上填报志愿考生须知》
> URL: https://www.lzk.hl.cn/gkpd/gkxx/202606/t20260617_19794.htm
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
HEILONGJIANG.official_url:
  severity: info
  value:
    official_url: https://www.lzk.hl.cn/
  effective_date: '2026-01-01'
  source_evidence_id: heilongjiang-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：黑龙江省招生考试院官方站与黑龙江省招生考试信息港同时被 2026 须知点名，当前规则使用更稳定、正文更完整的 `https://www.lzk.hl.cn/` 作为标准来源
- 例 2：如后续考试院统一迁移至 `hljea.org.cn` 且停用信息港，应同步改写机读链接

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 黑龙江省招生考试信息港
- 复核负责人: 待指派
