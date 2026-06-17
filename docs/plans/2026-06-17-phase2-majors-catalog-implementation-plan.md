# Phase2 专业目录真相源 Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task when tasks become independent enough; for the first batch, controller can implement directly because the repo currently has zero `data/majors*` code and the architecture needs one coherent landing.

**Goal:** 为 gaokao-volunteer-system 落地“2026 官方专业目录”最小可用真相源，使系统首次具备国家级专业目录的结构化读取、查询、校验与 CLI 能力，并为后续 school offering / audit integration 铺路。

**Architecture:** 先做国家级目录 MVP，不直接碰校级目录抓取和复杂 audit 集成。第一批只落 `data/majors_catalog/` 域模型 + loader + CLI + fixture 数据 + 测试，把“有真相源、可查询、可校验、可回归”闭环跑通。第二批再接 school offering 与 audit_engine major_validation。

**Tech Stack:** Python 3.11, pytest, mypy, ruff, JSON 数据文件, 现有 `scripts/gaokao-cli` 入口。

---

## 0. 当前真相与阶段口径

- `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` 把“专业目录接入(MVP)”写在 **Phase 3**。
- 当前用户已明确授权“Phase1 完成后继续下一阶段”，当前 active execution 将“专业目录真相源”作为**现在执行的 Phase2**。
- 因此本计划采用 **当前执行口径优先**：
  - **Phase2（当前执行）= 专业目录真相源 MVP**
  - 后续 CLI 全量面 / services 全量抽象仍按大设计分阶段推进

这不是改历史设计，而是把当前执行真相显式写清，防止后续再次出现 Phase2/Phase3 命名漂移。

---

## 1. 本批次范围（必须完成）

### 1.1 必做

1. 新增 `data/majors_catalog/` 包
2. 落国家级专业目录数据文件：
   - `data/majors_catalog/national/2024.json`
   - `data/majors_catalog/national/latest.json`
3. 落数据模型：`NationalMajor`
4. 落 loader / repository：
   - 读取 national latest
   - 支持按 code / name 查询
   - 支持列出状态统计
5. 扩展 `data/rules/cli.py` / `scripts/gaokao-cli`：
   - `gaokao-cli majors status --json`
   - `gaokao-cli majors lookup <name-or-code> --json`
   - `gaokao-cli majors verify --json`
6. 回归测试 + mypy/ruff + 全量门禁
7. commit + 三仓 push

### 1.2 明确不做

1. 不做自动抓取教育部网站
2. 不做高校招生目录批量采集
3. 不做 admin 路由改造
4. 不做 `gaokato/services/majors.py` 全量服务层
5. 不做 audit_engine 正式接入 `major_validation`

---

## 2. 文件落点

### 2.1 新增文件

- `data/majors_catalog/__init__.py`
- `data/majors_catalog/models.py`
- `data/majors_catalog/loader.py`
- `data/majors_catalog/cli.py`
- `data/majors_catalog/national/2024.json`
- `data/majors_catalog/national/latest.json`
- `data/majors_catalog/METADATA.md`
- `tests/test_majors_catalog_phase2.py`
- `tests/test_majors_cli_phase2.py`

### 2.2 修改文件

- `data/rules/cli.py`（挂 majors 子命令，或抽到共享入口）
- `scripts/gaokao-cli`
- `docs/MAJOR_DATA_SOURCE_OF_TRUTH.md`（补“当前已落地范围”）
- `docs/CURRENT_STATE.md`（Phase2 开始后再同步）

---

## 3. 数据契约（第一批）

### 3.1 NationalMajor

```python
@dataclass(frozen=True)
class NationalMajor:
    code: str
    name: str
    discipline: str
    category: str
    degree: str
    is_directional: bool
    status: str
    year_added: int
    year_removed: int | None
    notes: str | None
    source_url: str
    last_verified_at: str
```

### 3.2 `2024.json` 顶层结构

```json
{
  "year": 2024,
  "version": "2024.1",
  "source": "教育部普通高等学校本科专业目录（人工摘录校对）",
  "source_url": "https://www.moe.gov.cn/",
  "last_verified_at": "2026-06-17",
  "majors": [
    {
      "code": "020101",
      "name": "经济学",
      "discipline": "经济学",
      "category": "经济学类",
      "degree": "经济学学士",
      "is_directional": false,
      "status": "active",
      "year_added": 1998,
      "year_removed": null,
      "notes": null
    }
  ]
}
```

### 3.3 第一批数据策略

- 第一批不是一次性灌入 500+ 专业全集
- 先落 **可验证 MVP 子集**（建议 12-20 条，覆盖：经济学、法学、教育学、文学、理学、工学、医学、管理学、艺术学等）
- 同时在 `METADATA.md` 明确：
  - 当前是 `MVP curated subset`
  - 不是完整教育部目录
  - 未命中默认返回 `not found`，且后续会扩充

这样做的原因：

- 当前目标是 Phase2 真相源架构闭环，不是一次性完成全国全集录入
- 避免人为大规模录入带来新的不可校验证据漂移

---

## 4. 验收标准

### 4.1 Focused

- `pytest tests/test_majors_catalog_phase2.py tests/test_majors_cli_phase2.py -q` 全绿

### 4.2 CLI Smoke

- `python scripts/gaokao-cli majors status --json`
- `python scripts/gaokao-cli majors lookup 经济学 --json`
- `python scripts/gaokao-cli majors lookup 020101 --json`
- `python scripts/gaokao-cli majors verify --json`

### 4.3 Full Gate

- `bash scripts/dev-verify.sh --skip-pre-existing`

### 4.4 Git Delivery

- commit
- `git push gitea main && git push origin main && git push tksea main`

---

## 5. Batch 拆分

### Batch 1 — 国家级专业目录 MVP

- 模型
- loader
- curated subset 数据
- CLI status/lookup/verify
- 测试与门禁

### Batch 2 — 学校招生专业目录骨架

- `SchoolMajorOffering`
- schools 目录结构
- verify school catalog
- 仍不接正式抓取

### Batch 3 — 审计引擎接入

- `major_validation`
- plan major lookup
- deprecated / renamed / missing 的 issue 输出

---

## 6. 风险

1. **阶段命名漂移**
   - 缓解：本计划顶部显式说明“当前执行口径优先”
2. **MVP 子集被误当成完整目录**
   - 缓解：`METADATA.md` + CLI status 明确输出 `coverage_mode: mvp_subset`
3. **未来 school offering 与 national catalog 语义混淆**
   - 缓解：第一批只做 national，目录层级强分离

---

## 7. 当前执行顺序

1. 先实现 Batch 1（controller 直接做）
2. 跑 focused tests
3. 跑 CLI smoke
4. 跑全量门禁
5. 文档同步
6. commit + 三仓 push
