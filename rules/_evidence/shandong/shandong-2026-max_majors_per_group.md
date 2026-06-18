# shandong-2026-max_majors_per_group

> 对应规则: `SHANDONG.max_majors_per_group`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "1个“专业（专业类）+学校”为1个志愿。"
> —— 出处: 《山东省2026年普通高等学校考试招生（夏季高考）工作实施办法》
> URL: https://www.sdzk.cn/NewsInfo.aspx?NewsID=7200 / https://www.sdzk.cn/Floadup/file/20260518/6391471212594395957059302.doc
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
SHANDONG.max_majors_per_group:
  severity: warning
  value:
    max_majors_per_group: 1
  effective_date: '2026-01-01'
  source_evidence_id: shandong-2026-max_majors_per_group
  status: active
```

## 3. 关键边界与例外

- 例 1：山东常规批的最小志愿单位就是 1 个“专业（专业类）+学校”，因此机读值保持为 `1`
- 例 2：本规则不适用于提前批 A 类那类以学校为单位、且可附带多个专业志愿的批次

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 山东省教育招生考试院
- 复核负责人: 待指派
