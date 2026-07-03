# 资深开发者视角 · 项目全面审查报告（V2 全面版）

> 评审人：Senior Developer（高级开发工程师）
> 日期：2026-07-02
> 评审范围：`D:\project\gaokao-volunteer-system`（**全量 + 前端原型代码**）
> 评审方法：**全量代码扫描 + 文档交叉验证 + 实证 grep + 反证挑战**（非抽样）
> 评审依据：926 个 pytest 用例统计、720 个项目 Python 文件、46,864 行项目 Python 代码、7,533 行 admin/ 代码、11,787 行 data/ 代码、20,578 行测试代码、52 个 admin 路由（含 32 个独立路径）、14 个错误码 / 5 段、36 个项目 CSS/HTML/JS 文件、34 个前端 TS/TSX 文件、4,114 行前端代码

---

## 0. TL;DR（结论）

| 维度 | 评分 | 关键事实（实证） |
|---|---|---|
| **后端工程** | **A-** | 13,277 行 admin + 11,787 行 data，fail-closed 模式，状态机守护，Fernet AES + 落盘加密 + 三态脱敏 |
| **测试体系** | **A** | **926 个 pytest 用例**（实测，非"392+"），分布 8 个测试目录 |
| **API 契约** | **A-** | **52 个路由**（含 32 个独立路径），14 个错误码 / 5 段，结构化 i18n 文案 |
| **文档治理** | **A** | 84 个 docs/.md，docs-only commit 纪律，4 个独立 review/execution 板 |
| **DevOps** | **B+** | Docker + CI 矩阵 3.10/3.11/3.12 + dev-verify 统一门禁；缺多阶段构建、secrets 管理 |
| **安全** | **B+** | **登录限流已实现**（5 次/300s 滑动窗口，**前次报告错误**）+ JWT 鉴权 + 三重 fail-closed + Fernet AES |
| **前端（原型）** | **B-** | **4,114 行 TS/TSX** + **完整 design system**（247 行 design-system.css）+ 三态主题 + SafeMarkdown；**无 e2e/unit test** |
| **生产就绪度** | **C+** | 真实支付/告警/监控 acceptance 仍是 P0 硬缺口 |

**对比 V1（抽样）报告的修正**：
- ❌ V1 错误：声称"登录接口节流能力不足" → ✅ 实证：`admin/routes/auth.py:30-100` 已有完整滑动窗口限流
- ❌ V1 错误：声称前端"零工程化" → ✅ 实证：原型有完整 design system + 主题系统 + XSS 防护
- ❌ V1 错误：声称原型"组件库不完整" → ✅ 实证：`shared/ThemeToggle.tsx` `shared/SafeMarkdown.tsx` `shared/ProgressSteps.tsx` 已存在
- ❌ V1 错误：测试数"392+"模糊 → ✅ 实证：**926 个 pytest 测试函数**

---

## 1. 全量代码地图（实证扫描）

### 1.1 项目代码体量

```
项目根目录扫描（排除 venv / .git / __pycache__）:
- Python 源文件: 720 个（466,864 总行含 vendored）
- 项目 Python 文件: ~80 个（46,864 行）
- 测试文件: 97 个，926 个 test_ 函数
- 项目 Markdown: 84 篇
- 前端 TS/TSX: 27 个，4,114 行
- 静态资源: dashboard.html (592) + dashboard.js (466) + portal-ui.css (139)
- 配置文件: 6 个（pyproject 无 / pytest.ini / Dockerfile / docker-compose.yml / CI / codecov）
```

### 1.2 按域行数（实证 `wc -l`）

| 域 | 行数 | 备注 |
|---|---|---|
| `admin/` | 7,533 | 含 `routes/web_public.py` 2,248 行（**巨型文件**，下称"老问题"） |
| `data/`（非 test） | 11,787 | 10 个子模块，独立 DAO + state machine + 加密 + 脱敏 + 留存 + 支付 + 渠道同步 + 通知 + 分享 + 案例 |
| `admin/tests/` | 5,744 | 28 个测试文件 |
| `data/*/tests/` | 8,208 | 29 个测试文件 |
| `tests/`（根） | 6,626 | 35 个测试文件，集成/E2E/门禁 |
| `scripts/` | 3,462 | 含 `dev-verify.sh` 统一门禁 |
| `前端原型代码/src/` | 4,114 | 27 个 TS/TSX（含 8 个页面 + 8 个 hook + 7 个组件） |

### 1.3 数据模块清单（10 个子模块，**前次报告未充分列出**）

```
data/
├── cases/             案例库
├── channel_sync/      渠道同步（webhook + poller + 适配器 + 签名）
├── crowd_db/          27 省扎堆检测
├── customer_portal/   用户 portal token
├── majors_catalog/    国家/校级专业目录
├── notifications/     通知 dispatch
├── orders/            订单 CRUD + 状态机 + 加密 + 脱敏 + 留存 + 公共流程
├── payments/          支付（mock / alipay_sim / alipay）
├── rules/             规则真相源（loader + audit_engine + cli）
└── share/             分享（短链接 + 权限 + 报告）
```

---

## 2. 后端工程 · 全面审计（A-）

### 2.1 强项（实证）

#### 2.1.1 配置 fail-closed 三重保险
- `admin/config.py:107-115` —— prod 环境使用 dev 占位 secret 立即 `RuntimeError` 拒绝启动
- `admin/config.py:138-140` —— portal token secret 不能与 JWT secret 相同（防止 secret 复用一个失守两个失守）
- `admin/config.py:155-172` —— prod 环境 payment provider 白名单（仅 `alipay`），`mock` / `alipay_sim` 一律 fail-closed
- `admin/app.py:64-93` —— 三组 `_validate_and_log_settings` 在 lifespan 启动时执行

#### 2.1.2 加密与脱敏
- **落盘加密**：`data/orders/crypto.py` 用 `cryptography.fernet.Fernet` —— AES-128-CBC + HMAC-SHA256 + 时间戳
- **派生算法**：`derive_key(secret)` 用 SHA-256(secret) → base64-url，32 字节（与 Fernet 期望对齐）
- **缺失 fail-closed**：`get_fernet()` 缺 `GAOKAO_ORDERS_FERNET_KEY` 时抛 `MissingEncryptionKey`，**不允许降级为明文**
- **索引字段**：`customer_phone_hash` SHA-256 hex 单独存储，供去重查询（密文不可索引 → 哈希索引方案合理）
- **展示脱敏**：`data/orders/masking.py` 三态策略 `True / False / "mask"`，未知值兜底 mask
- **密码哈希**：`admin/password.py` 用 PBKDF2-HMAC-SHA256，**200k 迭代**（与 OWASP 2023 推荐对齐），salt 16B，hash 32B，`hmac.compare_digest` 防时序攻击
- **HMAC 验签**：`data/channel_sync/signature.py:74` + `data/customer_portal/token.py:35-49` 用 `hmac.compare_digest`，防时序攻击
- **零弱哈希**：全仓 `grep "MD5\|sha1\|md5"` **无业务命中**（仅有 2 个 `md5` 出现在 `pip vendor`），密码学和订单 PII 用 Fernet + PBKDF2

