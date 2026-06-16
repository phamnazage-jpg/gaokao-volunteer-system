# DESIGN_RULES_TRUSTED_CLI_2026-06-16

最后更新: 2026-06-16
真相源: 本设计是 `docs/PROJECT_PLANNING_REALIGNMENT_2026-06-16.md` 审计结果的具体设计落点。
目标: 在不破坏现有 v2.1 已完成能力的前提下，把"规则可信化 / 专业目录可信化 / CLI 能力面 / 智能体调度 / 整体整合"一次性收敛到下一阶段实施级方案。

---

## 0. 阅读顺序

1. 本节
2. §1 总目标与边界
3. §2 规则规范可信化架构
4. §3 统一审计引擎
5. §4 专业目录数据真相源
6. §5 Application Services 层
7. §6 统一 CLI 命令面
8. §7 智能体能力调度层
9. §8 整体项目整合
10. §9 与现有 PRD/ROADMAP/规划的对接
11. §10 风险与验证
12. §11 实施阶段

---

## 1. 总目标与边界

### 1.1 解决什么

- 规则三处真相源不一致(2.1 审计)
- 规则无证据链(2.2)
- 专业目录无结构化真相源(2.3)
- CLI 不统一(2.5)
- 智能体无统一调度(2.6)
- 文档分层混乱(2.8)

### 1.2 不解决什么

- 真实支付 acceptance(外部条件阻塞,与本设计解耦)
- 现有 SKILL.md 内部对话风格(本设计不动 skill 角色,只把它们的"事实与执行"抽到 services + CLI)
- 短期内不可能做完的 27 省"规则自动化采集" — 留 Phase 2
- 完整 SaaS 化 UI 重构

### 1.3 关键设计原则

- **单一真相源**: 任何"权威数据"在系统中只允许有一个写入路径
- **可追溯**: 任何规则/数据都带来源、版本、更新时间
- **可分层调用**: 一份实现同时供 CLI / Hermes skill / HTTP / 智能体
- **可回归验证**: 每条新能力必须有可被 pytest 调用的最小 happy path + error path
- **不破坏现有 v2.1 入口**: admin/、data/orders/、data/payments/ 已收口,只新增层,不改既有契约

---

## 2. 规则规范可信化架构

### 2.1 四层模型

```
┌──────────────────────────────────────────────────────────┐
│ L1 规则证据层 (rules/_evidence/)                         │
│   官方文件 / 公告原文 / 抓取快照 / 摘录                  │
│   - 存储格式: evidence_id, source_url, fetched_at, ...   │
│   - 写入方式: 手动 + 校验脚本                            │
└────────────────────┬─────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────┐
│ L2 规则真相源层 (rules/_truth/)                          │
│   - national_rules.yaml  # 全国通用规则                  │
│   - province/<prov>.yaml # 各省 2026 规则                │
│   - 字段: rule_id, scope, severity, source_evidence_id, │
│           effective_date, version, status                │
└────────────────────┬─────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────┐
│ L3 规则聚合层 (data/rules/loader.py)                    │
│   - 加载 national + province 规则                        │
│   - 校验所有 source_evidence_id 都能在 L1 找到          │
│   - 对外暴露 get_rule(province, rule_id)                │
│   - 暴露 list_province_rules(province) 等枚举接口        │
└────────────────────┬─────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────┐
│ L4 规则应用层                                            │
│   - 统一审计引擎(data/rules/audit_engine.py)            │
│   - CLI `gaokao-cli rules`                              │
│   - HTTP API `/api/rules/...`                           │
│   - Hermes skill `gaokao-rules-doctor`                  │
└──────────────────────────────────────────────────────────┘
```

### 2.2 关键目录与文件

新增:

- `rules/_evidence/`
  - `README.md` — 收录规范
  - `hunan/2026-本科批-院校专业组.md` — 抓取/摘录
  - `hunan/2026-征集志愿.txt` — 原始公告
  - ...
- `rules/_truth/`
  - `national.yaml` — 全国通用规则(平行志愿、一次投档、退档机制等)
  - `province/<prov>.yaml` — 各省 2026 规则
- `data/rules/__init__.py`
- `data/rules/loader.py`
- `data/rules/audit_engine.py`
- `data/rules/models.py`
- `data/rules/tests/test_loader.py`
- `data/rules/tests/test_audit_engine.py`

