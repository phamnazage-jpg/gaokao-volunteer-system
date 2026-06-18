# sichuan-2026-subject_mode

> 对应规则: `SICHUAN.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "我省普通高考实行“3+1+2”模式。"
>
> "其中，“3”为语文、数学、外语……3门全国统一考试科目；“1+2”为3门普通高中学业水平选择性考试科目，‘1’为首选科目……‘2’为再选科目……"
> —— 出处: 《四川省2026年普通高校招生实施规定》
> URL: http://www.sceea.cn/Html/202604/Newsdetail_4767.html
> 发布日期: 2026-04-21 / 2026-04-23 发布

## 2. 转写为机读规则

```yaml
SICHUAN.subject_mode:
  severity: warning
  value:
    subject_mode: 传统
  effective_date: '2026-01-01'
  source_evidence_id: sichuan-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：四川官方已直接写出 `3+1+2`，因此旧 truth 的 `传统` 口径已过时
- 例 2：`3+1+2` 只记录考试结构，不展开到具体外语语种或再选科目的全量清单

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 四川省教育考试院
- 复核负责人: 待指派
