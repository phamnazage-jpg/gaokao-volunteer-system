# MAJOR_DATA_SOURCE_OF_TRUTH

最后更新: 2026-06-16
真相源: 本文件是"专业目录"维度的入口索引。
审计上下文: `docs/PROJECT_PLANNING_REALIGNMENT_2026-06-16.md` §2.3-2.4
设计上下文: `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §4

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
| 国家级当前      | `data/majors_catalog/national/latest.json`              | JSON     | 软链或生成时锁定          |
| 校级招生专业    | `data/majors_catalog/schools/<year>/<school_code>.json` | JSON     | 人工为主,来源高校招生章程 |
| 元数据          | `data/majors_catalog/METADATA.md`                       | Markdown | 人工维护                  |
| 已撤销/新设清单 | `data/majors_catalog/changes/2024-2026.md`              | Markdown | 人工维护                  |

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

---

## 4. 接入策略

### 4.1 国家级

- **首选源**: 教育部 2024 年《普通高等学校本科专业目录》
- **兜底源**: 阳光高考/学位中心
- **抓取方式**: 不自动爬取,使用人工收录 + 摘录
- **校验**: `python3 -m data.majors_catalog.cli verify national`

### 4.2 校级

- **首选源**: 各高校 2025/2026 招生章程
- **覆盖范围**: 首批 5-10 所重点高校
- **接入节奏**: 每所高校每年一次,5 月前完成
- **校验**: `python3 -m data.majors_catalog.cli verify school <code>`

---

## 5. 审计引擎集成

`audit_engine.run` 接收 plan,新增一步:

```python
def _validate_majors(plan: VolunteerPlan) -> list[AuditIssue]:
    issues = []
    for item in plan.items:
        for major_name in item.major_names:
            major = majors_catalog.lookup(major_name)
            if major is None:
                issues.append(AuditIssue(
                    rule_id="MAJORS.not_found",
                    severity=RuleSeverity.WARNING,
                    title=f"专业未在国家级目录中找到: {major_name}",
                    suggestion="请人工核对",
                ))
            elif major.status != "active":
                issues.append(AuditIssue(
                    rule_id="MAJORS.deprecated",
                    severity=RuleSeverity.CRITICAL,
                    title=f"专业已撤销/合并/改名: {major.name}",
                    evidence_quote=f"{major.year_removed} 年已 {major.status}",
                ))
    return issues
```

---

## 6. Phase 3 必须收口

- `data/majors_catalog/national/2024.json` 落地,500+ 专业覆盖
- 5+ 重点高校 2025/2026 招生目录落地
- `gaokao-cli majors lookup/validate` 可用
- 1+ 真实 e2e:大厂AI方案跑 audit run 命中 major 验证

---

## 7. 风险

- 国家级目录与校级目录语义混淆
- 教育部新设专业不进入旧目录(2024 之后新设)
- 跨年招生章程口径不一致

---

**下一阶段**: Phase 3 实施,见 `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §11