保留并改造:

- `rules/provinces.md` → 改成自动生成索引, 由 `data/rules/loader.py` 输出
- `scripts/gaokao-checker` → 改为薄 wrapper, 内部调 `audit_engine.run()`

### 2.3 数据模型

```python
# data/rules/models.py

class RuleSeverity(str, Enum):
    FATAL = "fatal"
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class RuleScope(str, Enum):
    NATIONAL = "national"
    PROVINCE = "province"

class Rule:
    rule_id: str             # e.g. "HUNAN.max_volunteers"
    scope: RuleScope
    province: str | None     # 当 scope=province 时
    year: int                # 2026
    title: str
    description: str
    severity: RuleSeverity
    # 规则可机读形式,如 {"max_volunteers": 45}
    value: dict
    # 证据链
    source_evidence_id: str
    effective_date: date
    last_verified_at: datetime
    version: str             # "2026.1"
    status: str              # "active" | "draft" | "deprecated"

class AuditIssue:
    rule_id: str
    severity: RuleSeverity
    title: str
    message: str
    evidence_quote: str | None
    suggestion: str | None
```

### 2.4 与现有 PROVINCE_RULES 的迁移

迁移方式: 一次性脚本 `scripts/migrate_province_rules_to_truth.py`:

- 读 `scripts/gaokao-checker` 里的 `PROVINCE_RULES`
- 给每条记录生成 `source_evidence_id` 占位 + `last_verified_at = 2026-06-12`
- 输出 `rules/_truth/province/*.yaml`
- 保留 `gaokao-checker` 旧 API,但内部委托给 `audit_engine`

不破坏现有 27 省的覆盖。迁移后:

- `PROVINCE_RULES` 作为"过渡期镜像"保留
- 新代码只读 `data/rules/loader.py`
- 旧 skill 暂时继续用 `PROVINCE_RULES`,不影响线上

### 2.5 2026 规则更新流程

```
官方文件发布 (人)
    ↓
1. 抓取/摘录 -> rules/_evidence/<prov>/<date>.md
2. 更新 rules/_truth/province/<prov>.yaml
3. python3 -m data.rules.cli verify <prov>  # 自检 schema + 证据引用
4. pytest data/rules/tests/                # 跑回归
5. git commit -m "rules(<prov>): update 2026.2 ..."
6. 三仓推送
```

每月一次"规则刷新日"运行:

```bash
python3 -m data.rules.cli status
```

返回每个省的:

- 规则数量
- 最近验证时间
- 是否有未填 source_evidence_id
- 是否存在 active 状态但 last_verified_at > 90 天的规则

---

## 3. 统一审计引擎

### 3.1 接口设计

```python
# data/rules/audit_engine.py

class AuditEngine:
    def __init__(self, rule_loader: RuleLoader): ...

    def run(
        self,
        province: str,
        plan: VolunteerPlan,
        # 可选上下文: 选科 / 体检 / 投档历史
        context: AuditContext | None = None,
    ) -> AuditResult: ...

class AuditResult:
    province: str
    overall_pass: bool
    issues: list[AuditIssue]
    applied_rule_ids: list[str]
    evidence_chain: list[EvidenceRef]   # 用于报告里附"依据文件"
    schema_version: str
```

### 3.2 输入模型

```python
class VolunteerPlanItem:
    school_name: str
    school_code: str | None
    major_group_code: str | None
    major_names: list[str]
    subject_requirements: list[str] | None
    adjustment: bool | None    # 是否服从组内调剂
    reference_rank: int | None # 2025 年位次

class VolunteerPlan:
    province: str
    score: int | None
    rank: int | None
    subject_combo: str | None
    items: list[VolunteerPlanItem]
```

### 3.3 引擎内部分层

1. **Schema 校验** — 必填字段、字段类型
2. **全国通用规则检查** — 例如:
   - 平行志愿原则是否被违反
   - "一次投档"原则在文本中是否被描述正确
3. **省级规则检查** — 例如:
   - 志愿数是否在 max_volunteers 范围内
   - 是否使用了正确的"模式"术语
