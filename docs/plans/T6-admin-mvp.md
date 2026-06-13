# T6 管理后台 MVP — 详细设计

**状态**: v2.1 实施设计
**最后更新**: 2026-06-12
**关联文档**: [IMPLEMENTATION_PLAN_v2.md](../IMPLEMENTATION_PLAN_v2.md), [TECH_ARCHITECTURE.md](../TECH_ARCHITECTURE.md)
**关联任务**: T6.1 FastAPI 后端基础 / T6.2 仪表盘 / T6.3 用户管理 / T6.4 订单管理 / T6.5 案例管理 / T6.6 简易 WebUI / T6.7 Docker 部署

---

## 1. 设计目标

### 1.1 总目标

为运营人员提供一个最小可用的 Web 管理后台，承接订单/用户/案例/审核报告的核心 CRUD + 统计展示，覆盖 2026 高考季（6/25-7/5）的运营需求。

### 1.2 非目标

- ❌ 复杂 RBAC 权限体系（MVP 用 admin 单一角色，后续 T8 扩展）
- ❌ 重前端（Vue/React）—— 走 ECharts + 纯 HTML/JS（v2.1 不引前端框架）
- ❌ 高并发/集群部署 —— 用户基数小（目标 100+ 考生），单机 SQLite 足够
- ❌ 完整 OpenAPI 兼容性 —— 自动 Swagger 文档即可

### 1.3 关键原则

| 原则                | 说明                                                                  |
| ------------------- | --------------------------------------------------------------------- |
| **本地优先**        | 默认本地 SQLite，云端可选                                             |
| **零侵入宿主**      | 不依赖外部子项目，仅调用本项目 `data/orders/` 已实现层                |
| **测试优先**        | 每个路由有 test client 测试；覆盖率目标 >= 70%                        |
| **最小风险闭环**    | T6.1 只做骨架（启动+路由+JWT+Swagger），业务路由在 T6.2-T6.5 增量实现 |
| **明文/加密分字段** | API 层明文接收，落盘前调用 T4.1 加密层                                |

---

## 2. 技术选型（v2.1 决策）

| 维度        | 选择                         | 理由                                              |
| ----------- | ---------------------------- | ------------------------------------------------- |
| Web 框架    | **FastAPI 0.133**            | 自动 OpenAPI、依赖注入、类型驱动                  |
| ASGI 服务器 | **uvicorn 0.41**             | 标配 FastAPI 部署                                 |
| 认证        | **PyJWT 2.13 (HS256)**       | 标准 JWT，密钥从环境变量读取                      |
| ORM         | **不使用 SQLAlchemy**        | 保持项目"零运行时第三方"约束；用 stdlib `sqlite3` |
| Pydantic    | **Pydantic v2.13**           | FastAPI 强依赖；用 BaseModel 做请求/响应模型      |
| 密码哈希    | stdlib `hashlib.pbkdf2_hmac` | 不引 bcrypt/argon2（MVP 简化）                    |
| 测试        | pytest + httpx TestClient    | httpx 0.28 已装                                   |

**为什么不用 SQLAlchemy**:项目 README/requirements-dev.txt 明确"运行时本项目为纯标准库实现,无第三方运行时依赖"。T4.1 已用 stdlib `sqlite3` + 自写 dataclass。引入 SQLAlchemy 会破坏这个约束。DAO 层用 `sqlite3` + `dataclass` 即可覆盖 CRUD。

---

## 3. 模块结构

```
admin/
├── __init__.py             # 模块导出
├── app.py                  # FastAPI app 工厂 (create_app)
├── config.py               # 配置加载（环境变量 + .env 兜底）
├── db.py                   # SQLite 连接管理 + DAO 工厂
├── auth.py                 # JWT 签发/校验/依赖
├── password.py             # PBKDF2 哈希
├── routes/
│   ├── __init__.py
│   ├── health.py           # GET /health (公开)
│   ├── auth.py             # POST /api/auth/login, GET /api/auth/me
│   ├── orders.py           # T6.4 订单管理（列表/详情/录单/PATCH/导出）
│   ├── stats.py            # GET /api/stats/orders (骨架,T6.2 完善)
│   └── meta.py             # GET /api/meta (province 列等)
└── tests/
    ├── __init__.py
    ├── conftest.py         # FastAPI TestClient + 内存 SQLite fixture
    ├── test_app.py         # app 启动 + Swagger 可达
    ├── test_auth.py        # JWT 签发/校验 + 401 路径
    ├── test_routes_health.py
    ├── test_routes_auth.py
    └── test_routes_orders.py
```

### 3.1 顶层路由（v2.1 MVP 阶段）

