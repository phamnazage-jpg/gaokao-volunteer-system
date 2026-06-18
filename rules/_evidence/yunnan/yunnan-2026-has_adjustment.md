# yunnan-2026-has_adjustment

> 对应规则: `YUNNAN.has_adjustment`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "每个院校专业组志愿设置10个专业志愿和1个专业服从院校调剂标志。"
>
> "在设置专业服从院校调剂标志的批次（段）录取时，当考生所填专业均已录满时，院校可依据考生填报的志愿是否服从专业志愿调剂情况进行专业调剂录取。"
> —— 出处: 《云南省2025年普通高校招生考试安排和录取工作实施方案》
> URL: https://www.ynzs.cn/html/content/7511.html
> 发布日期: 2025-01-23

## 2. 转写为机读规则

```yaml
YUNNAN.has_adjustment:
  severity: warning
  value:
    has_adjustment: true
  effective_date: '2026-01-01'
  source_evidence_id: yunnan-2026-has_adjustment
  status: active
```

## 3. 关键边界与例外

- 例 1：云南普通类批次显式提供 `专业服从院校调剂标志`，因此 `has_adjustment` 必须为 `true`
- 例 2：不是所有批次都一定发生调剂录取，但系统层需要识别“允许调剂”这一能力位

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 云南省招生考试院
- 复核负责人: 待指派
