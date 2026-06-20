# 变更日志

记录高考志愿填报智能系统的所有变更。

---

## v2.1.1 (2026-06-20) — T12-D retention cleanup 生产化部署验收

### 🐛 修复

- **retention cleanup 多订单 anonymize 崩溃**（P0 — T12-D 端到端 acceptance 必现）
  - 现象: `retention_cleanup.run_cleanup(apply=True)` 在一次命中 ≥ 2 笔终端态订单时，
    第二笔开始全部 `sqlite3.ProgrammingError: Cannot operate on a closed database`
  - 根因: `OrdersDAO.__exit__` 不区分连接所有权，对外部 service 传入的
    `self._conn` 也 `close()`。`deletion_service.anonymize_order` 把 service 持有的
    连接包成 `OrdersDAO(self._conn)` 走 with-block，第一笔执行完就把连接关掉
  - 触发条件: 生产 `retention_days=180` + 周日 03:30 timer 触发时极易命中
  - 修复: `OrdersDAO.__init__` 新增 `owns_conn: bool = False` 参数；
    `__exit__` 仅在 `owns_conn=True` 时 close；`connect()` classmethod
    创建的连接自动设 `owns_conn=True`（保持原行为）
  - 回归测试: `tests/test_retention_cleanup.py::test_retention_cleanup_apply_anonymizes_multiple_old_orders_in_sequence` 锁住多订单连续 anonymize 契约

### 📝 文档

- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` §8 新增 T12-D 本地端到端 acceptance 步骤
  + 验收通过判定表（6 项全过）+ 部署前 checklist
- 历史 bug 背景已写入 runbook §8.4，避免后续误判为"运行环境问题"

---

## v2.1 (2026-06-13)

### 🚧 进行中

#### 新增（T5.3 已完成）

- 📝 **T5 集成测试与文档收口**
  - **T5.1 端到端主链已固化到 `tests/test_t5_e2e_workflows.py`**：覆盖“咨询→方案生成 / 审核→报告 / 订单→交付 / 升级流程 / 数据溯源展示”5 条主链
  - **T5.2 性能与并发门禁已固化到 `tests/test_t5_performance.py`**：
    - `gaokao-quick-3min.py` 的真实 `parse_quick_response + generate_quick_summary + generate_quick_recommendation` 链路 100 次执行断言 `< 5s`
    - `locustfile.py` 对 `admin.app` 做 10 并发、15 秒 headless 压测，断言聚合成功率 `>95%`
  - **T5.3 文档同步**：重写 `docs/API.md`、`docs/ARCHITECTURE.md` 以匹配当前已落地真相，并补充 T5 验证入口与当前系统边界说明
  - **定向验证**：`python3 -m pytest tests/test_t5_e2e_workflows.py tests/test_t5_performance.py -q` 通过；其中性能基准覆盖 100 次方案生成与 10 并发后台访问两条验收路径
  - **当前定位修正**：项目应描述为“管理后台 + 订单/分享/渠道同步 + AI 审核链路”的可运行系统；用户端 Web 自助闭环仍未落地

#### 新增（T6.4 已完成）

- ✨ **管理后台订单管理 `admin/routes/orders.py`**
  - **端点落地**：`GET /api/orders`（真实列表）/ `GET /api/orders/{id}`（详情 + 状态历史）/ `GET /api/orders/export`（CSV 导出）/ `POST /api/orders`（手工录单）/ `PATCH /api/orders/{id}`（业务字段更新 + 状态流转 + 退款）
  - **状态机守护**：写路径复用 `OrdersDAO.update()` 与 `transition_status()`，非法流转统一映射到 `E02301`，不允许绕过 6 态状态机直接写库
  - **默认脱敏**：列表、详情和 CSV 导出均走 `Order.to_dict(decrypt_sensitive="mask")`，避免管理后台直接导出完整手机号/身份证号
  - **手工兜底**：支持 `external_id` 留空的人工补录路径，与 `docs/CHANNEL_INTEGRATION.md` 约定一致；退款仅更新本地订单状态，不主动触发第三方退款 API
  - **测试 6 个全部通过**（`admin/tests/test_routes_orders.py`）：创建、列表/详情、PATCH 更新+付款、退款、非法状态冲突、CSV 导出
  - **定向验证**：`python3 -m pytest admin/tests/test_routes_orders.py admin/tests/test_routes.py -q` → 20 passed；`ruff check admin/routes/orders.py admin/tests/test_routes_orders.py admin/tests/test_routes.py` 通过
  - **文档同步**：`README.md` 新增 T6.4 章节；`docs/plans/T6-admin-mvp.md` 标记 T6.4 已落地并更新路由清单

#### 新增（T6.2 已完成）

- ✨ **管理后台仪表盘 — 真实 SQL 聚合层 `admin/stats.py`**（434 行）
  - **端点落地**：`GET /api/stats/dashboard`（一站式仪表盘）+ `GET /api/stats/orders`（沿用 T6.1 stub 字段名，去掉 `_stub` 标记）
  - **纯函数聚合层**：`build_dashboard_payload` / `compute_summary` / `compute_by_status` / `compute_by_source` / `compute_by_service_version` / `compute_trends` / `generate_day_series`
  - **响应契约**：`summary`(订单/用户/收入 + 今日/7d/30d 切片 9 字段) + `by_status` / `by_source` / `by_service_version` (完整 0 填充) + `trends` (today=1, 7d=7, 30d=30 个点, 日粒度, 0 填充) + `generated_at`
  - **关键口径**：
    - 收入 = `paid / serving / delivered / completed` 四态订单的 `amount_cents` 累计值；`pending`（未付款）与 `refunded`（已退款）排除
    - 趋势桶粒度 = 日（UTC，`YYYY-MM-DD`），用 `substr(created_at, 1, 10)` 切片
    - 0 填充 = 窗口内的"无订单日"也返回 0 点，前端拿到稠密序列
    - 数据源隔离 = `orders` 走 `GAOKAO_ORDERS_DB_PATH`（默认 `data/orders.db`），`admin_users` 走 `GAOKAO_DB_PATH`（默认 `data/orders/admin.db`）
    - 不读 PII：统计路径只触碰 `amount_cents` / `status` / `source` / `service_version` / `created_at`
  - **配置新增**：`Settings.orders_db_path`（`GAOKAO_ORDERS_DB_PATH` 环境变量，默认 `data/orders.db`），与 `data.channel_sync.webhook_server` 已有的同名变量对齐
  - **测试 12 个全部通过**（`admin/tests/test_routes_stats_dashboard.py`）：
    - 鉴权（无 token 401 / 有 token 200）
    - 空库形状契约：summary / by\_\* / trends 三层结构稳定
    - 趋势序列：1 / 7 / 30 个点，按日期严格升序
    - 0 填充点：包含完整三字段（`date` / `orders` / `revenue_cents`）
    - 真实数据：窗口边界（45 天前的订单被 30d 窗口排除，但计入 total）
    - 收入口径：pending / refunded 不计入 revenue
    - 0 填充：范围内无订单的日也返回 0 点
    - 兼容层：`/api/stats/orders` 字段名不变，`_stub` 标记已移除
  - **T9.3 已知缺口已闭环**：`admin/tests/conftest.py` 新增 `orders_db` autouse fixture（T6.2 起，所有测试默认带空 orders DB），`pytest -q admin/tests` 87/87 通过
  - **测试套件**：`pytest -q admin/tests` 87/87 passed；`pytest -q` 仓库全量 392/392 passed；`ruff check admin/stats.py admin/routes/stats.py admin/tests/test_routes_stats_dashboard.py admin/tests/conftest.py admin/config.py admin/tests/test_routes.py` All checks passed
  - **文档同步**：`docs/plans/T6-admin-mvp.md` 新增 §10（T6.2 设计与 DoD）；§12 后续任务衔接标 [x]；`README.md` 新增 T6.2 章节；`CHANGELOG.md` 本条

#### 新增（T9.3 已完成）

- ✨ **结构化 JSON 日志 `admin/logging_utils.py`**
  - 新增 `JsonLogFormatter`：单行 JSON 输出 `ts / level / logger / msg / ctx / exc`
  - 新增 `log_event()` / `log_event_exc()`：业务侧一行写结构化事件，避免散落字符串拼接
  - 新增 `contextvars` 请求上下文：自动注入 `request_id / path / method`，并在请求结束后清理，避免串请求污染
  - `admin/app.py` 新增 `request_context_middleware` 与 `--log-format json|plain` 启动参数；CLI 默认输出 JSON，保留 plain 便于本地调试
  - `admin/errors/exceptions.py` 的 `BusinessError` / `HTTPException` / `RequestValidationError` / 兜底异常日志全部升级为结构化事件
  - 新增 `admin/tests/test_logging.py` 8 个测试，覆盖 formatter、上下文绑定、异常 traceback、FastAPI 端到端 JSON 日志
  - 定向验证通过：`pytest -q admin/tests/test_logging.py admin/tests/test_errors.py` = 34/34 passed；`ruff check admin/app.py admin/errors/exceptions.py admin/logging_utils.py admin/tests/test_logging.py admin/tests/test_errors.py` 通过
  - 已知缺口（T6.2 已闭环）：`pytest -q admin/tests` 之前有 1 个非 T9.3 失败（`test_stats_orders_real_shape` 报 `sqlite3.OperationalError: no such table: orders`）— 根因是 stats 端点读 orders 表，但 T6.1 阶段 conftest 没建 orders DB；T6.2 在 conftest 加 `orders_db` autouse fixture 闭环，当前 `pytest -q admin/tests` 87/87 通过

#### 新增（T4.3 已完成）

- ✨ **订单管理 CLI `scripts/gaokao-order-manager` + `data/orders/cli.py`**
  - 子命令落地：`create / list / show / update / pay / deliver / stats`
  - 默认 JSON 输出，订单详情默认走 `Order.to_dict()` 遮罩模式，避免 CLI 直接泄露完整手机号/身份证
  - `create` 直接复用 `OrdersDAO.create()`；`show` 返回订单详情 + `order_status_history`
  - `update` 只允许业务字段，空更新返回 exit code 2，继续强制 `status` 变更走 DAO 状态机
  - `pay` 推进 `pending -> paid`；`deliver` 在 `paid` 时自动串联 `serving -> delivered`，兼容已在 `serving` 的最后一步交付
  - `stats` 输出 `total_orders / by_status / by_source / by_service_version`
  - 新增 `data/orders/tests/test_cli.py` 5 个 pytest 用例：
    - 脚本级端到端主链路（create/list/show/update/pay/deliver/stats）
    - 缺失订单错误码
    - 空更新防御
    - 模块内 direct-main 覆盖，`data.orders.cli` 覆盖率 **90%**
  - 定向验证：`pytest -q data/orders/tests/test_cli.py` 5/5 passed；`pytest -q data/orders/tests` 166/166 passed；`ruff check data/orders/cli.py data/orders/tests/test_cli.py scripts/gaokao-order-manager` 通过；`py_compile` 通过
- 📝 **`data/orders/README.md`** 新增 T4.3 CLI 使用示例与子命令语义

#### 新增（T4.2 已完成）

- ✨ **订单 DAO 数据访问层 `data/orders/dao.py`**（530 行，`OrdersDAO` 类）
  - **CRUD 完整**：`create()` / `get()` / `get_by_external_id()` / `find_by_phone()` / `list()` / `count()` / `stats_by_status()` / `update()` / `delete()`
  - **事务守护**：`dao.transaction()` 上下文管理器；嵌套语义（外层在事务中时内层不重复 commit，异常统一回滚外层）
  - **加密透明化**：API 入口接收 `Order` dataclass（明文 PII），DAO 内部用 `to_db_row()` 加密落盘 / `from_db_row()` 解密读回；调用方无需接触 `*_enc` 字段
  - **状态机守护**：`transition_status()` 走 `assert_valid_transition()` 单事务内 `UPDATE orders` + `INSERT order_status_history`；非法抛 `InvalidStateTransition` 并回滚
  - **时间戳联动**：`paid → paid_at` / `serving → started_at` / `delivered → delivered_at` / `completed → completed_at` 由状态自动置位（`COALESCE` 保留首次值）
  - **幂等 upsert**：`upsert_by_external_id()` 接管 T8.1 闲鱼 Webhook 路径，4 种 `action` 与 `data/channel_sync/dao_extension.py` 完全对齐（`inserted` / `updated` / `unchanged` / `illegal_transition`）
  - **防御设计**：`_row_factory_ctx()` 临时切 `sqlite3.Row`、退出后恢复外部 row_factory；`update()` 显式拒绝 `status` 字段（强制走 `transition_status()`）
  - **51 个 pytest 用例全绿**（覆盖加密透明化、状态机合法/非法路径、事务回滚、upsert 4 种 action、状态历史时间线、row_factory 不污染、删除 cascade）
  - **data/orders 模块总测试 163/163 通过**（含 T4.1 既有 112 + T4.2 新增 51）；`data/` 全模块 386/386 通过；ruff 0 warning
- 🔧 **`data/orders/__init__.py` 导出 DAO 公共 API**：`OrdersDAO` / `UpsertResult` / `StatusChange` / `OrderNotFound` / `DuplicateOrder` 一行 import
- 📝 **`data/orders/README.md`** 更新 T4.2 DAO 一览表、加密透明化边界表、DoD 勾选、API 下游衔接

#### 新增（T2.4 已完成）

- ✨ **扎堆报告生成器 `risk_report.py`**（`data/crowd_db/risk_report.py`，183 行）
  - `build_crowd_risks(plan, user_score, province, loader=None)` — 把 `crowd_detector.detect_crowd_risk` 的 `RiskFinding` 列表转换为 `templates/audit_report.html` 模板所需的 `crowd_risks` 字典格式
  - 三色 emoji 标识：high → 🔴、medium → 🟡、low → 🟢（随 `RISK_LEVEL_META` 自动匹配）
  - 模板字段完整：`school / major / frequency / predicted_increase / risk_level / risk_level_label / risk_emoji / platforms / alternatives`
  - alternatives 字段重映射：`name` → `school`，`score` 强制 `int`（防御非数字字符串）
  - 辅助能力：
    - `group_by_risk()` — 按风险等级分组（永远返回 high/medium/low 三个 key）
    - `format_risk_summary()` — 单行汇总（如 "🔴 1 个高风险、🟡 2 个中风险"），给报告顶部用
    - `render_risk_table()` — CLI / 微信消息场景的纯文本表格（含替代院校行）
  - 类型设计：用 `Protocol` 定义 `_LoaderProtocol`，避免对 `CrowdDBLoader` 强依赖（支持 mock 注入与未来的不同实现）
  - 22 个 pytest 单元测试全部通过（三色 emoji / 字段完整性 / 替代项重映射 / 防御性 fallback / 空方案 / 不存在省份 / 自定义 loader 注入）
- ✨ **端到端集成验证脚本 `scripts/verify_t2_4_e2e.py`**（95 行）
  - 用真实湖南 575 分数据 + `audit_report.html` 模板渲染一遍
  - 断言：模板必需字段全部存在 / alternatives 重映射正确 / 三色 emoji 在渲染输出可见
  - 跑法：`python3 scripts/verify_t2_4_e2e.py`
  - 6/6 集成断言通过
- ✅ **质量门禁**
  - `data/crowd_db/tests/` 105/105 通过（含本次新增 22 + 历史 83）
  - 仓库全量 pytest：392 passed
  - `ruff check data/crowd_db/ scripts/verify_t2_4_e2e.py` — All checks passed
  - `validate_template.py` 仍 PASS（模板字段契约未破坏）

#### 新增（T2.5 已完成）

- ✅ **扎堆检测单元测试 T2.5** — `data/crowd_db/tests/test_crowd_detector.py` 由 35 增至 55 个测试（新增 20 个）
  - **用例 1 高风险识别**：`test_high_risk_use_case_frequency_4_full_payload`（freq=4 全平台 + predicted_increase + alternatives）/ `test_high_risk_boundary_frequency_exactly_4`（>=4 闭合区间边界）/ `test_high_risk_distinct_from_medium_and_low`（high/medium 互不混淆）
  - **用例 2 替代方案**：`test_alternatives_use_case_contains_required_keys`（每个 alt 必须含 name/major/score, 0-100 区间）/ `test_alternatives_use_case_sortable_by_score`（detector 透传 alternatives 字段不丢）/ `test_alternatives_use_case_empty_list_is_valid`（空列表合法）
  - **用例 3 跨省份**：`test_cross_province_hunan_hit_guangdong_miss`（湖南 575 命中 vs 广东 575 无数据隔离）/ `test_cross_province_beijing_at_690`（同校不同省命中不同记录 — 清华 工科试验班）/ `test_cross_province_loader_called_with_correct_province`（province 透传给 loader, 不做全局查询）
  - **用例 4 异常处理**：`test_exception_use_case_loader_returns_none_field`（name=None 不崩）/ `test_exception_use_case_loader_returns_non_dict`（混入 None/str/int 时优雅过滤）/ `test_exception_use_case_loader_raises_propagates`（loader 抛错向上传播）/ `test_exception_use_case_unrecognized_entry_type`（int/float/object 走 str 兜底）/ `test_exception_use_case_entry_with_int_school_dict`（school=0 falsy 跳过）/ `test_exception_use_case_province_is_none`（province=None 不抛）/ `test_exception_use_case_tuple_with_non_string_school`（tuple 元组非 str school 走 str() 兜底）/ `test_exception_use_case_dict_with_truthy_non_string_school`（0.5 这种 truthy 非 str school 走 str() 兜底）/ `test_exception_use_case_dict_with_name_truthy_non_string`（name 字段 truthy 非 str 同样兜底）/ `test_exception_use_case_single_element_tuple_non_string`（单元素 tuple 非 str 兜底）/ `test_exception_use_case_malformed_frequency_in_record`（frequency="not a number"/None 时 try/except 按 0 处理）
- 🛡️ **`crowd_detector.py` 根因加固** — 与测试同步，detector 主循环加入三层防御：
  - `if not isinstance(rec, dict): continue` — 防止 loader 混入非 dict 元素时 `rec["name"]` 抛 TypeError
  - `if not isinstance(rec_name, str) or not rec_name.strip(): continue` — 防止 name 缺失/非 str 时 `.strip()` 抛 AttributeError
  - `try/except (TypeError, ValueError): freq = 0` — 防止 frequency 字段异常时 `int(...)` 崩溃
  - `_normalize_entry` 增加 truthy 非 str school 的 str() 兜底（dict / tuple / list 三分支）
  - 取值统一用 `or` 兜底空值：`rec.get("platforms") or []` / `rec.get("predicted_increase") or 0` / `rec.get("alternatives") or []`
- ✅ **质量门禁**
  - `crowd_detector.py` 单模块覆盖率：**93%**（101 statements / 7 missed 仅 `__main__` CLI demo 块）
  - 远高于 T2.5 PRD 阈值 **≥80%**
  - `data/crowd_db/tests/test_crowd_detector.py` 55/55 passed
  - `data/crowd_db/tests/` 全量 125/125 passed（不动 T2.1/T2.2/T2.4 既有测试）
  - `pytest -q --ignore=data/orders` 仓库全量 249 passed
  - `ruff check data/crowd_db/` — All checks passed

#### 新增（T1.3 已完成）

- ✨ **方案解析器 `plan_parser.py`**（`skills/gaokao-audit/scripts/plan_parser.py`，295 行）
  - 解析大厂AI志愿方案文本（纯文本/PDF提取/截图OCR）→ `ParsedPlan` dataclass
  - 字段提取：省份（27 省 + 别名）、分数、位次、选科、来源（千问/元宝/百度/豆包）、志愿列表
  - 志愿行识别支持 4 种行首编号格式：`1. xxx` / `1、xxx` / `1) xxx` / `1 xxx`（PDF 提取常见）
  - 学校/专业分隔支持 4 种风格：`学校 - 专业` / `学校：专业` / `学校（专业组）` / `学校 专业`（按大学/学院关键字兜底）
  - 健壮边界：空文本/无志愿/编号异常均返回 `ParsedPlan` 默认值，不抛异常
  - CLI：`python3 -m skills.gaokao-audit.scripts.plan_parser <file>` 输出 JSON
  - **10 个 pytest 单元测试全部通过**（基础解析/志愿列表/省份别名/选科/PDF 格式/空文本/无志愿/编号多样性/序列化/真实样本回归）
  - 真实样本回归 fixture：`tests/fixtures/sample_xianyu.txt`（百度AI方案）
- 🔒 **T1.2 review 闭环修复**（`skills/gaokao-audit/scripts/validate_template.py`）
  - 模板渲染 `Environment(autoescape=False)` → `autoescape=True`——修复用户派生字段（policy_errors/crowd_risks/data_issues）XSS 注入风险
  - 标签平衡检查：原 "(HTML5 void elements ignored)" 注释与实际行为不符（regex 未排除 void 元素），改为显式 `VOID_ELEMENTS` 集合减去空元素计数（103=103，7 void 元素正确排除）
  - T1.2 验证脚本仍 PASS（mock payload 全部 7 个 must_contain 字符串命中）
- 📝 **`docs/plans/T1-2-audit-skill-and-parser.md` 实施记录**：10/10 测试 ✓ · 真实样本解析正确 ✓ · 省份别名 27 省 ✓ · 编号格式 4 种 ✓

#### 新增（T1.2 已完成）

- ✨ **AI方案审核服务 Skill**（`skills/gaokao-audit/`）
  - `SKILL.md`（143 行）— 角色边界 + 49 元服务定价 + 四维审核框架 + 合规红线 + DoD
  - `templates/audit_report.html`（262 行，Jinja2）— 报告模板，含政策合规/扎堆风险/数据存疑/改进建议 4 区块 + 升级到 99 元完整方案卡片
  - `examples/sample_audit.md`（144 行）— 输入样例（大厂AI方案文本/PDF/截图）+ 输出报告样例 + 渲染数据契约表
  - `scripts/validate_template.py`（137 行）— 模板渲染校验器，16 个占位符 + 7 个渲染输出字符串断言
  - `tests/test_validate_template.py`（33 行）— pytest 入口，1 用例通过
  - 关键设计：T1.1 review 暴露的 4 个反模式（吞错、模糊 substring、vacuous 测试、缺失档位）已显式列入"对齐 T1.1 review 教训"表，由 T1.3 实施时强制规避
  - T1.2 测试套件：**1/1 通过**（含项目原有 6 个 spec_checker 测试 → 7/7 通过）

#### 新增（T7.1 已完成）

- ✨ **短链接生成**（`data/share/short_link.py` + `scripts/gaokao-shortlink`）
  - base62 短码生成（默认 6 位，4-16 位可配，加密随机 + 冲突重试）
  - SQLite 映射表 `share_links`（WAL 模式，code 主键 + report/owner/expires 三索引）
  - `ShortLinkService` 完整 API：`create / get / resolve / revoke / list_by_report / list_by_owner / get_stats / purge_expired`
  - 访问控制：`permission`（read/comment/edit/admin）+ 密码（PBKDF2-HMAC-SHA256，兼容历史 sha256 读时迁移）+ `expires_at` + `revoked`
  - `route_short_link(code, password, base_url)` 路由辅助，可挂载任意 Web 框架的 `/s/<code>`
  - CLI：`create / resolve / revoke / list / stats / purge`，全部子命令 JSON 输出
  - 25 个 pytest 用例全部通过（base62 编解码、碰撞重试、TTL、密码、撤销、列表、统计、清理、路由）

#### 新增（T7.3 已完成）

- ✨ **分享权限策略**（`data/share/permission.py`）
  - 新增 `PermissionPolicy.for_permission(permission)`：把 `read/comment/edit/admin` 归一化成分享页能力策略
  - 能力判断：`can_view / can_comment / can_edit / allows_field / can("...")`
  - 安全兜底：未知 permission 一律回退到最严格的 `read` 策略，防止越权
- ✨ **姓名脱敏策略复用**
  - 复用 `data/orders/masking.py::mask_name`，避免在分享链路重复实现脱敏算法
  - `read/comment` 默认回传脱敏姓名；公开分享场景额外收紧为：3 字及以上中文名统一 `姓+**`，非中文名统一 `**`
  - `edit`（以及历史兼容 `admin`）下姓名原样展示，但 `password_hash / internal_note / note / debug_info / raw_payload` 等内部字段仍强制隐藏
- ✨ **权限感知路由辅助**（`data.share.short_link.route_short_link_with_report`）
  - 在 `route_short_link()` 之上叠加报告 payload 渲染，支持 `report=` 直接注入或 `report_loader(report_id)` 懒加载
  - resolve 失败（not_found / revoked / expired / password_required / password_wrong）时不下发 `rendered` payload，避免泄露报告元数据
  - `render_report_payload(permission, report, share_url=...)` 输出统一结构：`policy + visible_fields + payload + masked_fields`
- ✅ **测试验证**
  - 新增 `data/share/tests/test_permission.py`，34 个 pytest 用例覆盖：三档权限、admin alias、未知 permission fallback、字段裁剪、姓名脱敏、公开分享收敛规则、route + report_loader 端到端
  - `python3 -m pytest data/share/tests/test_permission.py -q` → **34 passed**
  - `python3 -m pytest data/share/tests/ -q` → **61 passed**
  - `python3 -m pytest data/share/ data/orders/ -q` → **231 passed**
  - `python3 -m ruff check data/share/permission.py data/share/tests/test_permission.py data/share/short_link.py` → **All checks passed**

#### 新增（T10.1 已完成）

- ✨ **GitHub Actions CI 流水线**
  - 自动化测试（push / pull_request 触发）
  - 多 Python 版本矩阵（3.10 / 3.11 / 3.12）
  - pytest + pytest-cov 覆盖率报告（XML 产物供 T10.2 codecov 集成）
  - pip 依赖缓存（加速运行）
- ✨ `requirements-dev.txt` — 测试依赖（pytest / pytest-cov / pytest-timeout / pytest-xdist）
- ✨ `pytest.ini` — 统一本地与 CI 测试发现配置
- ✨ README 顶部 CI 状态徽章

#### 新增（T10.2 已完成）

- ✨ **Codecov 覆盖率报告与徽章**
  - `.github/workflows/ci.yml` 集成 `codecov/codecov-action@v4`，3.11 单点上传 coverage.xml
  - `codecov.yml` 定义 project 目标 80% / 核心 skills 目标 100% / patch 目标 70%，与 T5.5 硬门槛对齐
  - `fail_ci_if_error: false`：codecov 不可达时不影响 CI 通过（适配多镜像仓库场景）
  - README 顶部新增 codecov 覆盖率徽章
- ✨ PR 浮动容忍 1%（project）/ 2%（core），避免噪声红灯

#### 新增（T11.2 已完成）

- ✨ **敏感字段展示脱敏工具 `data/orders/masking.py`**（127 行）
  - `mask_phone` / `mask_id_card` / `mask_name` / `mask_sensitive_dict` 四个纯函数
  - 手机号：11 位 → `138****1234`；支持 `+86` / `86` 国家码剥离、常见分隔符（空格 / 横杠）
  - 身份证：18 位 → `430102********1234`（保留前 6 行政区划 + 末 4 位）；15 位老版兼容；非 18/15 位且 ≥13 位的非标准输入也走"前 6 后 4"遮罩
  - 姓名：1 字原样 / 2 字 `张*` / 3 字 `张*丰` / 4+ 字 `张**`；非中日韩字符全遮 `*****`
  - 默认安全：None / 空串 / 非字符串均不抛错，统一返回 None / ""
  - `mask_sensitive_dict` 一键遮罩订单字典中所有已知 PII 字段（不动 \_enc / \_hash 等索引/密文字段）
- ✨ **`Order.to_dict` 扩展 `decrypt_sensitive` 三态策略**
  - `True` : 完整明文（权限内接口使用，如后台人工核对）
  - `False`: 完全移除明文（对外公开统计 / 审计日志）
  - `"mask"` (默认): 部分遮罩（列表 / 详情默认 — 推荐且默认安全）
  - 未知字符串策略值回退为 mask（防误传"plaintext"导致明文泄露）
- ✨ `data/orders/tests/test_masking.py` — 32 个 pytest 用例覆盖：手机号 11/12/带 +86 / 短串 / 非法输入、身份证 18/15/X 校验位 / 短串 / 13 位非标准、姓名 1/2/3/4+ 字 / 英文 / 混合、`mask_sensitive_dict` 不变性、Order.to_dict 三态与默认 mask
- ✅ **测试验证**：data/orders/tests 全套 112 用例通过（含原有 80 + 新增 32）；全仓 344/344 通过；`ruff check` 0 warning；`ruff format --check` 3 文件已规范
- 🔒 **与 T4.1 落盘加密的关系**：crypto.py 负责"落盘形态"（密文 + hash），masking.py 负责"展示形态"（部分遮罩），两者正交 — 落盘加密是底层保险，脱敏展示是上层最小特权

#### 新增（T8.3 已完成）

- ✨ **企业微信最小客户端**（`data/channel_sync/wecom_adapter.py`）
  - `WeComBotClient.from_env()`：从 `GAOKAO_WECOM_BOT_KEY` / `GAOKAO_WECOM_API_BASE` / `GAOKAO_WECOM_TIMEOUT_SECONDS` 读取机器人 webhook 配置，缺失时 fail-fast
  - `WeComAppClient.from_env()`：从 `GAOKAO_WECOM_CORP_ID` / `GAOKAO_WECOM_CORP_SECRET` / `GAOKAO_WECOM_AGENT_ID` / `GAOKAO_WECOM_API_BASE` / `GAOKAO_WECOM_TIMEOUT_SECONDS` 读取应用消息配置
  - 机器人消息：`send_text(...)` 覆盖文本通知，支持 `mentioned_list` / `mentioned_mobile_list`
  - 应用消息：`send_text(...)` 覆盖 `touser` / `toparty` / `totag` 文本推送，支持 `safe` 与重复消息检查参数
  - access_token 自动缓存 + 提前刷新窗口：避免每次应用推送都重新拉 token
  - 错误模型统一：HTTP 非 2xx、上游 `errcode != 0`、transport 异常、非 JSON 响应统一包装为 `WeComAPIError`
- ✨ **企业微信集成测试**（`data/channel_sync/tests/test_wecom_adapter.py`）
  - 覆盖机器人 webhook payload、应用 token 缓存/消息 payload、上游 errcode、transport 异常、环境变量缺失 fail-fast
  - 同时补上 `WeChatClient` transport 异常包装回归，避免标准库 transport 网络错误直接泄漏原始异常

#### 新增（T8.2 已完成）

- ✨ **微信 SDK 最小客户端**（`data/channel_sync/wechat_adapter.py`）
  - `WeChatClient.from_env()`：从 `GAOKAO_WECHAT_APP_ID` / `GAOKAO_WECHAT_APP_SECRET` / `GAOKAO_WECHAT_API_BASE` / `GAOKAO_WECHAT_TIMEOUT_SECONDS` 读取配置，缺失时 fail-fast
  - access_token 自动缓存 + 提前刷新窗口：避免每次发送都重新拉 token，也避免临近过期 token 被继续复用
  - 订阅消息：`send_subscribe_message(...)` 自动规范化 `data` 为 `{key: {value: ...}}` 形状，并透传 `page / miniprogram_state / lang`
  - 客服消息：`send_custom_message(...)` / `send_custom_text(...)` 覆盖文本客服场景，支持可选 `kf_account`
  - 纯标准库 HTTP：`UrllibTransport` + 可注入 `Transport` 协议，便于测试 fake transport 与后续 T8.3 复用
  - 错误模型统一：HTTP 非 2xx、上游 `errcode != 0`、非 JSON 响应全部包装为 `WeChatAPIError`
- ✨ **微信集成测试**（`data/channel_sync/tests/test_wechat_adapter.py`）
  - 覆盖 token 缓存/刷新、订阅消息 payload、客服文本消息 payload、上游 errcode、HTTP 500、环境变量缺失 fail-fast
  - `pytest --cov=data.channel_sync.wechat_adapter` 覆盖率 **90%**（8/8 通过）
  - `pytest -q data/channel_sync/tests` → **75 passed**；`ruff check data/channel_sync/wechat_adapter.py data/channel_sync/tests/test_wechat_adapter.py data/channel_sync/__init__.py` → **All checks passed**

#### 新增（T8.1 已完成）

- ✨ **闲鱼 Webhook + poller 兜底同步**（`data/channel_sync/`）

- `webhook_server.py`：`POST /webhook/xianyu` + `/healthz`，覆盖签名校验、时间戳过期、重复 event、非法状态迁移、审计落库、单 IP 限流
- `poller.py`：共享 `upsert_by_external_id` 幂等链路，支持 cursor 推进与 `poller_state` / `poller_run` 运行记录
- `audit.py` + `dao_extension.py` + `xianyu_adapter.py` + `signature.py`：补齐渠道同步所需审计、适配、验签与订单写库能力
- `data/channel_sync/tests/test_xianyu_channel.py`：129 个 `data/orders + data/channel_sync` 测试通过；`data.channel_sync` 覆盖率 90%，`ruff check data/channel_sync` 0 warning
- 修复关键缺陷：Webhook server 预热 SQLite 连接原先在主线程创建，server 线程复用时触发 `sqlite3.ProgrammingError`，导致 accepted/duplicate/illegal-transition 路径误报 500 且拒绝审计落库失败；现改为 schema bootstrap 后以 `check_same_thread=False` 重新打开连接

#### 新增（T2.3 已完成）

- ✨ **扎堆检测算法**（`data/crowd_db/crowd_detector.py`）
  - `detect_crowd_risk(plan, user_score, province) → list[RiskFinding]`：遍历方案每条志愿，匹配该分数段内的 crowd_db 记录，返回风险列表 + 替代方案
  - 风险等级映射：frequency ≥4 high / 2-3 medium / 1 low / 0 跳过
  - 院校模糊匹配（互相包含），专业可选（计划未指定专业时按院校命中）

#### 新增（T3.1 已完成）

- ✨ **27 省院校数据模型扩展溯源字段**（`data/crowd_db/{province}.json` + `loader.py`）
  - 27 省 JSON 顶层新增 6 字段：`source` / `source_url` / `source_type` / `data_year` / `confidence` / `last_updated`
  - 现有 26 省骨架数据：confidence=0.45，source_type=`manual_summary`，data_year=2025
  - 湖南数据：confidence=0.85，含 68 条推荐（专科批→省外顶尖，10 段连续 440-690 覆盖）
  - `CrowdDBLoader` 扩展 `warn_low_confidence` / `load_metadata(province) → 8 字段` / `list_supported_provinces()` / `list_provinces()` / `load_province` 对 confidence<0.5 发 `UserWarning`
  - 新增 `data/crowd_db/SCHEMA.md`：顶层/分数段/推荐条目三表 schema + `source_type` 枚举（`manual_summary` / `official_release` / `platform_scrape` / `derived`）+ 骨架文件约定
  - 测试：`data/crowd_db/tests/test_provenance.py` 9 用例（27 存在性、顶层字段、score_range schema、confidence 区间、loader 27 报告、metadata 8 字段、低 confidence 警告、端到端匹配），T2.1/T2.2/T2.3 46 用例无回归
  - 与 T2.3 协同：`crowd_detector._risk_level_from_frequency` 与 `CrowdRecommendation.risk_level` 在 frequency 0-5 边界完全一致

#### 新增（T3.2 已完成）

- ✨ **溯源字段查询 + 验证 API**（`data/crowd_db/loader.py` + `tests/test_provenance_query.py`）
  - 新增 dataclass `ProvenanceValidation`：含 `ok` / `errors` / `warnings` / `is_usable` / `summary` 5 字段 + `to_dict()`
  - 类常量：`USABLE_CONFIDENCE_THRESHOLD = 0.5` / `VALID_SOURCE_TYPES`（4 枚举）/ `ISO_DATE_PATTERN` / `REQUIRED_PROVENANCE_FIELDS`（7 字段）
  - `validate_provenance(data, province) → ProvenanceValidation`（@classmethod，不需 loader 实例）：校验字段类型/范围/枚举/日期格式，区分硬错误与软警告
  - `validate_province(province) → ProvenanceValidation`：加载 + 校验一体化
  - `validate_all() → dict[province, ProvenanceValidation]`：27 省一次性扫描
  - `filter_provinces(*, source_type, min_confidence, max_confidence, data_year, updated_since, updated_before, only_usable) → list[province]`：多维溯源过滤，按 `PROVINCE_FILE_MAP` 顺序返回
  - `get_provenance_report(*, only_usable, source_type) → dict`：汇总 `total` / `usable_count` / `failed_count` / `by_source_type` / `items`
  - 27 省现状：全部 schema 校验通过（`failed=0`），仅湖南 1 省 `is_usable=True`（confidence=0.85），26 省 low_confidence warning
  - 测试：`data/crowd_db/tests/test_provenance_query.py` **33 用例全通过**，覆盖 validate_all/27、validate_province 单省、validate_provenance 边界（None/空 dict/confidence 越界/source_type 非法/data_year 类型错/date 格式错/empty source warning）、filter_provinces 9 维 + 组合、get_provenance_report 5 统计项、未知省份 load_failed、ProvenanceValidation.to_dict、load_metadata 兼容性、validate_provenance 不可变性
  - 不破坏既有 API：`load_province` / `find_recommendations` / `find_recommendation_by_school` / `load_metadata` 行为与契约完全不变；T2.x 46 用例 + T3.1 9 用例 + T3.2 33 用例 = **88/88 通过**
  - 多种 plan 形态：dict / CrowdRecommendation / tuple / list
  - 支持注入 `loader` 便于测试，频率降序排序
  - 20 个单元测试覆盖：高/中风险识别、替代方案、分数段边界、模糊匹配、专业匹配、空/异常输入、部分命中、排序
- ✨ `data/crowd_db/tests/test_crowd_detector.py` — 20 个测试覆盖算法各分支

### 📅 计划中

- T5.5 覆盖率硬门槛（全局 ≥80% / 核心 =100% / E2E模拟通过）

---

## v2.0 (2026-06-11)

### 🎉 重大变化

#### 新增

- ✨ **规范检查Skill V2**：支持27个省份自动适配
  - 院校专业组模式（14省）
  - 专业+学校模式（8省）
  - 传统模式（5省）
- ✨ 省份规则库（`rules/provinces/`）
- ✨ 错误模式库（`rules/errors/`）
- ✨ 真实案例库（`docs/case-studies/`）
- ✨ 优化日志（`docs/optimization-log/`）
- ✨ 完整项目目录结构

#### 修复

- 🐛 修正"院校专业组"概念（原错误为"45个学校"）
- 🐛 修正调剂规则（原错误为"全校调剂"）
- 🐛 修正投档后规则（原错误为"退到下个志愿"）
- 🐛 移除主观概率（原错误为"35%、80%"）
- 🐛 修正选科一刀切（原错误为"所有会计都要求物+化+生"）

#### 改进

- ⚡ 院校数据从2025年位次精确化
- ⚡ 风险提示前置
- ⚡ 数据来源明确标注
- ⚡ 强调"以官方为准"

### 📝 起源事故

- 真实用户咨询：湖南578分/物化生
- 原方案出现致命错误（院校专业组概念错误）
- 用户质疑"是否符合规范"触发自查
- 创建本检查Skill防止错误复发

---

## v1.0 (2026-06-10 → 2026-06-11)

### 初始版本

- gaokao-college-advisor Skill
- 可视化报告脚本
- 1分钟/3分钟/7步三套问卷
- 邮件发送功能

### 已知问题

- ❌ 政策理解停留在2024年水平
- ❌ 数据主观化严重
- ❌ 缺乏方案检查机制
- ❌ 部分细节不符合本省规范

### 用户反馈

- "符合今年对应区域志愿填报规范吗？" ← 触发v2.0创建

---

## 📊 版本对比

| 维度       | v1.0 | v2.0          |
| ---------- | ---- | ------------- |
| 省份支持   | 湖南 | 27个          |
| 检查机制   | 无   | 规范检查Skill |
| 错误模式库 | 无   | 8+种错误      |
| 数据精度   | 主观 | 基于2025位次  |
| 风险提示   | 后置 | 前置          |
| 项目结构   | 散落 | 集中          |
| 文档体系   | 简单 | 完善          |

---

## 🎯 下一步

- 添加更多省份（覆盖完整30+省）
- 完善数据自动化对接
- 增强算法精度
- 完善UI/UX

详见 `docs/optimization-log/future-plan.md`