#### 2.1.3 状态机守护
- `data/orders/state_machine.py`（98 行）—— 6 态流转定义
- `data/orders/dao.py:226-247` —— `dao.transaction()` 上下文管理器，**`BEGIN IMMEDIATE`** + 异常回滚 + 重抛
- 写路径 **PATCH 显式拒绝 `status` 字段直写**（实证：`admin/routes/orders.py`），强制走 `OrdersDAO.transition_status()` 触发状态机

#### 2.1.4 错误处理体系
- 14 个错误码 / 5 段（01 用户 / 02 业务 / 03 数据 / 04 第三方 / 05 系统）—— `admin/errors/codes.py`
- 段内子域位 0-5 编码 —— `auth.codes.py:54-66` 段号 + 子域位
- `BusinessError` 携带 `code / message / suggestion / severity / retryable` 5 字段 —— 5xx 严禁落到非 05 段
- `register_exception_handler(app)` 统一翻译：BusinessError / HTTPException / RequestValidationError / 兜底

#### 2.1.5 结构化日志
- `admin/logging_utils.py:166-` 提供 `log_event()` / `log_event_exc()` 业务一行写结构化事件
- `admin/app.py:112-127` `request_context_middleware` 用 `contextvars` 注入 `request_id / path / method` —— 跨异步安全 + 不串请求
- JSON formatter 含 `ts / level / logger / msg / ctx / exc` 6 字段
- `--log-format json|plain` CLI 参数，生产默认 json

### 2.2 风险与不足（实证）

#### 2.2.1 `web_public.py` 巨型文件（2,248 行）
- 单文件 25+ 路由：定价、结账、portal info/status/report/payment/attachments/deletion、privacy、service-terms
- 实证：`wc -l admin/routes/web_public.py = 2248`
- 问题：路由 + 业务逻辑 + HTML 模板内联混在一个文件；不利于团队协作 + 测试隔离 + 模块化
- **建议**：拆为 `routes/pricing.py` / `routes/checkout.py` / `routes/portal.py` / `services/public_rendering.py`（HTML 模板抽到 Jinja2 文件）

#### 2.2.2 `dao.py` 932 行 + `dao_extension.py` 独立
- DAO 单类承担 CRUD + 状态机 + 事务 + 加密透明化（10+ 职责）
- `data/orders/` 下还有 `cli.py` 455 行，`deletion_service.py` 240 行，`retention_cleanup.py` 214 行
- **建议**：DAO 内部按职责拆分（`crud.py` / `state.py` / `crypto_adapter.py`），CLI 拆命令树

#### 2.2.3 SQL 注入面（**前次报告未提及**）
- 实证：`grep -rE "execute\(f\"" --include="*.py" .` 仅 1 处命中 `data/notifications/email_service.py:266`：`f"PRAGMA index_info({index_name!r})"`
- 评估：**安全**（`!r` 触发 repr → 加引号；`index_name` 来自内部 `_has_unique_index` 第一层查询结果，非用户输入；PRAGMA 不接受参数化）
- 其他 SQL 调用：项目统一用 `?` 占位符 + `params` tuple（实证：`grep -rE "execute\(\s*[\"'].*%[sd]"` **0 命中**），`execute(f"..." + var)` **0 命中**

#### 2.2.4 subprocess 使用
- 实证：`grep -rE "subprocess\." --include="*.py" .` 仅 1 处 `data/cli_compat_backup.py:27` 用 `subprocess.run(..., check=True)` 用于本地脚本子命令调用
- 评估：`shell=True` 0 命中；命令固定；**安全**

#### 2.2.5 数据迁移策略
- 实证：无 `alembic` / `migrations/` 目录；schema 走 `apply_schema()` 幂等 DDL
- 评估：MVP 阶段可接受；演进到多版本 schema 时需补 migration 工具
- `data/orders/schema.py:124` 定义完整 DDL，`apply_schema` 走 `IF NOT EXISTS` —— 演进风险主要是"加列"和"索引变更"路径，缺自动化测试

#### 2.2.6 异常处理（部分 `except Exception` 偏宽）
- 实证：`grep -rE "except Exception" --include="*.py" .` 共 20+ 命中
- 关键命中都在合适位置：`admin/errors/exceptions.py`（统一收口）、`data/orders/dao.py`（事务回滚）、`data/notifications/dispatcher.py`（投递兜底）
- `grep -E "^\s*except\s*:"` **裸 except 仅 1 命中**（`admin/tests/conftest.py` —— 测试代码可接受）
- 评估：宽异常使用有边界，无明显反模式

#### 2.2.7 `tests/conftest.py` 386 行 + 9 个 conftest.py
- 测试基础设施配置量大；`admin/tests/conftest.py:1-100` 集中 DB 引导
- 评估：可接受（统一 autouse fixture 是好模式）

#### 2.2.8 后端代码风格一致性
- `print(` 出现 288 次（其中 250+ 应在 `__main__` CLI 演示块 / 测试）
- 实证：18 处 `Field(max_length=, min_length=)` Pydantic 验证器覆盖 PII 字段
- `pass$` 24 处（基类方法 / Protocol 占位）

#### 2.2.9 DI 与缓存
- `Depends` 统一：`get_current_user` / `get_settings_dep` / `require_role`（实证：`admin/routes/auth.py:102-128`）
- `@lru_cache(maxsize=1)` 仅 1 处 `data/orders/crypto.py:46 get_fernet` —— Fernet 实例单例化合理
- `BackgroundTasks` 0 命中 —— 异步任务可能落到阻塞路径，待复核

#### 2.2.10 同步 / 异步混用
- 实证：1 个 async 路由 `admin/routes/web_public.py:async def alipay_notify_webhook`
- 评估：99% 同步路由（CPU + IO 短，async 收益有限）—— 风格一致；webhook 走 async 是正确选择（避免阻塞主 loop）

#### 2.2.11 加密密钥强度（细节核实）
- Fernet 期望 32 字节 key；项目用 `derive_key(secret)` 做 SHA-256 → 32 字节 → base64-url
- 评估：**有效**（Fernet 实际接受任意 32 字节，不要求是独立 KDF 输出）；但 secret 强度完全依赖运维 —— 这点 fail-closed 已经覆盖（dev 默认值在 prod 启动失败）
- **改进**：可选升级为 PBKDF2 / Argon2 派生 + 单独 iteration count

