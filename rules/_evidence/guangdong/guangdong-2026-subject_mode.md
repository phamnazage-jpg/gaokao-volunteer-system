# guangdong-2026-subject_mode

> 对应规则: `GUANGDONG.subject_mode`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "由 3 门全国统一高考考试科目和 3 门广东省普通高中学业水平选择性考试科目组成，实行“3+1+2”考试模式。"
> —— 出处: 《广东省普通高等学校招生工作规定》
> URL: https://eea.gd.gov.cn/tzgg/content/post_4896626.html / https://eea.gd.gov.cn/attachment/0/613/613821/4896626.pdf
> 发布日期: 2026-05-13

## 2. 转写为机读规则

```yaml
GUANGDONG.subject_mode:
  severity: warning
  value:
    subject_mode: 3+1+2
  effective_date: '2026-01-01'
  source_evidence_id: guangdong-2026-subject_mode
  status: active
```

## 3. 关键边界与例外

- 例 1：广东 2026 普通高考明确采用 `3+1+2` 模式，不是 3+3
- 例 2：艺体类考生在此基础上还要加考专业省统考，但不改变 `subject_mode` 主字段

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 广东省教育考试院
- 复核负责人: 待指派