| 方法  | 路径                 | 鉴权 | 说明                           | 阶段 |
| ----- | -------------------- | ---- | ------------------------------ | ---- |
| GET   | `/health`            | 公开 | 健康检查（DB + 版本）          | T6.1 |
| GET   | `/docs`              | 公开 | Swagger UI（FastAPI 自动）     | T6.1 |
| GET   | `/openapi.json`      | 公开 | OpenAPI Schema                 | T6.1 |
| POST  | `/api/auth/login`    | 公开 | 用户名+密码 → JWT              | T6.1 |
| GET   | `/api/auth/me`       | JWT  | 当前用户信息                   | T6.1 |
| GET   | `/api/orders`        | JWT  | 订单列表（真实 DAO + 脱敏）    | T6.4 |
| GET   | `/api/orders/export` | JWT  | CSV 导出（默认脱敏）           | T6.4 |
| GET   | `/api/orders/{id}`   | JWT  | 订单详情 + 状态历史            | T6.4 |
| POST  | `/api/orders`        | JWT  | 手工录单（external_id 可空）   | T6.4 |
| PATCH | `/api/orders/{id}`   | JWT  | 业务字段更新 / 状态流转 / 退款 | T6.4 |
| GET   | `/api/stats/orders`  | JWT  | 订单统计（占位,空对象）        | T6.1 |
| GET   | `/api/meta`          | JWT  | 元数据（省份列等）             | T6.1 |

> T6.2 / T6.3 / T6.4 已分别落地仪表盘、用户管理与订单管理；后续剩余案例 CRUD、登录页 + 列表页等增量任务。

---

## 4. 数据模型

### 4.1 复用 T4.1

- `data/orders/models.py::Order` — 订单 dataclass
- `data/orders/schema.py::apply_schema` — DDL
- `data/orders/crypto.py::encrypt/decrypt/hash_for_index` — 字段加密
- `data/orders/state_machine.py::OrderStatus` — 6 态枚举

### 4.2 新增：admin_users 表（T6.1 引入）

```sql
CREATE TABLE IF NOT EXISTS admin_users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,      -- 存储格式: <salt_hex>$<pbkdf2_hash_hex>
    role            TEXT NOT NULL DEFAULT 'admin',  -- 后续 T8 RBAC 扩展
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    last_login_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
```

### 4.3 决策点

- **只允许单 admin?** ❌ — 支持多账户（运营多人轮班）
- **密码存储?** PBKDF2-HMAC-SHA256, 200k 迭代, 16B salt → 64B hash
- **默认账户?** 启动时若 `admin_users` 为空,自动创建 `admin/admin123`,并在日志 WARN 提示修改

---

## 5. JWT 设计

### 5.1 Token 结构（HS256）

```json
{
  "sub": "admin:1", // 用户标识
  "username": "admin",
  "role": "admin",
  "iat": 1718172800,
  "exp": 1718176400 // 默认 1 小时
}
```

### 5.2 配置

| 环境变量             | 默认值                       | 说明                |
| -------------------- | ---------------------------- | ------------------- |
| `GAOKAO_JWT_SECRET`  | dev-only 占位（启动时 WARN） | HS256 密钥（>=32B） |
| `GAOKAO_JWT_EXP_MIN` | 60                           | 过期时间（分钟）    |
| `GAOKAO_DB_PATH`     | `data/orders/admin.db`       | SQLite 路径         |
| `GAOKAO_ENV`         | `dev`                        | dev/prod 标识       |

> **安全警告**:生产部署必须显式设置 `GAOKAO_JWT_SECRET` 为高熵随机值。MVP 阶段在 `dev` 环境用占位即可,但启动日志必须明显提示。

### 5.3 中间件行为

- 请求带 `Authorization: Bearer <token>` → 解析 token,设置 `request.state.user`
- 无 token / 过期 / 签名错 → 返回 401 `WWW-Authenticate: Bearer`
- 受保护路由通过 `Depends(get_current_user)` 获取当前用户
- 公开路由（health, login, docs, openapi）走白名单

---

## 6. Swagger / OpenAPI

### 6.1 自动生成

FastAPI 自动生成 `/docs` (Swagger UI) 和 `/openapi.json`。无需手写。

### 6.2 元信息增强

```python
app = FastAPI(
    title="高考志愿填报管理后台 API",
    version="0.1.0",
    description="""管理后台 MVP API。
    认证:POST /api/auth/login → Bearer JWT。
    详细字段:data/orders/models.py""",
    contact={"name": "Hermes Agent"},
    license_info={"name": "MIT"},
)
```

### 6.3 标签分组

- `health` — 健康检查
- `auth` — 认证
- `orders` — 订单
- `stats` — 统计

---

## 7. 测试策略（TDD）