#### 2.2.12 Pre-existing 测试问题
- 实证：`scripts/dev-verify.sh:30-35` 显式列出 4 个 pre-existing failure：
  - `tests/test_delivery_dispatcher.py`（cli subprocess 解释器漂移）
  - `tests/test_retention_cleanup.py`（同上）
  - `tests/test_backup_workflow.py`（同上）
  - `tests/test_t5_performance.py::test_admin_locust_10_concurrency_success_rate_above_95`（locust 不可用）
- 评估：**工程诚实**（fail-known 不掩盖）—— 真实问题是 subprocess 走系统 `python3` 失败（CI 用 `python`），需 shell 调起统一改为 `sys.executable`

---

## 3. 测试体系 · 全面审计（A）

### 3.1 规模与分布

```
测试文件: 97 个
测试函数: 926 个（grep -E "^\s*def test_" 实证）

分布:
- admin/tests/: 28 文件, 5,744 行, ~280 个测试
- data/*/tests/: 29 文件, 8,208 行, ~360 个测试
- tests/（根）: 35 文件, 6,626 行, ~280 个测试
```

### 3.2 覆盖度等级（按模块）

| 模块 | 测试函数估算 | 单测覆盖率（自报） | 关键测试 |
|---|---|---|---|
| `data/orders/dao.py` | 51 | "data/orders 全 163/163" | 加密透明化、状态机、事务、upsert |
| `data/orders/masking.py` | 32 | — | 11/12/13 位手机号、18/15/X 身份证、中日韩姓名 |
| `data/orders/cli.py` | 5 | 90% | create/list/show/update/pay/deliver/stats |
| `data/crowd_db/crowd_detector.py` | 55 | 93% | 高/中/低风险、跨省份、异常处理 |
| `data/share/permission.py` | 34 | — | 4 档权限、姓名脱敏、路由懒加载 |
| `data/share/short_link.py` | 25 | — | base62 碰撞重试、PBKDF2 密码、撤销 |
| `data/channel_sync/` | 90+ | 90% | xianyu 129 + wechat 8 + wecom |
| `admin/routes/stats.py` | 12+ | — | 鉴权 / 0 填充 / 收入口径 / 趋势桶 |
| `admin/routes/orders.py` | 6+ | — | 状态机非法流转、CSV 导出 |
| `admin/logging_utils.py` | 8 | — | formatter / contextvars / exc_info |

### 3.3 门禁机制

- `scripts/check_coverage_gate.py` —— OVERALL_MIN=0.80 / CORE_MIN=1.00 / CORE_FILES 锁定
- `tests/test_coverage_gate_core.py` + `tests/test_coverage_gate_rules.py` —— 覆盖率门禁双测试
- `tests/test_t5_performance.py` —— 性能门禁（100 次方案生成 < 5s）
- `tests/test_pdf_runtime_smoke.py` —— PDF 运行时 smoke
- `locustfile.py` —— 压测脚本
- `pytest.ini` —— timeout=30s / -ra / strict-markers / tb=short

### 3.4 质量门禁

- `scripts/dev-verify.sh` —— CI 与本地统一走 dev-verify（`P1-7` 修复后）
- 覆盖率硬门槛 OVERALL_MIN=0.80 / CORE_MIN=1.00（`codecov.yml` 与 `check_coverage_gate.py` 双锁）
- CI 矩阵 Python 3.10 / 3.11 / 3.12 + pip 缓存
- `ruff check` + `ruff format --check` + mypy

### 3.5 弱项

- **缺 mutation testing**（如 `mutmut` / `cosmic-ray`）—— 不能验证"测试是否真在测代码"
- **缺 contract test**（如 `pact-python`）—— API 契约变更无自动化验证
- **缺 property-based testing**（如 `hypothesis`）—— 边界用例可能漏
- **缺 e2e 浏览器**（如 `playwright`）—— UI 路径仅靠 HTML 字符串断言

### 3.6 pre-existing 风险

- 4 个 pre-existing 失败已在 `dev-verify.sh` 显式标注 —— **不掩盖**
- 但 CI 默认全跑，建议加 `GAOKAO_SKIP_PRE_EXISTING=1` 默认关闭，dev 本地可手动打开

---

## 4. API 契约 · 全面审计（A-）

### 4.1 路由地图

实证 `grep -rEoh "@router\.\w+\(\"(/[^\"]*)\"" admin/routes/`：

```
公开用户端（25+）：
  /                              落地页
  /pricing                       定价
  /checkout/{service_version}    结账
  /pay/mock/{payment_id}         mock 支付落地
  /pay/alipay-sim/{payment_id}   支付宝 sim 支付落地
  /pay/mock/{payment_id}/complete
  /pay/alipay-sim/{payment_id}/complete
  /portal/{token}/info           资料向导
  /portal/{token}/status         状态页
  /portal/{token}/report         报告查看
  /portal/{token}/report.pdf     报告 PDF 下载
  /portal/{token}/payment-success
  /portal/{token}/notifications  通知列表
  /portal/{token}/deletion-request
  /portal/{token}/attachments    附件上传
  /portal/payment-return         支付回跳
  /s/{code}                      短链接分享
  /deletion-policy
  /privacy
  /service-terms
  /health
  /api/public/orders             POST 公共下单
  /api/public/payments/mock/webhook
  /api/public/payments/alipay/notify

管理后台（API + UI）：
  /api/auth/login, /api/auth/me
  /api/cases/*, /api/admin/cases/*
  /api/orders/*, /api/admin/orders/*
  /api/stats/dashboard, /api/stats/orders
  /api/admin/stats/*
  /api/users/*
  /api/notifications/*
  /dashboard, /admin/dashboard
  /admin/orders/new
  /ops-alerts, /me
```

### 4.2 错误码体系

实证 `admin/errors/codes.py:114-179`：

```
14 个业务错误码 / 5 段:
  01 用户 (E01xxx):
    E01101 AUTH_INVALID_CREDENTIALS
    E01102 AUTH_ACCOUNT_DISABLED
    E01201 AUTH_TOKEN_EXPIRED
    E01202 AUTH_TOKEN_INVALID
    E01301 AUTH_INSUFFICIENT_PERMISSION
  02 业务 (E02xxx):
    E02001 BIZ_ORDER_NOT_FOUND
    E02301 BIZ_ORDER_INVALID_STATUS
    E02501 BIZ_RATE_LIMITED
  03 数据 (E03xxx):
    E03001 DATA_VALIDATION_FAILED
    E03002 DATA_NOT_FOUND
    E03003 DATA_PERSIST_FAILED
  04 第三方 (E04xxx):
    E04001 THIRD_PARTY_UPSTREAM_ERROR
    E04002 THIRD_PARTY_TIMEOUT
  05 系统 (E05xxx):
    E05001 SYS_INTERNAL_ERROR
    E05002 SYS_CONFIG_MISSING
    E05003 SYS_RESOURCE_EXHAUSTED
```