4. **数据完整性检查** — 例如:
   - 每个 item 必须有 reference_rank 或明确标注待官方公布
   - 院校代码与名称是否对得上
5. **风险评估** — 不在规则层,而是规则层之上,见 §3.4

### 3.4 与 `gaokao-spec-checker` / `gaokao-audit` 的关系

| 能力                      | 改造前                                               | 改造后                                                                |
| ------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------- |
| regex 规则检查            | `skills/gaokao-spec-checker/scripts/spec_checker.py` | 保留,改为薄 wrapper, 内部调 `audit_engine`                            |
| 完整审核(含扎堆/数据溯源) | `skills/gaokao-audit/scripts/audit_service.py`       | 保留,改为薄 wrapper, 内部调 `audit_engine` + crowd_db + major_catalog |
| 客服/智能体调用           | 直接 `import`                                        | 改为调 CLI 或 HTTP,不再依赖 Python 模块路径                           |

---

## 4. 专业目录数据真相源

### 4.1 必要性

用户原话:"最近两年各学校和国家机构取消和新增了很多专业,防止我们提供错误的专业"。

当前仓库:

- 没有教育部本科专业目录导入
- 没有高校招生专业目录导入
- 现有 `data/crowd_db/*.json` 只是"大厂AI 热门汇总",与官方目录不是同一回事
- 推荐/审核如果引用"已撤销专业"或"目录外专业名",系统不会报警

### 4.2 数据模型(两层)

#### L1 教育部本科专业目录

```python
# data/majors/models.py

class NationalMajor:
    code: str               # 教育部专业代码 e.g. "120201K"
    name: str               # 官方名称 e.g. "工商管理"
    discipline: str         # 学科门类 e.g. "管理学"
    category: str           # 专业类 e.g. "工商管理类"
    degree: str             # 授予学位 e.g. "管理学学士"
    is_directional: bool    # 是否国家控制布点专业
    status: str             # "active" | "renamed" | "merged" | "deprecated"
    year_added: int         # 首次列入目录年份
    year_removed: int | None
    notes: str | None
    source_url: str
    last_verified_at: datetime
```

#### L2 高校招生专业(招生章程)

```python
class SchoolMajorOffering:
    school_code: str
    school_name: str
    major_code: str          # 教育部专业代码
    major_name: str          # 学校招生目录名称
    admission_year: int
    province: str
    duration_years: int
    tuition_cny: int | None
    study_mode: str          # "全日制"
    is_new: bool             # 该校该年新增
    is_discontinued: bool    # 该校该年撤销/停招
    source: str
    last_verified_at: datetime
```

### 4.3 数据接入

#### 4.3.1 教育部本科专业目录(国家级)

- **优先级 1**: 教育部 2024 年发布《普通高等学校本科专业目录》
- **优先级 2**: 教育部学位中心公开数据
- **来源类型**:
  - 半自动抓取 + 人工校对(高优)
  - 用户/客服智能体可调 `gaokao-cli majors ingest <url>` 提交
- **落地格式**: `data/majors_catalog/national/{year}.json` + `latest.json` 软链
- **不做**:
  - 自动爬取(高风险/合规)
  - 把整个目录当自动真相源(目录有延迟,需要人工核对)

#### 4.3.2 高校招生专业(校级)

- **优先级 1**: 各高校招生章程(每年 5-7 月发布)
- **优先级 2**: 阳光高考平台公示
- **格式**: `data/majors_catalog/schools/{year}/{school_code}.json`
- **接入方式**:
  - 暂不做自动抓取
  - 维护一个 `schools_2026.csv` 入口清单(20-30 所主流校)
  - 每个文件加 `confidence` 字段和 `verified_by` 字段

### 4.4 在审计引擎里的使用

`audit_engine` 新增一个 `major_validation` 检查步骤:

- 输入 plan 里的 `major_names`
- 对每一条:
  - 查 `NationalMajor` 是否存在且 `status=active`
  - 如果不存在或已撤销,标 `FATAL` 错误
  - 如果 `is_new=true`(2024 之后新设),建议核查该专业是否真招
  - 给出 evidence: 教育部目录年份 + 国家专业代码

对学校专业组同理:

- 查 `SchoolMajorOffering` 是否在 2026 招生目录
- 标记 `is_discontinued` 的项

### 4.5 风险管理

