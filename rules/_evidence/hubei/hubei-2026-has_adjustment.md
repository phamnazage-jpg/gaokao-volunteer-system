# hubei-2026-has_adjustment

> 对应规则: `HUBEI.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "高考志愿设置将主要采用“院校专业组”方式。考生志愿由若干个“院校专业组”组成，每个“院校专业组”志愿内设若干个专业志愿和是否服从专业调剂志愿。"
> —— 出处: 《各批次志愿结构如何设置的？》
> URL: https://www.hbksw.com/info/41/1047.html
> 发布日期: 页面未标注（湖北省普通高校招生阳光招生问答公开页）

## 2. 转写为机读规则

```yaml
HUBEI.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: hubei-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：湖北是“有是否服从专业调剂选项”，不是“必调剂”；考生可以显式选择不服从
- 例 2：选择服从调剂只表示允许在该院校专业组内参与调剂，不代表可以跨组流转

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 湖北招生考试网 / 湖北省教育考试院
- 复核负责人: 待指派