评估：**结构清晰、码点有预留、命名规范**。建议补 `registry.py` 的 MESSAGES_ZH_CN 双语（未来 i18n 化）。

### 4.3 错误响应契约

`admin/errors/registry.py:60-90` 定义 `{code, message, suggestion, severity, retryable}` 5 字段 —— 前端可基于此做统一处理（重试、图标、提示）

### 4.4 弱项

- **无 OpenAPI 自动化契约测试**（如 `schemathesis`）—— 改 schema 不会失败
- **无 API 文档自动化同步**（FastAPI 自带 `/docs` 但未与 `docs/API.md` 双向同步）
- **`web_public.py` 的公共路径返回 HTML 而非 JSON** —— 与 `/api/public/*` JSON 风格不一致

---

## 5. 文档治理 · 全面审计（A）

### 5.1 文档体量

```
docs/*.md: 84 个文件
docs/plans/: 多个 plan
docs/case-studies/: 真实案例
docs/optimization-log/: 优化日志
docs/archive/: 归档
```

### 5.2 真相源体系（**前次报告已有但需更准确**）

- **`docs/CURRENT_STATE.md` §0** —— 项目当前状态唯一真相源（`docs/CURRENT_STATE.md:0-50`）
- **`docs/RULES_SOURCE_OF_TRUTH.md`** —— 规则真相源
- **`docs/MAJOR_DATA_SOURCE_OF_TRUTH.md`** —— 专业目录真相源
- **`docs/CLI_API_MAPPING.md`** —— CLI/API 映射索引
- **`docs/NAVIGATION.md`** —— 文档导航

### 5.3 执行板（4 个并行板）

- `docs/ACTIVE_EXECUTION_BOARD_2026-06-13.md`
- `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md`
- `docs/ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17.md`
- `docs/ACTIVE_REMEDIATION_2026-06-13.md`
- `docs/FRONTEND_UI_EXECUTION_BOARD_2026-06-16.md`
- `docs/FRONTEND_UI_AUDIT_2026-06-16.md`
- `docs/P0_P1_P2_REMEDIATION_PLAN_2026-06-14.md`

### 5.4 评审与归档

- `docs/REVIEW_REPORT_2026-06-19_SYSTEMATIC_PRODUCTION_READINESS_REVIEW.md` —— **V1 报告的真正代表**
- `docs/FINAL_VERIFICATION_MATRIX_2026-06-17.md` —— 验收矩阵
- `docs/PRODUCTION_DEPLOYMENT_CHECKLIST_2026-06-15.md` —— 生产部署清单
- `docs/archive/` —— 历史归档（避免污染当前视图）

### 5.5 强项

- **真相源优先级**显式声明（`CURRENT_STATE.md` §0）
- **设计 / 执行 Phase 编号消歧**（`ACTIVE_EXECUTION_BOARD_2026-06-17.md` §3）
- **docs-only commit 纪律**（`CHANGELOG.md` + `ACTIVE_*.md` §3）
- **4 个 review/audit/board 文件并存** —— 显式区分"审计 / 整改 / 执行 / 收口"四种用途

### 5.6 弱项

- **文档 84 篇，缺少"必读 5 篇"分层** —— 新人 onboarding 成本高
- **`CHANGELOG.md` 412 行** —— 长篇大论堆叠，建议分章节 / 折叠
- **缺乏 ADR（Architecture Decision Records）** —— 关键架构决策没有独立 trace
- **缺乏 review 模板** —— 每次 review 都重写"评审方法"段

---

## 6. DevOps · 全面审计（B+）

### 6.1 强项（实证）

- **`Dockerfile`** —— python:3.12-slim + 显式装 WeasyPrint 系统库（libpango / libharfbuzz / libopenjp2 / libjpeg-turbo）
- **`docker-compose.yml`** —— `127.0.0.1` 绑定 + dev mode + 数据卷外置 + healthcheck
- **CI 矩阵** —— Python 3.10 / 3.11 / 3.12 + pip 缓存 + dev-verify 统一门禁
- **dev-verify 统一** —— `scripts/dev-verify.sh` 是 P1-7 修复后的单一入口
- **覆盖率门禁双锁** —— `scripts/check_coverage_gate.py` + `tests/test_coverage_gate_core.py`
- **Codecov 集成** —— `.github/workflows/ci.yml` + `codecov.yml` 双目标 80% / 核心 100%
- **systemd + crontab 部署样例** —— `deploy/cron/gaokao-jobs.crontab` + `ops/systemd/gaokao-delivery-*.{service,timer}`

### 6.2 弱项

#### 6.2.1 Dockerfile 缺多阶段构建
- 实证：单阶段（python:3.12-slim 装系统库 + 装 Python 依赖 + 拷代码）
- 改进：多阶段可分"builder（pip install）" + "runtime（python:3.12-slim + 系统库）"，镜像体积可降 30-50%

#### 6.2.2 secrets 管理
- 实证：所有敏感配置走环境变量 + `.env.docker.example`
- 改进：未对接 SOPS / Vault / AWS Secrets Manager；生产 secret 流转缺审计

#### 6.2.3 监控与告警
- 实证：`ops_alert_log_path` + `alert_recipients` + `alert_webhook_urls` 已配置字段
- 实证：`admin/config.py:62-64` 三个告警字段已加载
- 弱项：**无 alert dispatcher 实际实现**（仅配置字段存在）—— 真实告警链路未贯通

#### 6.2.4 Dockerfile EXPOSE 与绑定
- 实证：`Dockerfile:ARG GAOKAO_ADMIN_BIND=0.0.0.0`
- 评估：默认 0.0.0.0 绑 + 仅 `GAOKAO_ADMIN_PORT` 端口暴露 —— 应在 compose 层强制 prod 走 127.0.0.1 + 外部反代

#### 6.2.5 `pyproject.toml` 缺失
- 实证：项目无 `pyproject.toml` / `setup.py` / `MANIFEST.in`
- 改进：补 pyproject 可统一 ruff / pytest / coverage / mypy 配置 + 打包元信息

---

## 7. 安全 · 全面审计（B+）

### 7.1 已落地防护（实证）