- **不在审计/推荐里引用 2024 年前撤销的专业** — 默认行为
- **新设专业必须有 2024 之后的 evidence** — 默认行为
- **失败安全**: 如果某条 major 在 national catalog 找不到,只警告,不强阻断(因为可能有"新设尚未入库"的情况)
- **所有"找不到"必须留下"待人工确认"标签**

---

## 5. Application Services 层

### 5.1 为什么需要

现有调用方式:

- `skills/gaokao-counselor-long` 通过 `import skills.gaokao-audit.scripts.audit_service` 直接调
- `scripts/gaokao-order-manager` 通过 `import data.orders.cli` 直接调

问题:

- 调用方依赖服务方内部模块路径
- 没有事务边界、权限、日志
- 不能跨 Python 版本/虚拟环境复用

### 5.2 设计

新增 `gaokato/services/` 包,作为"业务门面"层:

```
gaokato/
├── services/
│   ├── __init__.py
│   ├── audit.py           # audit_plan(province, plan, ctx) -> AuditResult
│   ├── order.py           # create_order, get_order, list_orders, update_status
│   ├── plan.py            # generate_plan, validate_plan
│   ├── report.py          # render_report
│   ├── payment.py         # payment_doctor, ...
│   ├── majors.py          # lookup_major, validate_plan_majors
│   ├── rules.py           # list_province_rules, get_rule, status
│   └── delivery.py        # dispatch, watchdog
└── transport/
    ├── cli.py             # argparse / typer
    ├── http_client.py     # admin FastAPI 调用封装
    └── skill_adapter.py   # 给 hermes skill 用的稳定接口
```

### 5.3 与现有代码关系

- `data/orders/cli.py` 已有 `OrdersCLI`,把核心方法抽到 `gaokato.services.order`
- `skills/gaokao-audit/scripts/audit_service.py` 抽到 `gaokato.services.audit`
- `scripts/gaokao-checker` 改为调 `gaokato.services.audit.run(...)`
- 旧 skill 与旧 CLI 内部都委托给 services,保持外部契约

### 5.4 关键接口草案

```python
# gaokato/services/audit.py

def audit_plan(
    province: str,
    plan: VolunteerPlan | dict,
    *,
    include_crowd_check: bool = True,
    include_major_validation: bool = True,
    output_format: str = "structured",   # "structured" | "text" | "json"
) -> AuditResult: ...
```

```python
# gaokato/services/order.py

def create_order(
    service_code: str,            # "audit" | "standard" | "premium"
    customer_name: str,
    customer_contact: str,
    *,
    source: str = "agent-cli",
    actor: str | None = None,     # 谁触发的(留痕)
    dry_run: bool = False,
) -> Order: ...

def get_order(order_id: str) -> Order: ...
def list_orders(*, status: str | None = None, limit: int = 50) -> list[Order]: ...
def update_status(order_id: str, new_status: str, *, actor: str, note: str | None = None) -> Order: ...
```

```python
# gaokato/services/rules.py

def list_province_rules(province: str) -> list[Rule]: ...
def get_rule(province: str, rule_id: str) -> Rule: ...
def status(province: str | None = None) -> RulesStatus: ...
```

```python
# gaokato/services/majors.py

def lookup_major(name_or_code: str) -> NationalMajor | None: ...
def validate_plan_majors(plan: VolunteerPlan) -> list[AuditIssue]: ...
```

### 5.5 日志与权限

- 所有 service 调用强制写 `logs/gaokato_audit.log`(JSON Lines)
- 每条记录包含:
  - `ts`
  - `actor`
  - `action`
  - `args`(脱敏)
  - `result`(`ok` / `error`)
  - `duration_ms`
- 不在 services 层做"用户/角色"判断,留给上层:
  - CLI 入口用 `--actor`
  - HTTP API 用 JWT subject
  - Skill 用 skill 自身 caller

---

## 6. 统一 CLI 命令面

### 6.1 命令入口

`gaokao-cli` 单一入口,子命令分组:

```
gaokao-cli
├── audit
│   ├── run         # gaokato.services.audit.audit_plan
│   ├── explain     # 输出某条规则的解释与证据
│   └── list-rules  # 列出某省 2026 规则
├── order
│   ├── create
│   ├── get
│   ├── list
│   ├── update-status
│   └── export
├── plan
│   ├── generate
│   └── validate
├── report
│   ├── render
│   └── export-pdf
├── majors
│   ├── lookup
│   ├── validate
│   └── list-changes
├── rules
│   ├── status
│   ├── list
│   └── explain
├── payment
│   ├── doctor
│   └── status
├── delivery
│   ├── dispatch
│   ├── watchdog
│   └── status
├── channel
│   ├── fallback
│   └── status
├── backup
│   ├── snapshot
│   ├── verify
│   └── restore
└── retention
    ├── cleanup
    └── status
```

### 6.2 公共约定

- 所有命令支持:
  - `--json` 输出 JSON
  - `--actor <who>` 留痕
  - `--quiet` 仅退出码
- 退出码:
  - `0` 成功
  - `1` 业务错误
  - `2` 调用错误(参数/IO)
  - `3` 不可恢复(权限/数据完整性)
- 错误输出统一格式:
  ```json
  {"ok": false, "code": "E05099", "message": "...", "details": {...}}
  ```
- 长操作命令支持 `--watch`(简单轮询)
- 任何"写"操作支持 `--dry-run`

### 6.3 命令集详细

| 命令                  | 用途                           | 适用角色           |
| --------------------- | ------------------------------ | ------------------ |
| `audit run`           | 对一份方案做政策+专业+扎堆审核 | 客服/智能体/管理员 |
| `audit list-rules`    | 列某省 2026 规则               | 客服/智能体/管理员 |
| `audit explain`       | 解释某条规则的来源             | 客服/智能体        |
| `order create`        | 创建订单                       | 智能体/管理员      |
| `order get`           | 查询订单                       | 客服/智能体        |
| `order list`          | 列表                           | 客服/管理员        |
| `order update-status` | 推进状态                       | 管理员             |
| `order export`        | CSV 导出                       | 管理员             |
| `plan generate`       | 生成方案                       | 智能体             |
| `plan validate`       | 校验方案                       | 智能体             |
| `report render`       | 渲染报告                       | 智能体             |
| `report export-pdf`   | 导出 PDF                       | 智能体/管理员      |
| `majors lookup`       | 查专业                         | 客服/智能体        |
| `majors validate`     | 校验方案中所有专业             | 智能体             |
| `majors list-changes` | 列近两年专业增减               | 客服/智能体        |
| `rules status`        | 规则台账状态                   | 管理员             |
| `rules list`          | 规则列表                       | 管理员/客服        |
| `rules explain`       | 规则解释                       | 客服               |
| `payment doctor`      | 支付 provider 健康检查         | 管理员             |
| `payment status`      | 支付状态汇总                   | 管理员             |
| `delivery dispatch`   | 触发交付                       | 管理员/智能体      |
| `delivery watchdog`   | 跑一次 watchdog                | 管理员             |
| `channel fallback`    | 渠道兜底拉取                   | 管理员             |
| `backup snapshot`     | 备份                           | 管理员             |
| `backup verify`       | 校验备份                       | 管理员             |
| `backup restore`      | 恢复                           | 管理员             |
| `retention cleanup`   | 清理超期                       | 管理员             |
| `retention status`    | 状态                           | 管理员             |

### 6.4 实现位置

`gaokato/transport/cli.py` 用 `typer`(或 `argparse` 子解析),每个子命令对应一个 handler,内部委派 `gaokato.services.*`。

向后兼容:

- `scripts/gaokao-audit` 改成 `gaokao-cli audit run`
- `scripts/gaokao-order-manager` 改成 `gaokao-cli order ...`
- `scripts/gaokao-checker` 改成 `gaokao-cli audit run`
- 旧入口保留 3-6 个月作为 alias,带 deprecation warning

### 6.5 安装与发现

- `gaokao-cli` 在 `pyproject.toml` 注册 `console_scripts`
- `gaokao-cli --help` 输出命令树
- `gaokao-cli <group> --help` 输出子命令
- `gaokao-cli doctor` 自检: Python 版本、env、DB、规则可加载性

---

## 7. 智能体能力调度层

### 7.1 形态

不重写已有 skill(它们已经稳)。新增**能力注册表 + 调用层**:

