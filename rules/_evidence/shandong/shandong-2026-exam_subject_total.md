# shandong-2026-exam_subject_total

> 对应规则: `SHANDONG.exam_subject_total`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "总成绩为750分。"
> —— 出处: 《山东省2026年普通高等学校考试招生（夏季高考）工作实施办法》
> URL: https://www.sdzk.cn/NewsInfo.aspx?NewsID=7200 / https://www.sdzk.cn/Floadup/file/20260518/6391471212594395957059302.doc
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
SHANDONG.exam_subject_total:
  severity: info
  value:
    exam_subject_total: 750
  effective_date: '2026-01-01'
  source_evidence_id: shandong-2026-exam_subject_total
  status: active
```

## 3. 关键边界与例外

- 例 1：750 分对应夏季高考招生录取总成绩，不是单科满分
- 例 2：3 科统一高考科目原始分满分各 150 分，3 科等级考试科目原始分满分各 100 分，按等级分计入总成绩

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 山东省教育招生考试院
- 复核负责人: 待指派
