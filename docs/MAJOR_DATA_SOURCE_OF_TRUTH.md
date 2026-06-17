# MAJOR_DATA_SOURCE_OF_TRUTH

最后更新: 2026-06-17
真相源: 本文件是"专业目录"维度的入口索引。
审计上下文: `docs/PROJECT_PLANNING_REALIGNMENT_2026-06-16.md` §2.3-2.4
设计上下文: `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §4
执行上下文: `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md` §1.2-§1.4

---

## 1. 范围

本文件收敛以下两类信息:

- 教育部本科专业目录(国家级)
- 高校招生专业目录(校级)

---

## 2. 当前真相源路径

| 类别            | 路径                                                    | 格式     | 写入方式                  |
| --------------- | ------------------------------------------------------- | -------- | ------------------------- |
| 国家级专业目录  | `data/majors_catalog/national/<year>.json`              | JSON     | 半自动抓取 + 人工校对     |
| 国家级当前      | `data/majors_catalog/national/latest.json`              | JSON     | 当前先用同内容副本锁定    |
| 校级招生专业    | `data/majors_catalog/schools/<year>/<school_code>.json` | JSON     | 人工为主,来源高校招生章程 |
| 元数据          | `data/majors_catalog/METADATA.md`                       | Markdown | 人工维护                  |
| 已撤销/新设清单 | `data/majors_catalog/changes/2024-2026.md`              | Markdown | 人工维护                  |

### 2.1 当前已落地范围（2026-06-17）

执行 Phase 2 三个 Batch 全部收口：

- 已落地 `data/majors_catalog/` 包与 national loader/CLI（Batch 1）
- 已落地 `national/2024.json` + `national/latest.json`（13 个 curated subset, `coverage_mode=mvp_subset`）（Batch 1）
- 已新增 `schools/2026/10001.json` 校级招生目录骨架样本（**当前仅 1 所样本**，未扩面）（Batch 2）
- 已落地 `major_validation` 接入 `audit_engine`（Batch 3）
- 已新增 CLI 子命令：
  - `gaokao-cli majors {status,lookup,verify,changes}`（Batch 1）
  - `gaokao-cli majors {school-status,school-verify --year}`（Batch 2）
  - `gaokao-cli audit run --province --plan --truth-root --catalog-root --json` 命中 `MAJORS.not_found` / `MAJORS.non_active`（Batch 3）
- 提交链：`36ad58a` → `6b1157f` → `edc5b11`，三仓同步

### 2.2 尚未落地

- 更多学校 `schools/<year>/` 批量目录（仅 1 所样本）
- `changes/2024-2026.md`
- 国家层第二批扩面（>13 个专业）
- 国家层 2026 版（当前是 2024 版快照）

---

## 3. 两层数据模型

### 3.1 国家级(NationalMajor)

```python
NationalMajor:
  code: str                     # 教育部专业代码, e.g. "120201K"
  name: str                     # 官方名称, e.g. "工商管理"
  discipline: str               # 学科门类
  category: str                 # 专业类
  degree: str                   # 授予学位
  is_directional: bool          # 国家控制布点专业
  status: "active" | "renamed" | "merged" | "deprecated"
  year_added: int
  year_removed: int | None
  notes: str | None
  source_url: str
  last_verified_at: datetime
```

### 3.2 校级(SchoolMajorOffering)

```python
SchoolMajorOffering:
  school_code: str
  school_name: str
  major_code: str
  major_name: str
  admission_year: int
  province: str
  duration_years: int
  tuition_cny: int | None
  study_mode: str
  is_new: bool
  is_discontinued: bool
  source: str
  last_verified_at: datetime
```

> **当前落地情况**：校级骨架 `schools/2026/10001.json` 1 所样本；其余待 Batch 4 扩面。

---

## 4. 接入策略

### 4.1 国家级

- **首选源**: 教育部 2024 年《普通高等学校本科专业目录》
- **兜底源**: 阳光高考/学位中心
- **抓取方式**: 不自动爬取,使用人工收录 + 摘录
- **校验**: `python3 scripts/gaokao-cli majors verify --json`

### 4.2 校级

- **首选源**: 各高校 2025/2026 招生章程
- **覆盖范围**: 首批 5-10 所重点高校
- **接入节奏**: 每所高校每年一次,5 月前完成
- **校验**: `python3 scripts/gaokao-cli majors school-verify --year <year> --json`

---

## 5. 审计引擎集成

`AuditEngine.audit_plan` 新增 `major_validation` 一步：

- 命中 `MAJORS.not_found`（专业未在国家级目录中找到）
- 命中 `MAJORS.non_active`（专业已撤销/合并/改名）

详细见 `tests/test_audit_engine_major_validation_phase2.py`。

---

## 6. 下一阶段（执行 Phase 2 收口后的 Batch 4 候选清单）

> 已在 Batch 1/2/3 中**完成**的事项不再列入"必须收口"清单。

- 国家层扩面（>13 个专业）— **Batch 4 候选**
- 校级扩面（>1 所学校）— **Batch 4 候选**
- `changes/2024-2026.md` — **Batch 4 候选**
- 国家层 2026 版快照（当前为 2024 版）— **Batch 4 候选**

---

## 7. 风险

- 国家级目录与校级目录语义混淆
- 教育部新设专业不进入旧目录(2024 之后新设)
- 跨年招生章程口径不一致
- 当前 13 个 curated subset 不应被误读为完整教育部目录
