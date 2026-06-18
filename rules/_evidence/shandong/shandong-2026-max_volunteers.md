# shandong-2026-max_volunteers

> 对应规则: `SHANDONG.max_volunteers`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生每次填报志愿的数量最多不超过96个。"
> —— 出处: 《山东省2026年普通高等学校考试招生（夏季高考）工作实施办法》
> URL: https://www.sdzk.cn/NewsInfo.aspx?NewsID=7200 / https://www.sdzk.cn/Floadup/file/20260518/6391471212594395957059302.doc
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
SHANDONG.max_volunteers:
  severity: fatal
  value:
    max_volunteers: 96
  effective_date: '2026-01-01'
  source_evidence_id: shandong-2026-max_volunteers
  status: active
```

## 3. 关键边界与例外

- 例 1：96 个是常规批每次填报的上限，不是全部批次通用上限
- 例 2：本条与“1个志愿 = 1个专业（专业类）+学校”配套，避免把志愿单元误解成院校专业组

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 山东省教育招生考试院
- 复核负责人: 待指派