```
gaokato/
├── capabilities/
│   ├── __init__.py
│   ├── registry.py        # 能力注册表
│   └── adapters/
│       ├── hermes.py      # 把能力导出为 hermes tool
│       └── skill.py       # 让 skill 通过 cli 调用
```

### 7.2 能力注册表

```python
# gaokato/capabilities/registry.py

class Capability:
    name: str
    description: str
    cli: str                         # "audit run" / "order create" ...
    schema: dict                     # JSON schema, 参数约束
    risk: str                        # "read" | "write" | "destructive"
    roles: list[str]                 # 哪些角色可调
    examples: list[dict]

REGISTRY: list[Capability] = [
    Capability(
        name="audit_plan",
        description="对一份志愿方案做政策/专业/扎堆四维审核",
        cli="gaokao-cli audit run --province <p> --plan <file>",
        schema={...},
        risk="read",
        roles=["agent", "operator", "admin"],
        examples=[...],
    ),
    ...
]
```

### 7.3 与 Hermes skill 的关系

- **现状**:
  - `gaokao-counselor-long` 靠 Python import 调 audit_service
  - 与目录结构耦合
- **目标**:
  - skill 内部 import `gaokato.services.audit` 而非 `skills.gaokao-audit.scripts.audit_service`
  - 不再走 Python import 调外部脚本,改用 `subprocess` 调 `gaokao-cli`
  - 这给"未来切到独立进程/HTTP"留好接口

### 7.4 与 admin HTTP 的关系

- 现有 `admin/routes/orders.py`、`admin/routes/cases.py` 等直接调 data 层的 DAO
- 改造路径:
  - `admin/routes/orders.py` 内部改为调 `gaokato.services.order.*`
  - HTTP 层不再直接读 `data/orders/*`
  - 这样:
    - CLI 与 admin 用同一份 service 实现
    - 未来后台 API 拆分不影响业务

### 7.5 与真实"志愿服务智能体"的关系

- 单一智能体 = 一个 role + 多个 capability
- 推荐形态:
  - 客服智能体: `audit_plan` + `order get` + `report render`
  - 运营智能体: `order create` + `order update-status` + `report render`
  - 志愿顾问智能体: `plan generate` + `plan validate` + `audit run`
  - 管理员智能体: 全集 + `payment doctor` + `backup verify`
- 智能体本身不实现业务,只编排 capability

---

## 8. 整体项目整合

### 8.1 真相源分层

```
CURRENT_STATE.md           # 项目总览 + 当前阶段
PROJECT_PLANNING_REALIGNMENT_2026-06-16.md  # 漂移审计(本轮新增)
RULES_SOURCE_OF_TRUTH.md  # 规则真相源索引(本轮新增)
MAJOR_DATA_SOURCE_OF_TRUTH.md  # 专业目录真相源索引(本轮新增)
CLI_API_MAPPING.md        # CLI/HTTP/skill 三层映射(本轮新增)
DESIGN_RULES_TRUSTED_CLI_2026-06-16.md  # 本设计
```

### 8.2 目录结构(终态)

```
/home/long/project/gaokao-volunteer-system/
├── admin/                 # 现有 FastAPI 后台
├── data/                  # 现有 data 域
├── skills/                # 现有 skill
├── scripts/               # 现有 scripts(逐步 thin wrapper)
├── gaokato/               # 【新增】应用服务 + transport + capability
│   ├── services/
│   ├── transport/
│   └── capabilities/
├── rules/                 # 【扩展】
│   ├── _evidence/         # 规则证据(原文/摘录)
│   ├── _truth/            # 规则真相源
│   │   ├── national.yaml
│   │   └── province/
│   ├── errors/
│   └── provinces.md       # 自动生成索引
├── data/majors_catalog/   # 【新增】专业目录真相源
│   ├── national/
│   └── schools/
└── docs/
    ├── CURRENT_STATE.md
    ├── PROJECT_PLANNING_REALIGNMENT_2026-06-16.md
    ├── RULES_SOURCE_OF_TRUTH.md
    ├── MAJOR_DATA_SOURCE_OF_TRUTH.md
    ├── CLI_API_MAPPING.md
    └── DESIGN_RULES_TRUSTED_CLI_2026-06-16.md
```

### 8.3 不会破坏的边界

