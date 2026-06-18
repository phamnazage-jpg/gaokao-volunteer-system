# beijing-2026-mode

> 对应规则: `BEIJING.mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "填报本科院校专业组须符合相应的选考科目要求。"
> —— 出处: 《北京市2026年普通高等学校招生志愿填报须知》
> URL: https://www.bjeea.cn/html/gkgz/tzgg/2026/0614/88216.html
> 发布日期: 2026-06-15
>
> "本科阶段的志愿填报与录取投档采用院校专业组方式。"
> —— 出处: 《本科普通批志愿填报政策早了解》
> URL: https://www.bjeea.cn/html/ksb/gaozhaozhuanban/2022/0330/81257.html
> 发布日期: 2022-03-30

## 2. 转写为机读规则

```yaml
BEIJING.mode:
  severity: fatal
  value:
    mode: 院校专业组
  effective_date: '2026-01-01'
  source_evidence_id: beijing-2026-mode
  status: active
```

## 3. 关键边界与例外

- 例 1：2026 年志愿填报须知给出的是当前招生季适用场景，直接说明北京统考本科志愿仍按院校专业组填报
- 例 2：院校专业组的制度性定义来自 2022 年北京考试报官方解读，用于补足“mode=院校专业组”的规则语义

## 4. 后续维护

- 下次复核时间: 2026-07-15
- 复核来源: 北京教育考试院 / 北京考试报
- 复核负责人: 待指派
