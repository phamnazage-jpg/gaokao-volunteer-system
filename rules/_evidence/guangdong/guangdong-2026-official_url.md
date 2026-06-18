# guangdong-2026-official_url

> 对应规则: `GUANGDONG.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "广东省教育考试院"
> "主办单位：广东省教育考试院"
> —— 出处: 广东省教育考试院官网首页
> URL: https://eea.gd.gov.cn/
> 发布日期: 页面未标注

## 2. 转写为机读规则

```yaml
GUANGDONG.official_url:
  severity: info
  value:
    official_url: https://eea.gd.gov.cn/
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：`official_url` 固定为考试院官网主站根入口，不使用单篇通知页替代
- 例 2：当前站点已启用 HTTPS，truth 同步规范化为 `https://eea.gd.gov.cn/`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