- `admin/` 的现有路由契约不破坏
- `data/orders/`、`data/payments/` 的现有 DAO/Model 不破坏
- `skills/` 的现有 SKILL.md frontmatter 不破坏(只改内部 import)
- `scripts/gaokao-checker` 之类的旧入口 alias 保留 3-6 个月

### 8.4 数据流总图

```
外部输入 (用户/智能体/CLI/HTTP)
    ↓
统一入口(CLI / admin FastAPI / Hermes tool)
    ↓
gaokato.services.* (业务门面,带审计日志)
    ↓
    ├─→ data.rules.audit_engine  (规则层,读 rules/_truth)
    ├─→ data.majors_catalog      (专业目录)
    ├─→ data.crowd_db            (扎堆检测)
    ├─→ data.orders.dao          (订单)
    ├─→ data.payments.service    (支付)
    └─→ data.notifications       (通知)
    ↓
SQLite / 文件存储
```

---

## 9. 与现有 PRD / ROADMAP / 规划的对接

### 9.1 PRD 对接

- PRD 中"F020 AI 方案审核"标 ✅,实际本设计把它从"skill 内部能力"提升为"系统级 capability"
- PRD 中 F011 数据自动更新,本设计给出真实数据接入路径
- PRD 中 F015 智能推荐,本设计为其提供"可信数据底座"

### 9.2 ROADMAP 对接

- 2026 Q2 阶段:已闭合
- 2026 Q3 阶段建议插入:
  - **本设计是 2026 Q3 收口级工作**
  - 不与商业化目标冲突,反而是商业化的必要前置

### 9.3 IMPLEMENTATION_PLAN_v2 对接

- T1~T11 已完成,本设计是后续 T13 候选
- T12 用户端 Web 自助的下一阶段,需要本设计提供:
  - 规则可信化(否则 2026 高考季扛不住)
  - 专业目录可信化(否则推荐错误成本高)
  - CLI 能力面(否则客服/运营跟不上)

### 9.4 本设计与原 4 个优化目标对齐

| 目标              | 落到本设计的哪里 |
| ----------------- | ---------------- |
| 规则规范可信化    | §2 + §3          |
| 2026 专业目录     | §4               |
| CLI 能力层        | §5 + §6 + §7     |
| 整体规划/实现优化 | §8 + §9          |

---

## 10. 风险与验证

### 10.1 关键风险

- **R1**: 迁移 `PROVINCE_RULES` 时可能漏字段
  - 缓解: 一次性脚本 + 全量单元测试,确保 28 省全覆盖
- **R2**: 教育部专业目录与"高校招生目录"语义混淆
  - 缓解: §4.2 明确两层,分别建模
- **R3**: 客服/智能体依赖旧 Python 路径,新设计未落地前不能破坏
  - 缓解: §8.3 明确保留旧入口 3-6 个月
- **R4**: 全国通用规则抽象被过度设计
  - 缓解: Phase 1 只抽"已明确稳定的"全国规则,避免空想规则
- **R5**: 真实环境无 2026 规则原文
  - 缓解: Phase 1 接受"暂以 2025 已稳定规则 + 标注 last_verified_at"为基线
- **R6**: CLI 改名影响线上脚本
  - 缓解: 旧 entry 保留为 alias + deprecation warning

### 10.2 真实验收标准

每条 Phase 必须有:

1. **可运行入口**: `gaokao-cli <group> --help` 出树
2. **可执行 smoke**: `gaokao-cli audit run --province 湖南 --plan fixtures/sample.json` 返回结构化结果
3. **可回归测试**: `pytest gaokato/ data/rules/ data/majors_catalog/ -q` 全绿
4. **可读源码**: 服务层每个函数都有 docstring + 错误码
5. **可被智能体调用**: hermes skill `gaokato_capabilities.json` 列出全部 capability
6. **可被后台调用**: `admin/routes/` 全部委托给 `gaokato.services.*`

### 10.3 阶段验收检查点

每个 Phase 结束时必须:

- 跑 `bash scripts/dev-verify.sh`
- 跑 `gaokao-cli doctor`
- 跑 `gaokao-cli rules status`
- 跑 `gaokao-cli majors validate fixtures/sample.json`
- 三仓推送

---

