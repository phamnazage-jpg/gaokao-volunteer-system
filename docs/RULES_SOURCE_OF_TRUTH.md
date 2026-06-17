# RULES_SOURCE_OF_TRUTH

最后更新: 2026-06-17
真相源: 本文件是"规则"维度的入口索引。
设计上下文: `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §2
执行上下文: `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md` §1.1

---

## 1. 范围

本文件收敛以下四类信息:

- 国家级规则
- 省级规则
- 规则证据链
- 统一审计入口

---

## 2. 当前真相源路径

| 类别       | 路径                                       | 格式     | 写入方式                        |
| ---------- | ------------------------------------------ | -------- | ------------------------------- |
| 国家级规则 | `rules/_truth/national.yaml`               | YAML     | 人工摘录 + 官方文件校对         |
| 省级规则   | `rules/_truth/province/<slug>.yaml`        | YAML     | 人工摘录 + 招生考试院校对       |
| 规则证据层 | `rules/_evidence/<prov>/<year>-<topic>.md` | Markdown | 待补建（设计层 Phase 1.5 要求） |
| 旧规则字典 | `scripts/gaokao-checker` `PROVINCE_RULES`  | Python   | 过渡期镜像，已迁移到 \_truth    |
| 错误码字典 | `rules/errors/ERRORS.md`                   | Markdown | 人工维护                        |

### 2.1 当前已落地范围（2026-06-17）

- 已落地 `rules/_truth/national.yaml`（国家级）
- 已落地 `rules/_truth/province/<slug>.yaml`（27 省，2026 版）
- 已落地 `data/rules/loader.py` `RuleLoader.from_truth_root`
- 已落地 `data/rules/audit_engine.py` `AuditEngine`
- 已落地 `data/rules/cli.py` `rules {status,verify}`
- 已落地 `scripts/migrate_province_rules_to_truth.py`（从 `PROVINCE_RULES` 一次性迁移）
- 已落地 `tests/test_rules_truth_phase1.py` + `tests/test_rules_cli_phase1.py`（部分）

### 2.2 尚未落地

- `rules/_evidence/<prov>/<year>-<topic>.md`（证据层）— 设计层 Phase 1.5 要求；当前**未建**
- 逐省证据链审计报告 — 本轮 docs-only 收口后，下一阶段再启动
- 规则"最近验证时间 > 90 天"自动告警（设计层 §2.5）

---

## 3. 数据模型

### 3.1 Rule（`data/rules/models.py`）

```python
Rule:
  rule_id: str             # e.g. "HUNAN.max_volunteers"
  scope: "national" | "province"
  province: str | None     # 当 scope=province 时
  year: int                # 2026
  title: str
  description: str
  severity: "fatal" | "critical" | "warning" | "info"
  value: dict              # 规则可机读形式
  source_evidence_id: str  # 证据链引用
  effective_date: date
  last_verified_at: datetime
  version: str             # "2026.1"
  status: "active" | "draft" | "deprecated"
```

### 3.2 AuditIssue（`data/rules/models.py`）

```python
AuditIssue:
  rule_id: str
  severity: RuleSeverity
  title: str
  message: str
  evidence_quote: str | None
  suggestion: str | None
```

---

## 4. 接入策略

### 4.1 国家级

- **首选源**: 教育部 / 教育考试院公开规则文件
- **覆盖范围**: 平行志愿、一次投档、退档机制、体检要求等
- **接入节奏**: 年度全量 + 差异更新

### 4.2 省级

- **首选源**: 各省招生考试院/教育考试院 2026 招生工作通知
- **覆盖范围**: 27 省（与 `PROVINCE_RULES` 对齐）
- **接入节奏**: 月度差异更新

### 4.3 证据层

- **首选源**: 上述官方文件原文
- **存储格式**: Markdown 摘录 + 官方文件 URL
- **校验**: 每条规则必须能引用至少一个证据条目

---

## 5. 统一审计入口

- `gaokao-cli rules status --json` — 27 省 + national 状态摘要
- `gaokao-cli rules verify --json` — `national.yaml` + `province/` 完整性
- `gaokao-cli audit run --province <p> --plan <json> --truth-root <path> --catalog-root <path> --json` — 完整审计

---

## 6. 下一阶段（执行 Phase 1 收口后的 Batch 候选清单）

> 已在 Phase 1 / 1.5 中**完成**的事项不再列入"必须收口"清单。

- `rules/_evidence/<prov>/<year>-<topic>.md` 证据层补建 — **Batch 4 候选**
- 逐省证据链审计报告 — **Batch 4 候选**
- `gaokao-cli rules explain <rule_id>` 命令 — **Batch 4 候选**
- "最近验证时间 > 90 天"自动告警 — **Batch 4 候选**

---

## 7. 风险

- 证据层未建导致规则可信度依赖 yaml 自描述
- 旧 `PROVINCE_RULES` 字典与新 `_truth` 字典需要保持同步过渡
- 月度刷新流程目前依赖人工 cron，未与 `gaokao-cli rules status` 联动
