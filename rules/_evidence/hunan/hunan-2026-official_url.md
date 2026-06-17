# hunan-2026-official_url

> 对应规则: `HUNAN.official_url`
> 所属: 省级（信息型规则）
> 规则版本: `2026.1`
> 摘录时间: 2026-06-17
> 摘录人: Hermes Agent (主代理)

## 1. 官方原文摘录

> 湖南省教育考试院官方门户：
>
> - 主站: http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/
> - 政策文件栏目: http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/zcwj/
> - 招生录取查询: http://www.hneeb.cn/

## 2. 转写为机读规则

```yaml
HUNAN.official_url:
  severity: info
  value:
    official_url: http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/
  effective_date: 2026-01-01
  source_evidence_id: hunan-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：主站域名变更需在 `effective_date` 上同步更新
- 例 2：URL 不可用时降级到 archive.org 镜像

## 4. 后续维护

- 下次复核时间: 2027-01-01
- 复核来源: 域名 + URL 可达性
- 复核负责人: 待指派