### 7.1 测试框架

- `pytest` + `fastapi.testclient.TestClient`（内部用 httpx；dev 依赖需显式安装）
- fixture：内存 SQLite（`sqlite3.connect(':memory:')`）+ 自动建表 + 自动建 admin 账户
- 每个测试函数独立 DB，避免状态污染

### 7.2 必测项

| 项                              | 验证                        |
| ------------------------------- | --------------------------- |
| `GET /health`                   | 200 + `{"status":"ok"}`     |
| `GET /docs`                     | 200 HTML                    |
| `GET /openapi.json`             | 200 JSON, 含 `paths`        |
| `POST /api/auth/login` 正确凭证 | 200 + JWT                   |
| `POST /api/auth/login` 错凭证   | 401                         |
| `GET /api/auth/me` 无 token     | 401                         |
| `GET /api/auth/me` 有效 token   | 200 + 用户信息              |
| `GET /api/orders` 无 token      | 401                         |
| `GET /api/orders` 有效 token    | 200 + `[]` (MVP 阶段无数据) |
| `GET /api/orders/{id}` 不存在   | 404                         |
| JWT 过期                        | 401                         |
| JWT 签名错                      | 401                         |
| `pytest --cov admin`            | 覆盖率 >= 70%               |

### 7.3 覆盖率门槛

参考 v2.1 实施计划：核心包覆盖率 >= 70%。T6.1 完成后跑：

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m pytest admin/tests/ --cov=admin --cov-report=term-missing
```

---

## 8. 部署

### 8.1 MVP 本地启动

```bash
# 1. 安装依赖（一次性）
pip3 install --user --break-system-packages fastapi uvicorn pyjwt httpx pydantic

# 2. 启动服务
export GAOKAO_JWT_SECRET="$(python3 -c 'import secrets;print(secrets.token_hex(32))')"
python3 -m admin.app --port 8000

