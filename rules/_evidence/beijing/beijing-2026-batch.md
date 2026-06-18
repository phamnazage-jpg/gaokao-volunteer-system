# beijing-2026-batch

> 对应规则: `BEIJING.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "统考考生填报本科提前批志愿、特殊类型招生志愿、本科普通批志愿。"
> —— 出处: 《北京市2026年普通高等学校招生志愿填报须知》
> URL: https://www.bjeea.cn/html/gkgz/tzgg/2026/0614/88216.html
> 发布日期: 2026-06-15

## 2. 转写为机读规则

```yaml
BEIJING.batch:
  severity: info
  value:
    batch: 本科批
  effective_date: '2026-01-01'
  source_evidence_id: beijing-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：该摘录直接证明北京 2026 统考志愿阶段存在“本科普通批”批次
- 例 2：同一时间段还包含本科提前批与特殊类型招生志愿，`BEIJING.batch` 只落普通本科批名称，不覆盖其它批次

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 北京教育考试院
- 复核负责人: 待指派
