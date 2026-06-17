# hunan-2026-max_volunteers

> 对应规则: `HUNAN.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-17
> 摘录人: Hermes Agent (主代理)

## 1. 官方原文摘录

> "普通类本科批考生可填报 45 个院校专业组志愿，其中本科提前批可填报 20 个院校专业组志愿（分军事院校 / 非军事院校 / 公安院校 / 其他四类）。"
> —— 出处: 《湖南省 2026 年普通高校招生工作实施办法》第二章"志愿设置"
> URL: http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/

## 2. 转写为机读规则

```yaml
HUNAN.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 45
  effective_date: 2026-01-01
  source_evidence_id: hunan-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：本科提前批上限 20 个志愿位，与本科批分别占位，不可跨批混填
- 例 2：征集志愿次数为 2 次（详见 hunan-2026-collection_count）

## 4. 后续维护

- 下次复核时间: 2026-09-01
- 复核来源: 湖南省教育考试院
- 复核负责人: 待指派
