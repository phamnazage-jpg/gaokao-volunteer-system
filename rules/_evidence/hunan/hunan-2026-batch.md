# hunan-2026-batch

> 对应规则: `HUNAN.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-17
> 摘录人: Hermes Agent (主代理)

## 1. 官方原文摘录

> "2026 年湖南省普通高校招生共设本科提前批、本科批、专科提前批、高职专科批四个批次。普通类本科批为院校专业组平行志愿。"
> —— 出处: 《湖南省 2026 年普通高校招生工作实施办法》
> URL: http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/

## 2. 转写为机读规则

```yaml
HUNAN.batch:
  severity: info
  value:
    batch: 本科批
  effective_date: 2026-01-01
  source_evidence_id: hunan-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：本科提前批在本科批之前投档，单独录取流程
- 例 2：本科批为本次审计引擎主战场（45 个院校专业组志愿位）

## 4. 后续维护

- 下次复核时间: 2026-09-01
- 复核来源: 湖南省教育考试院
- 复核负责人: 待指派
