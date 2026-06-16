# RULES_SOURCE_OF_TRUTH

最后更新: 2026-06-16
真相源: 本文件是"规则"维度的入口索引。
审计上下文: `docs/PROJECT_PLANNING_REALIGNMENT_2026-06-16.md`
设计上下文: `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §2

---

## 1. 范围

本文件收敛以下三类信息:

- 各省高考 2026 规则
- 全国通用规则
- 错误模式库

---

## 2. 当前真相源路径(Phase 1 之后)

| 类别         | 路径                                | 格式      | 写入方式                           |
| ------------ | ----------------------------------- | --------- | ---------------------------------- |
| 全国通用规则 | `rules/_truth/national.yaml`        | YAML      | 人工 PR + 自动校验                 |
| 省级规则     | `rules/_truth/province/<prov>.yaml` | YAML      | 人工 PR + 自动校验                 |
| 规则证据原文 | `rules/_evidence/<prov>/<file>`     | 抓取/摘录 | 人工收录                           |
| 错误模式库   | `rules/errors/ERRORS.md`            | Markdown  | 人工维护(短期保留)                 |
| 跨省索引     | `rules/provinces.md`                | Markdown  | 由 `data/rules/loader.py` 自动生成 |

---

## 3. 数据模型最小契约

```python
Rule:
  rule_id: str                  # e.g. HUNAN.max_volunteers
  scope: "national" | "province"
  province: str | None
  year: int
  title: str
  description: str
  severity: "fatal" | "critical" | "warning" | "info"
  value: dict                   # 机读字段,如 {"max_volunteers": 45}
  source_evidence_id: str       # 指向 rules/_evidence/<id>.md
  effective_date: date
  last_verified_at: datetime
  version: str
  status: "active" | "draft" | "deprecated"
```

---

## 4. 当前覆盖矩阵(写入本文件时为准)

| 省份   | 模式       | 文档宣称        | checker 实际   | 备注                           |
| ------ | ---------- | --------------- | -------------- | ------------------------------ |
| 湖南   | 院校专业组 | ✅              | ✅             | 详细规则见 province/hunan.yaml |
| 广东   | 院校专业组 | ✅              | ✅             |                                |
| 湖北   | 院校专业组 | ✅              | ✅             |                                |
| 安徽   | 院校专业组 | ✅              | ✅             |                                |
| 江西   | 院校专业组 | ✅              | ✅             |                                |
| 甘肃   | 院校专业组 | ✅              | ✅             |                                |
| 黑龙江 | 院校专业组 | ✅              | ✅             |                                |
| 江苏   | 院校专业组 | ✅              | ✅             |                                |
| 福建   | 院校专业组 | ✅              | ✅             |                                |
| 广西   | 院校专业组 | ✅              | ✅             |                                |
| 北京   | 院校专业组 | ✅              | ✅             |                                |
| 上海   | 院校专业组 | ✅              | ✅             |                                |
| 天津   | 院校专业组 | ✅              | ✅             |                                |
| 海南   | 院校专业组 | ✅              | ✅             |                                |
| 浙江   | 专业+学校  | ✅              | ✅             |                                |
| 山东   | 专业+学校  | ✅              | ✅             |                                |
| 河北   | 专业+学校  | ✅              | ✅             |                                |
| 重庆   | 专业+学校  | ✅              | ✅             |                                |
| 辽宁   | 专业+学校  | ✅              | ✅             |                                |
| 贵州   | 专业+学校  | ✅              | ✅             |                                |
| 青海   | 专业+学校  | ✅              | ✅             |                                |
| 吉林   | 专业+学校  | ✅              | ✅             |                                |
| 新疆   | 传统       | ✅              | ✅             |                                |
| 西藏   | 传统       | ✅              | ✅             |                                |
| 河南   | 传统       | ✅              | ✅             |                                |
| 四川   | 传统       | ✅              | ✅             |                                |
| 云南   | 传统       | ✅              | ✅             |                                |
| 山西   | 传统       | ❌(SKILL.md 漏) | ✅(checker 有) | SKILL.md frontmatter 漂移待修  |
| 陕西   | —          | ❌(SKILL.md 含) | ❌(checker 无) | checker 漂移待修               |

---

## 5. 文档漂移清单(已识别)

- D1: `rules/provinces.md` 描述 27 省,实际 28 省
- D2: `skills/gaokao-spec-checker/SKILL.md` 含山西漏陕西
- D3: 传统模式数 provinces.md 写 5,SKILL.md 写 6
- D4: 文档与代码都没有 source_evidence_id 链

---

## 6. Phase 1 必须收口

- 28 省全部有 `province/<prov>.yaml`
- 至少 1 条全国通用规则有 `national.yaml`
- 1-2 个规则有真实 `source_evidence_id` 链路(湖南优先)
- `gaokao-cli rules status` 可用

---

## 7. 验证脚本

```bash
# 规则台账
gaokao-cli rules status

# 单条规则解释
gaokao-cli rules explain --province 湖南 --rule-id HUNAN.max_volunteers

# 一致性自检
python3 -m data.rules.cli verify
```

---

**下一阶段**: Phase 1 实施,见 `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §11