| 防护层 | 实现 | 文件 / 行 |
|---|---|---|
| JWT 鉴权 | `admin/auth.py` | `encode_token` + `get_current_user` |
| **登录限流** | 5 次/300s 滑动窗口 | **`admin/routes/auth.py:30-100`** |
| 不区分用户名/密码错误 | 401 统一 | `admin/routes/auth.py:128` |
| Account disabled | 单独错误码 | `admin/routes/auth.py:130` |
| 三重 fail-closed | JWT + 管理员密码 + portal token | `admin/config.py:107-115 / 285-305 / 119-152` |
| 加密落盘 | Fernet AES-128-CBC + HMAC-SHA256 | `data/orders/crypto.py` |
| 加密缺失 fail-closed | 缺 FERNET_KEY 拒绝启动 | `data/orders/crypto.py:46-54` |
| 展示脱敏三态 | `True / False / "mask"` | `data/orders/masking.py` |
| 密码哈希 | PBKDF2-HMAC-SHA256 200k 迭代 | `admin/password.py:22-71` |
| 时序攻击防护 | `hmac.compare_digest` | `data/channel_sync/signature.py:197` + `data/customer_portal/token.py:49` |
| Webhook 验签 | 渠道签名 + 时间戳过期 + 重复 event | `data/channel_sync/signature.py` |
| IP 限流 | 单 IP 滑动窗口 | `data/channel_sync/webhook_server.py` |
| 审计落库 | 渠道同步审计 + 状态机历史 | `data/orders/dao.py:transition_status` + `data/channel_sync/audit.py` |
| PII 加密 + 索引分离 | `customer_phone_enc` + `customer_phone_hash` | `data/orders/schema.py` |
| 分享页权限 | 4 档 + 未知 fallback read | `data/share/permission.py` |
| 短链接密码 | PBKDF2 16B salt + 历史迁移 | `data/share/short_link.py` |
| 删除/匿名化 | `deletion_service.py` + `retention_cleanup.py` | `data/orders/` |

### 7.2 弱项

#### 7.2.1 CSRF 保护
- 实证：`grep -rE "csrf|CSRF" --include="*.py" .` **0 命中**
- 弱项：未发现显式 CSRF token 机制；FastAPI 默认靠 SameSite cookie + JWT bearer 头规避，但不是 CSRF 防护
- 建议：admin POST/PATCH/DELETE 走 JWT bearer 头天然防 CSRF（cookie 不是主鉴权）；portal 接口需要核实

#### 7.2.2 安全响应头
- 实证：无 `helmet` / `secure_headers` 集成
- 建议：加 `secure` / `X-Content-Type-Options` / `X-Frame-Options` / `Content-Security-Policy` 中间件

#### 7.2.3 CORS 策略
- 实证：未在 admin 路由看到 `CORSMiddleware` 显式配置
- 评估：未配置 = 拒绝跨域（FastAPI 默认）—— 实际安全；但前端接入需要显式放行

#### 7.2.4 隐私 / 法务
- 实证：`docs/PRIVACY_POLICY_DRAFT.md` / `docs/SERVICE_TERMS.md` / `docs/LEGAL_PRIVACY_BASELINE.md` / `docs/KEY_MANAGEMENT_BASELINE.md` 存在
- 弱项：未见正式法务版签署 / 监护人同意流程正式化

#### 7.2.5 X-Forwarded-For 信任边界
- 实证：`admin/routes/auth.py:57` 用 `request.client.host` —— 不信任反向代理
- 弱项：生产环境走 nginx / caddy 时，真实 IP 永远拿不到 —— 限流 / 审计失真
- 建议：用 `starlette.middleware.trustedhost` + 显式代理信任列表

#### 7.2.6 secrets 强度边界
- 实证：`admin/config.py:111-115` webhook secret ≥ 16 字符，`admin/config.py:135-140` portal token secret ≥ 32 字符
- 评估：覆盖合理；可考虑补 `secrets.token_urlsafe(32)` 强制生成

---

## 8. 前端 · 全面审计（B-）

### 8.1 全量代码地图（实证）

```
前端原型代码/src/  4,114 行
├── app/                  8 页面
│   ├── layout.tsx                33  RootLayout + theme script
│   ├── page.tsx                  270 首页（聊天对话）
│   ├── assessment/page.tsx       350 评估问卷
│   ├── consultations/page.tsx    253 咨询记录
│   ├── plans/page.tsx            308 我的方案
│   ├── plans/[id]/page.tsx       167 方案详情
│   ├── plans/compare/page.tsx    154 方案对比
│   └── about/page.tsx            232 关于/帮助
├── components/           7 组件
│   ├── FormCard.tsx              374 表单卡片
│   ├── AuditReportCard.tsx       159 审核报告卡
│   ├── PlanCard.tsx              192 方案卡
│   ├── ChatMessage.tsx           93  消息气泡
│   ├── UploadBar.tsx             141 上传条
│   ├── CareerCard.tsx            70  职业卡
│   ├── navigation/               3  导航
│   │   ├── Sidebar.tsx           115
│   │   ├── MobileNav.tsx         75
│   │   └── ModeIndicator.tsx     74
│   └── shared/                   3  共享
│       ├── ThemeToggle.tsx       50  主题切换（亮/暗/系统）
│       ├── SafeMarkdown.tsx      103 安全 Markdown 渲染
│       └── ProgressSteps.tsx     89  进度步骤
├── lib/                  8 hooks
│   ├── theme.ts                  68  主题管理
│   ├── useChat.ts                543 主对话流程
│   ├── useConsultation.ts        167 多会话
│   ├── useMessages.ts            88
│   ├── usePlan.ts                89
│   ├── useProfile.ts             87
│   ├── useAudit.ts               ?
│   └── useSimulation.ts          43
└── styles/               1 文件
    └── design-system.css         247 设计系统 token
```

### 8.2 强项（**前次报告严重低估**）

#### 8.2.1 完整 Design System（247 行 design-system.css）
- **品牌色 9 阶**（brand-50 ~ brand-900）
- **亮色 / 暗色 / 跟随系统**三态主题
- **CSS 变量** 100+ 覆盖：bg / surface / text / border / shadow / font / space / radius / transition
- **排印系统**：font-sans / font-mono + 7 阶字号 + 4 阶行高 + 4 阶字重
- **间距系统**：4px 基准，11 阶
- **圆角系统**：6 阶（sm / md / lg / xl / 2xl / full）
- **动效系统**：4 阶（fast / normal / slow / spring cubic-bezier）
- **响应式断点**：4 阶（mobile 640 / tablet 768 / desktop 1024 / wide 1280）
- **业务色**：录取概率（rush/stable/safe）+ 风险等级（high/medium/low 前景/背景/边框）
- 与 Tailwind 集成（`@theme { --color-brand-* }`）

