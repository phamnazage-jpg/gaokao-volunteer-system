# hubei-2026-official_url

> 对应规则: `HUBEI.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "湖北省教育考试院——首页"
> "主办单位：湖北省教育考试院"
> —— 出处: 湖北省教育考试院首页
> URL: https://www.hbea.edu.cn/
> 发布日期: 无（首页入口）

## 2. 转写为机读规则

```yaml
HUBEI.official_url:
  severity: info
  value:
    official_url: https://www.hbea.edu.cn/
  effective_date: '2026-01-01'
  source_evidence_id: hubei-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：本条只用于锁定湖北省教育考试院官方域名入口，不承担具体志愿规则字段解释
- 例 2：湖北招生考试网 `hbksw.com` 是教育厅主管、考试院主办的关联发布站，但项目中的 `official_url` 仍统一落考试院主域名

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 湖北省教育考试院首页
- 复核负责人: 待指派