## 11. 实施阶段

### Phase 1 — 规则真相源化(无破坏,低风险)

**目标**: 把"规则硬编码"升级为"可追溯规则"

任务:

1. 落 `rules/_truth/national.yaml` + `province/<prov>.yaml`(27 省)
2. 写迁移脚本 `scripts/migrate_province_rules_to_truth.py`
3. 落 `data/rules/loader.py` + `audit_engine.py` 最小可用版
4. 保留 `scripts/gaokao-checker` 与 SKILL 行为
5. 加测试: `data/rules/tests/test_loader.py` + `test_audit_engine.py`

验收:

- `gaokao-cli rules status` 可用
- `gaokao-cli audit run` 行为与旧 `gaokao-checker` 一致
- 27 省规则 100% 迁移

---

### Phase 2 — 统一审计引擎最小可用

任务:

1. `gaokato/services/audit.py` 抽核心
2. `gaokato/transport/cli.py` 注册 `gaokao-cli audit run/explain/list-rules`
3. `skills/gaokao-counselor-long` 内部改为调 service(或 CLI)
4. 旧 skill 行为不变

验收:

- `gaokao-cli audit run` + JSON 输出
- hermes skill 仍能调起同一能力

---

### Phase 3 — 专业目录接入(MVP)

任务:

1. 落 `data/majors_catalog/national/2024.json`(教育部最新)
2. 落 5-10 所重点高校 2025/2026 招生目录
3. `gaokato/services/majors.py`
4. `gaokato.services.audit` 接入 major_validation
5. `gaokao-cli majors lookup/validate/list-changes`

验收:

- 任意 plan 跑 `gaokao-cli majors validate` 可标出已撤销/新设专业
- 至少 1 个 e2e:大厂AI方案 → audit run → major validation 命中

---

### Phase 4 — 统一 CLI 命令面

任务:

1. 落 `gaokato/transport/cli.py` 全部子命令
2. 保留旧脚本 alias + deprecation warning
3. `gaokao-cli doctor` 自检
4. `gaokato/capabilities/registry.py` 全集

验收:

- 全部 25+ 子命令可用
- `gaokao-cli --help` 树清晰
- 所有 `--json` 行为一致

---

### Phase 5 — 智能体调度与 admin 整合

任务:

1. `admin/routes/*` 委托 `gaokato.services.*`
2. hermes skill `gaokato_capabilities.json` 导出
3. 至少 3 个 skill 角色(客服/运营/顾问)绑定 capability
4. 端到端跑通

验收:

- 客服智能体可"读方案 → 调 audit → 查 order → 出报告"
- 运营智能体可"创建订单 → 改状态 → 出报告"
- 顾问智能体可"生成方案 → 校验 → 出报告"

---

### Phase 6 — 文档/真相源索引收口

任务:

1. 落 `RULES_SOURCE_OF_TRUTH.md` `MAJOR_DATA_SOURCE_OF_TRUTH.md` `CLI_API_MAPPING.md`
2. `CURRENT_STATE.md` 更新指向本设计
3. `PROJECT_PLANNING_REALIGNMENT_2026-06-16.md` 标记已落地

验收:

- 任何入口文档(CURRENT_STATE / README / PROJECT_PLANNING_REALIGNMENT)不再有冲突

---

## 12. 一次性完成顺序

主代理按以下顺序继续执行(用户已批准继续):

1. **本设计落盘** ✅ (本文件)
2. **审计落盘** ✅ (`PROJECT_PLANNING_REALIGNMENT_2026-06-16.md`)
3. **三处真相源文档** → `RULES_SOURCE_OF_TRUTH.md` + `MAJOR_DATA_SOURCE_OF_TRUTH.md` + `CLI_API_MAPPING.md`
4. **整体规划对接** → 提交一次 docs-only commit + 三仓推送
5. **回主对话** → 报告本轮完成

下一轮(用户再"继续"):

- Phase 1 实施
- TDD 走 RED-GREEN
- 仍然按"生产级 + 三仓同步"标准

---

**版本**: v1.0  
**最后更新**: 2026-06-16  
**对应规划**: `docs/PROJECT_PLANNING_REALIGNMENT_2026-06-16.md`  
**后续执行**: 等待用户"继续"进入 Phase 1