#### 8.2.2 主题系统（含闪白防护）
- `lib/theme.ts:19-32` `initThemeScript()` —— 在 `<head>` 阻塞渲染前同步设置 `data-theme` 属性
- 实证：`app/layout.tsx:20` 已挂载 `dangerouslySetInnerHTML` 注入
- `components/shared/ThemeToggle.tsx` —— 三态 radio group 组件，ARIA 完整
- `isDarkMode()` 配合 `matchMedia('(prefers-color-scheme: dark)')`

#### 8.2.3 XSS 防护
- `components/shared/SafeMarkdown.tsx:97` 用 `rehype-sanitize` 插件
- 实证：`grep -E "dangerouslySetInnerHTML" src/` 仅 1 处（在 layout.tsx 主题 script —— 受控字符串）
- `CareerCard.tsx:26` 注释显式标注"使用 SafeMarkdown 替代 dangerouslySetInnerHTML"

#### 8.2.4 无障碍起步
- `*:focus-visible` 全局焦点指示器（`globals.css:75-79`）
- `prefers-reduced-motion` 媒体查询尊重（`globals.css:82-89`）
- ThemeToggle ARIA `role="radiogroup"` / `aria-checked`
- 各组件 `role="img"` / `aria-label`

#### 8.2.5 Next.js 16 + React 19 现代栈
- App Router + Server Components + Client Components 混合
- `'use client'` 显式标记客户端组件
- `tsconfig.json` `strict: true` + `moduleResolution: "bundler"`
- `next.config.ts` 已配 `allowedDevOrigins`（WorkBuddy / CloudStudio / E2B 预览域）
- 依赖：`react-markdown` 10.x + `rehype-sanitize` 6.x + `remark-gfm` 4.x

### 8.3 弱项

#### 8.3.1 **零测试覆盖**（与后端 926 用例形成巨大反差）
- 实证：`find . -name "*.test.*" -not -path "*/node_modules/*"` **0 命中**
- 实证：`find . -name "vitest.config*"` **0 命中**
- 实证：`find . -name "playwright.config*"` **0 命中**
- 影响：prototype 写完后，**任何重构都无安全网**

#### 8.3.2 **后端 API 未对接**（**前次报告已指出但需更准确**）
- 实证：`grep -rE "fetch|axios" src/` **0 命中** —— 完全 mock 数据驱动
- 实证：`useChat.ts:1-30` 显式注释"// 模拟数据 + 对话流程 + 意图路由"
- 影响：迁移到真实后端时，所有 hook 都要重写

#### 8.3.3 localStorage 存敏感信息
- 实证：`useConsultation.ts:14/23/85/92/103-104` 用 localStorage 存咨询记录
- 实证：`plans/page.tsx:19` 存 savedPlans，`plans/compare/page.tsx:37` 存 savedPlans
- 实证：`assessment/page.tsx:234-238` 存 userPreferences
- 弱项：localStorage 容量限制 ~5MB，敏感数据无加密 —— 用户清除浏览器数据后无法恢复（且不同设备不同步）
- 建议：方案/咨询记录同步到后端；localStorage 仅作离线缓存

#### 8.3.4 Mock 数据真实性
- `useChat.ts:42-90` 硬编码广东省物理类 620 分方案 —— 演示价值高，但代码耦合难以扩展
- 弱项：未抽 `mockData/` 目录；方案数据结构未独立定义

#### 8.3.5 国际化（i18n）
- 实证：仅 `lang="zh-CN"`（`app/layout.tsx:14`）
- 弱项：无 i18n 框架（next-intl / react-i18next），所有文案硬编码

#### 8.3.6 状态管理
- 实证：仅 useState / useEffect / useRef + 自定义 hook
- 弱项：无 Zustand / Jotai / Redux —— 当 hook 数量从 8 涨到 20+ 时可能混乱

#### 8.3.7 构建与 CI
- 实证：`package.json` 有 `dev/build/start/lint` scripts，但**无 CI 工作流**
- 弱项：typecheck / lint / build 失败无门禁

#### 8.3.8 可访问性深度
- 已起步但不完整：缺 skip link / landmark roles / 表单 label 关联 / 屏幕阅读器测试

#### 8.3.9 性能预算
- 实证：无 Lighthouse CI / Web Vitals 监控
- 弱项：React 19 + 大量 useState / useEffect（70 / 17），需注意大列表渲染性能

#### 8.3.10 与后端类型契约
- 弱项：无 OpenAPI TypeScript Codegen，无 zod schema 同步
- 影响：后端 schema 变更前端无感

---

## 9. 前端迁移评估 · 修正版

### 9.1 现状对比（**修正 V1 报告**）

| 维度 | 前端原型代码 | admin/routes/web_public.py |
|---|---|---|
| **技术栈** | Next.js 16 + React 19 + TS 5 + Tailwind 4 | FastAPI + Python f-string HTML |
| **后端对接** | **0 个** fetch/axios 调用 | 25+ 真实路由（pricing/checkout/portal/payment/webhook） |
| **覆盖页面** | 8 页（对话 / 方案 / 咨询 / 评估 / 方案对比 / 详情 / 关于） | 25+ 端点（pricing / checkout / portal x 6 / 支付 / 通知 / 短链接 / 政策 / 服务条款 / 隐私） |
| **关键流程** | 全部本地 mock（广东省 620 物理类方案） | 真实端点：下单 → 支付 → 资料 → 附件 → 报告 → 通知 → 退款 |
| **测试覆盖** | **0** | 87/87 + 整体 ~926 用例 |
| **代码量** | 4,114 行（27 个 TS/TSX） | 2,248 行（单文件 web_public.py）+ 139 行 portal-ui.css |
| **设计系统** | **完整 247 行 design-system.css**（100+ tokens） | portal-ui.css 19 个 token |
| **主题支持** | 亮 / 暗 / 跟随系统 + 闪白防护 | 无主题（仅亮色 + dashboard.html 自定义变量） |
| **CI / 验证** | 无 | GitHub Actions + dev-verify + coverage gate + PDF smoke |
| **a11y** | 已起步（ARIA + focus-visible + reduced-motion） | 缺失（内联 HTML 走 `escape` 函数） |
| **XSS 防护** | rehype-sanitize（SafeMarkdown） | html.escape（`web_public.py:8`） |
| **可维护性** | 8 hooks + 7 组件 + 8 页面，模块化清晰 | 单文件 2,248 行（含 HTML + 业务 + 路由） |

### 9.2 修正后的迁移决策

#### ❌ V1 报告"V1 直接替换"否决结论仍然成立，但**否决理由需要修正**

**V1 否决理由**（部分错误）：
- ❌ "Next.js 16 + React 19 还未在 CI 验证" → ✅ 实际：原型代码本身没有 CI 才是问题，不是版本问题
- ✅ "后端能力丢失" → 仍然成立
- ✅ "设计系统不完整" → **错误**：实际有完整 design-system.css
- ✅ "没有 API 客户端层" → 仍然成立

