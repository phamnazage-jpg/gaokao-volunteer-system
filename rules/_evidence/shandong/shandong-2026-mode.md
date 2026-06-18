# shandong-2026-mode

> 对应规则: `SHANDONG.mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "均实行以“专业（专业类）+学校”为单位的平行志愿模式。"
> "1个“专业（专业类）+学校”为1个志愿。"
> —— 出处: 《山东省2026年普通高等学校考试招生（夏季高考）工作实施办法》
> URL: https://www.sdzk.cn/NewsInfo.aspx?NewsID=7200 / https://www.sdzk.cn/Floadup/file/20260518/6391471212594395957059302.doc
> 发布日期: 2026-05-18

## 2. 转写为机读规则

```yaml
SHANDONG.mode:
  severity: fatal
  value:
    mode: 专业+学校
  effective_date: '2026-01-01'
  source_evidence_id: shandong-2026-mode
  status: active
```

## 3. 关键边界与例外

- 例 1：这条规则只描述常规批主流程，艺术类提前批 A 类的“学校+专业”志愿模式不纳入本条
- 例 2：官方原文将单位写成“专业（专业类）+学校”，truth 统一归一化为 `专业+学校`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 山东省教育招生考试院
- 复核负责人: 待指派