# 3. 访问
open http://localhost:8000/docs
```

### 8.2 T6.7 Docker 阶段（不在 T6.1 范围）

T6.7 阶段出 Dockerfile + docker-compose.yml。

---

## 9. 风险与缓解

| 风险                       | 概率 | 影响 | 缓解                                         |
| -------------------------- | ---- | ---- | -------------------------------------------- |
| FastAPI 升级破坏兼容       | 低   | 中   | 锁版本（fastapi==0.133.1, pydantic==2.13.4） |
| 默认 admin 账户泄露        | 中   | 高   | 启动日志 WARN + README 强调 prod 必须改密    |
| JWT secret 弱              | 中   | 高   | dev 占位 + 启动日志断言长度                  |
| SQLite 并发写冲突          | 低   | 低   | MVP 单机 + 启用 WAL                          |
| 与 T4.1 dataclass 耦合过紧 | 低   | 中   | DAO 层明确接口边界                           |

---

## 10. T6.2 仪表盘（一站式数据统计）

### 10.1 设计目标

为运营人员提供一个最小可用的仪表盘端点：返回订单数 / 用户数 / 收入三项汇总
卡片，叠加 6 态分布 / 来源分布 / 服务版本分布三个柱状图数据源，并给出
今日 / 7 天 / 30 天三个窗口的趋势序列（日粒度，0 填充）。

### 10.2 端点

| 方法 | 路径                   | 鉴权 | 说明                                                |
| ---- | ---------------------- | ---- | --------------------------------------------------- |
| GET  | `/api/stats/dashboard` | JWT  | 一站式仪表盘 payload                                |
| GET  | `/api/stats/orders`    | JWT  | 订单维度统计（沿用 T6.1 stub 字段名，接入真实 SQL） |

### 10.3 响应契约

```json
{
  "summary": {
    "total_orders": 6, "total_revenue_cents": 100000, "total_users": 1,
    "orders_today": 3, "orders_7d": 4, "orders_30d": 5,
    "revenue_today_cents": 20000, "revenue_7d_cents": 70000, "revenue_30d_cents": 100000
  },
  "by_status":         {"pending": 0, "paid": 1, "serving": 1, "delivered": 0, "completed": 1, "refunded": 1},
  "by_source":         {"xianyu": 0, "wechat": 0, "web": 0, "school": 0},
  "by_service_version":{"audit": 0, "basic": 0, "standard": 0, "premium": 0},
  "trends": {
    "today": [{"date": "2026-06-12", "orders": 3, "revenue_cents": 20000}],
    "7d":    [{"date": "2026-06-06", "orders": 0, "revenue_cents": 0}, ... 共 7 个点 ...],
    "30d":   [{"date": "2026-05-14", "orders": 0, "revenue_cents": 0}, ... 共 30 个点 ...]
  },
  "generated_at": "2026-06-12T16:30:00+00:00"
}
```

### 10.4 口径约定（必须文档化）

- **收入 (revenue_cents)** = 所有 **非 pending 且非 refunded** 订单的
  `amount_cents` 累计值。
  - `pending`：未付款，不计入有效收入
  - `refunded`：已退款，从累计收入中扣除
  - `paid / serving / delivered / completed`：四态均计入
- **趋势桶粒度** = 日（UTC，`YYYY-MM-DD`）。`substr(created_at, 1, 10)` 与
  ISO8601 字符串前缀等价。
- **"今日"** = 服务器当前 UTC 日；**7d / 30d** = 含今日回溯 7 / 30 个完整日。
- **0 填充**：窗口内的"无订单日"也要返回 0 点，前端拿到的是稠密序列。
- **数据源隔离**：
  - `orders` / `order_status_history` → `GAOKAO_ORDERS_DB_PATH`（默认 `data/orders.db`）
  - `admin_users` → `GAOKAO_DB_PATH`（默认 `data/orders/admin.db`）
- **不读 PII**：统计路径只触碰 `amount_cents` / `status` / `source` /
  `service_version` / `created_at`，不进入加密层。

### 10.5 模块分层

- `admin/stats.py`：纯函数 SQL 聚合层（`build_dashboard_payload` /
  `compute_summary` / `compute_by_*` / `compute_trends` / `generate_day_series`）
  - 可单测：纯函数 + 可注入 `today` 参数
  - 与路由层解耦：业务测试不依赖 FastAPI
- `admin/routes/stats.py`：FastAPI 路由层
  - 仅鉴权 + 响应包装
  - `DashboardResponse` / `OrderStatsResponse` 两个 pydantic 模型

### 10.6 配置新增

- `Settings.orders_db_path`（`GAOKAO_ORDERS_DB_PATH`，默认 `data/orders.db`）
  - 与 `data.orders.*` 共享同一 DB
  - 与 `data.channel_sync.webhook_server` 已有的同名环境变量对齐

### 10.7 测试覆盖（11 用例）

`admin/tests/test_routes_stats_dashboard.py`：

- 鉴权（无 token 401 / 有 token 200）
- 空库形状契约：summary / by\_\* / trends 三层结构稳定
- 趋势序列：1 / 7 / 30 个点，按日期严格升序
- 0 填充点：包含完整三字段（`date` / `orders` / `revenue_cents`）
- 真实数据：窗口边界（45 天前的订单被 30d 窗口排除，但计入 total）
- 收入口径：pending / refunded 不计入 revenue
- 0 填充：范围内无订单的日也返回 0 点
- 兼容层：`/api/stats/orders` 字段名不变，`_stub` 标记已移除

### 10.8 T6.2 DoD

- [x] `admin/stats.py` 纯函数聚合层落地
- [x] `/api/stats/dashboard` + `/api/stats/orders` 双端点接入
- [x] 11 个 dashboard 测试 + 1 个真实数据兼容测试，全部通过
- [x] admin 全量 87/87 测试通过；repo 全量 412/412 测试通过
- [x] 新增代码 ruff check 通过
- [x] 文档同步：本文档新增 §10、README 增量更新、CHANGELOG 记录

---

## 11. 完成标准（DoD）

T6.1 完成的硬标准：

- [x] 设计文档（本文件）
- [x] `admin/` 模块代码（app/config/db/auth/password/routes）
- [x] 测试套件通过（覆盖率 >= 70%）
- [x] `python3 -m admin.app` 启动成功
- [x] `http://localhost:8000/docs` 可访问
- [x] `http://localhost:8000/openapi.json` 返回合法 OpenAPI schema
- [x] `POST /api/auth/login` + `GET /api/auth/me` 端到端通
- [x] 默认 admin 账户创建,WARN 日志输出
- [x] requirements-dev.txt 或新 requirements-admin.txt 列出依赖
- [x] AGENTS.md / README.md 增量更新（T6.1 章节）
- [x] git commit + push 三仓库

---

## 12. 后续任务衔接

- [x] **T6.2** (仪表盘)：`/api/stats/dashboard` + `/api/stats/orders` 已落地（见 §10）
- [x] **T6.3** (用户管理)：`/api/admin/users` 列表 / 详情 / 脱敏 / 搜索已落地
- [x] **T6.4** (订单管理)：`/api/orders` 已补齐列表 / 详情 / POST / PATCH / export，状态变化统一走 `state_machine`
- **T6.5** (案例管理)：新增 `data/cases/` 表 + `/api/cases` CRUD
- **T6.6** (WebUI)：HTML 模板 + 静态托管
- **T6.7** (Docker)：Dockerfile + compose
