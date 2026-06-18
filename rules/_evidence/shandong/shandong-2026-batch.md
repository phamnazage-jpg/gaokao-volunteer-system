# shandong-2026-batch

> 对应规则: `SHANDONG.batch`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "普通类分为提前批和常规批两个录取批次。"
> "常规批。包括教育部高校专项计划、地方专项计划以及未列入提前批的其他本、专科招生。"
> —— 出处: 《山东省2026年普通高等学校考试招生（夏季高考）工作实施办法》
> URL: https://www.sdzk.cn/NewsInfo.aspx?NewsID=7200 / https://www.sdzk.cn/Floadup/file/20260518/6391471212594395957059302.doc
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
SHANDONG.batch:
  severity: info
  value:
    batch: 普通批
  effective_date: '2026-01-01'
  source_evidence_id: shandong-2026-batch
  status: active
```

## 3. 关键边界与例外

- 例 1：官方原文写的是“常规批”，truth 归一化为便于跨省对比的“普通批”
- 例 2：本条只描述夏季高考普通类主流程，不覆盖提前批 A/B 类和艺术类、体育类的其它批次名称

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 山东省教育招生考试院
- 复核负责人: 待指派
