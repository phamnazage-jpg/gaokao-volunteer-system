# fujian-2026-official_url

> 对应规则: `FUJIAN.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "关于印发2026年福建省普通高等学校招生录取实施办法的通知"
> —— 出处: 福建省教育考试院官网首页
> URL: https://www.eeafj.cn/
> 发布日期: 2026-06-12

## 2. 转写为机读规则

```yaml
FUJIAN.official_url:
  severity: info
  value:
    official_url: https://www.eeafj.cn/
  effective_date: '2026-01-01'
  source_evidence_id: fujian-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：本条校验的是福建省教育考试院官方入口域名 `eeafj.cn`，不把具体公告页路径固化到 truth 层
- 例 2：首页公告列表可直接指向 2026 高招实施办法，因此 `https://www.eeafj.cn/` 仍可作为福建官方规则入口根地址

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 福建省教育考试院
- 复核负责人: 待指派