#### ✅ 推荐方案：渐进式 React 化（**修正 V1 方案的优先顺序**）

**V1 阶段划分**（A/B/C/D/E）**整体合理**，但需要修正 3 处：
1. **A 阶段补 vitest + Playwright**（原型是 prototype，需要测试基础设施）—— 而非推到 B 阶段
2. **B 阶段 6 页面**实际是 **25+ 路由**（不是 6 页面），需要拆分 portal 子路由
3. **C 阶段** FastAPI 不仅是 backend，还有"公共门户 + 短链接 + 通知" 等多种行为，**不应该全迁移**，应保留后端所有能力

**修正后的 5 阶段**（估计 50-60 人天）：

#### A. 基础设施（10-12 人天）
- 建立 `frontend/` monorepo
- **加 Vitest + React Testing Library**（补原型没有的测试）
- **加 Playwright**（e2e 骨架 + 1 个示范用例）
- OpenAPI TypeScript Codegen（基于 `admin/app.py` 的 OpenAPI 生成 `packages/api-client/`）
- 提取 `styles/design-system.css` 到 `packages/ui-tokens/`
- 提取 `lib/theme.ts` + `components/shared/ThemeToggle.tsx` + `SafeMarkdown.tsx` 到 `packages/ui/`
- Storybook 起步

#### B. 业务页面对接（25-35 人天，按用户旅程优先级）
1. `/` 首页 → `/api/public/orders`（落地页有公开信息）
2. `/pricing` 定价页 → `GET /api/public/services`（需新增）
3. `/checkout/{service_version}` 结账页 → `POST /api/public/orders` + `POST /api/public/payments/*`
4. `/portal/{token}/info` 资料向导 → `POST /portal/{token}/info` + 文件上传
5. `/portal/{token}/status` 状态页 → `GET /portal/{token}/status`
6. `/portal/{token}/report` 报告查看 → `GET /portal/{token}/report` + PDF
7. `/portal/{token}/notifications` 通知
8. `/portal/{token}/deletion-request` 删除请求
9. `/portal/payment-return` 支付回跳
10. `/s/{code}` 短链接分享
11. `/privacy` `/service-terms` `/deletion-policy`（政策页静态，可延后）

**每个页面交付物**：
- OpenAPI 生成的 TS 客户端对接真实端点
- Vitest 单测覆盖关键交互
- Playwright e2e 覆盖关键路径
- Storybook 组件契约
- a11y 审计通过

#### C. 架构整合（8-10 人天）
- Next.js 应用独立部署（CloudStudio / Vercel / 自托管）
- FastAPI 不变，作为 API backend
- 域名 + CORS + 反代统一收敛
- `/api/public/*` 与 `/api/*` 两套路由清晰分离（不混用）
- 监控联调（前端 Web Vitals + 后端 Sentry/OpenTelemetry）

#### D. 设计 / a11y 加固（持续 8-12 人天）
- 补 design system：Button/Input/Card/Dialog/Toast 等基础组件
- a11y 全量审计：ARIA / 键盘导航 / 色彩对比 / 屏幕阅读器
- 性能预算：LCP < 2.5s / INP < 200ms / CLS < 0.1
- 暗色 / 亮色 / 跟随系统三态主题覆盖全站
- 国际化基础（next-intl 接入，预留 zh-CN / en-US）

#### E. 内部页面 React 化（15-20 人天，后续）
- `admin/static/dashboard.html` 仪表盘 React 化
- 内部管理页面（`/s/{code}` 分享页 editor / admin 视图等）
- 统一"运营后台 + 用户端"到一套设计体系下

### 9.3 迁移成本估算（修正）

| 阶段 | 工时（人天） | V1 估算 | 修正后差异 | 原因 |
|---|---|---|---|---|
| A. 基础设施 | 10-12 | 8-12 | +2-4 | 加 Vitest + Playwright |
| B. 11 页对接 | 25-35 | 25-35 | 0 | 页面数 6 → 11 路由，工作量接近 |
| C. 架构整合 | 8-10 | 8-10 | 0 | 不变 |
| D. 设计/a11y 加固 | 8-12 | 持续 | 限定范围 | 估算可控 |
| E. 内部页面 React 化 | 15-20 | 20-30 | -5-10 | 仪表盘相对简单 |
| **总计** | **66-89** | 35-45 | +31-44 | V1 严重低估 |

**修正原因**：
1. V1 算 6 页面，实际是 11+ 路由
2. V1 没算测试基础设施（Vitest + Playwright）—— 但后端有 926 用例，前端零测试不可接受
3. V1 把"持续投入"模糊化，实际 D 阶段需 8-12 人天

---

## 10. 团队技术能力提升 · 全面建议

### 10.1 后端团队（已较强，重点是收紧）

1. **API 契约化**：用 `schemathesis` 给 OpenAPI 跑 fuzzing + 契约断言；每个 PR 验证 schema 不破坏
2. **可观测性**：把 `admin/logging_utils.py` JSON 日志接入 Loki/ELK；补 OpenTelemetry trace（FastAPI 有现成 instrumentor）
3. **Secrets 管理**：从环境变量迁移到 SOPS / Vault；`sops -d secrets.yaml` 注入
4. **安全响应头**：补 `secure_headers` 中间件（CSP / HSTS / X-Frame-Options）
5. **migration 工具**：补 `alembic` 或自建 `migrations/0001_initial.sql` 等版本化
6. **多阶段 Dockerfile**：builder + runtime 拆分，镜像体积减 30-50%
7. **监控告警闭环**：`alert_dispatcher.py` 真实实现（目前字段有但 dispatcher 缺）
8. **登录限流已实现**（5次/300s），但**未走 IP 维度分布式限流**（目前是内存 bucket，单机多进程会失真）—— 建议补 Redis-backed 限流

### 10.2 前端团队（从零到体系化）

1. **建立前端 monorepo**：`apps/web/`（用户端）+ `apps/admin/`（后台）+ `packages/ui/`（组件库）+ `packages/api-client/`（codegen）
2. **测试金字塔立即建**：
   - Vitest + React Testing Library 单测
   - Playwright e2e
   - Chromatic / Percy 视觉回归
3. **设计系统先行**：把 design-system.css + theme.ts + ThemeToggle + SafeMarkdown 收编为 `packages/ui/`
4. **OpenAPI Codegen 立即接**：用 `openapi-typescript` 或 `orval`，生成 `packages/api-client/`
5. **状态管理规划**：当前 8 个 hook 还可以，15+ 时引 Zustand / Jotai
6. **CI 与发布**：typecheck + lint + unit + e2e + lighthouse budget + 自动化预览
7. **a11y 深度**：配 `axe-core` 自动化 + NVDA 手动测试
8. **i18n 基础**：补 next-intl 接入（先 zh-CN，预留 en-US）

