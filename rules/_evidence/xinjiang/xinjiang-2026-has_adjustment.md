# xinjiang-2026-has_adjustment

> 对应规则: `XINJIANG.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "进行以上操作后，系统会提示需要在“统招调剂”或“定向调剂”选项中选择“服从”或“不服从”。"
> —— 出处: 《2026年新疆高考志愿填报系统操作手册》
> URL: http://www.xjzk.gov.cn/upload/resources/file/2026/06/12/30062.pdf
> 发布日期: 2026-06-12

## 2. 转写为机读规则

```yaml
XINJIANG.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: xinjiang-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：新疆志愿系统明确存在“服从 / 不服从”选择，因此不能把主规则写成 `has_adjustment: false`
- 例 2：这里证的是系统存在调剂开关，不是在替具体某一高校承诺一定会执行调剂录取

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 新疆教育考试院
- 复核负责人: 待指派