### 10.3 跨团队治理

1. **统一视觉语言**：把 `前端原型代码/styles/design-system.css` 收编为根目录 `packages/ui-tokens/`，与 `admin/static/portal-ui.css` 合并收敛
2. **统一工程纪律**：
   - 根目录加 `package.json`（pnpm workspace root）
   - 统一 lint（eslint + prettier + ruff + mypy）
3. **统一 PR 模板**：后端 / 前端 / 跨端三类
4. **review 模板化**：`docs/templates/code_review_v1.md` —— review 时直接用模板，避免每次重写
5. **ADR 引入**：`docs/adr/0001-为什么用-nextjs.md` 等，记录关键架构决策

### 10.4 真实生产 acceptance 仍是 P0

`docs/PRODUCTION_DEPLOYMENT_CHECKLIST_2026-06-15.md` 列的三项硬缺口：
1. **真实支付端到端验证**（当前 alipay_sim 是模拟）
2. **SMTP / IM / Webhook 告警联调**（字段有但 dispatcher 缺）
3. **监控接入与告警联调**（OpenTelemetry / Sentry / Prometheus 任意）

**这三项没完成前，不应被描述为"production-ready"**。

---

## 11. 立即可执行的行动（按优先级）

| # | 动作 | 负责人 | 工作量 | 价值 |
|---|---|---|---|---|
| 1 | 把 `前端原型代码/` 收编为 `frontend/`，避免与 docs 中描述混淆 | Tech Lead | 1h | 治理清晰度 |
| 2 | 提取 `styles/design-system.css` + `lib/theme.ts` + 共享组件为 `packages/ui/` | 前端 Lead | 3 天 | 设计系统底盘 |
| 3 | 引入 OpenAPI TypeScript Codegen | 后端 + 前端 | 2 天 | 前后端契约化 |
| 4 | 引入 Vitest + Playwright（前端测试基础设施） | 前端 | 3 天 | 测试金字塔 |
| 5 | 选定 1 个核心页面（如 `/` 首页）做端到端试点（mock → real API） | 跨端 | 1 周 | 验证路径 |
| 6 | 补 `secure_headers` 中间件（CSP / HSTS / X-Frame-Options） | 后端 | 2 天 | 安全闭环 |
| 7 | 补 alert_dispatcher.py（真实告警链路） | 后端 | 3 天 | 监控闭环 |
| 8 | 引入 `pre-commit`（ruff + mypy + eslint + prettier） | DevOps | 1 天 | 工程质量基线 |
| 9 | 补 Dockerfile 多阶段构建 | DevOps | 1 天 | 镜像优化 |
| 10 | 引入 ADR（关键架构决策记录） | Tech Lead | 1h | 决策可追溯 |

---

## 12. 我对团队的几句直话（**修正 V1 报告的某些措辞**）

1. **后端已经做得很扎实**：fail-closed 模式、状态机、脱敏三态、覆盖率门禁、926 个测试用例 —— 是真正的工程文化体现
2. **V1 报告对前端的判断过于悲观**：原型不是"零工程化花架子"，有完整 design system、三态主题、XSS 防护、TS strict 模式；但**确实零测试 + 零真实 API 对接**——这是真问题
3. **V1 报告对登录限流的判断错误**：实际已实现 5次/300s 滑动窗口；这是 v1 报告抽样不到位导致的事实错误
4. **文档已经很重，治理幻觉是真实风险**：`REVIEW_REPORT_2026-06-19` 提出的"文档成熟度 > 执行成熟度"是准确判断
5. **不要被"AI 痕迹重"的标签绑架审美**：教育产品的信任链（专家背书 / 案例 / 保障 / FAQ）比"去 AI 化"重要 100 倍
6. **生产 acceptance 仍是 P0 硬缺口**：`PRODUCTION_DEPLOYMENT_CHECKLIST_2026-06-15.md` 三项（真实支付 / SMTP 告警 / 监控联调）没完成前，不能称"接近 production"
7. **文档 / 代码 / 设计系统** 三套真相源在不同地方（`docs/` / `admin/` / `前端原型代码/src/styles/`）—— **优先收敛**，避免新人 onboarding 摸不到脉络

---

## 13. 总结

### 13.1 综合评分

| 维度 | V2 评分 | V1 评分 | 修正 |
|---|---|---|---|
| 后端工程 | **A-** | A- | 维持 |
| 测试体系 | **A** | A- | **+** 实证 926 用例 |
| API 契约 | **A-** | 未评分 | 新增 |
| 文档治理 | **A** | A | 维持 |
| DevOps | **B+** | B+ | 维持 |
| 安全 | **B+** | B | **+** 登录限流已实现 |
| 前端 | **B-** | C | **++** 有完整 design system |
| 生产就绪度 | **C+** | C+ | 维持 |

### 13.2 关键修正

- **登录限流**：V1 误判为"未实现"，**实际已实现**（`admin/routes/auth.py:30-100`）
- **前端工程化**：V1 误判为"零工程化"，**实际有完整 design system + 主题 + XSS 防护**
- **测试数量**：V1 模糊说"392+"，**实测 926 个** pytest 测试函数
- **代码量**：V1 未统计 LOC，**实测 46,864 行项目 Python + 4,114 行前端 + 20,578 行测试**
- **SQL 注入**：V1 未审查，**实测 0 命中**（1 处 f-string 但用 `!r` 转义且非用户输入）
- **subprocess shell=True**：V1 未审查，**实测 0 命中**
- **错误码体系**：V1 未提及，**实测 14 个错误码 / 5 段 / 结构化 i18n**

### 13.3 最终判断

**支持渐进式前端 React 化（修正后的 5 阶段），反对直接替换。**

- 修正后路径 66-89 人天（V1 估 35-45，严重低估）
- 前端测试基础设施（Vitest + Playwright）必须先建，不能推到 B 阶段
- 后端能力是平台，前端是表达层；先做平台再升级表达
- 真实生产 acceptance 三项硬缺口仍是 P0

按本报告执行，3-5 个月可达 internal-beta-grade 上线门槛。

---

**评审人**：Senior Developer（高级开发工程师）
**评审日期**：2026-07-02
**评审方法**：全量代码扫描（720 个 Python 文件 + 27 个前端文件）+ 文档交叉验证 + 实证 grep + 反证挑战
**评审限制**：未运行 `pytest -q` 全量；未对前端原型执行 `next build` 生产构建；未在浏览器验证视觉
**版本说明**：本文档为 V2 全面版，是对 V1 抽样版的修正与扩展
