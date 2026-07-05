<!-- 历史快照提示：本文件保留为历史审计材料，不再代表当前项目状态。 -->
> ⚠️ **历史快照（非当前真相源）**：本文件仅保留当时审查/收口结论。当前状态与执行顺序以 `docs/CURRENT_STATE.md`、`docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`、`docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`、`docs/plans/2026-07-05-review-remediation-systemic-fix-plan.md` 和 `reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md` 为准。

---

# 高考志愿填报系统严格全面 Review 报告

- 项目路径：`/home/long/project/gaokao-volunteer-system`
- 评审日期：2026-06-18
- 评审方式：文档审计 + 结构化代码审计 + 安全/数据治理/运行时补充审计 + 定点命令验证 + 定点测试复核
- 评审目标：识别项目真实状态、代码与运维质量、规划/设计/实现差距、对外承诺边界、隐藏安全问题与后续优先级

---

## 1. 执行结论

### 1.1 结论

本项目**不是完整的用户端 Web 自助 SaaS**。

当前更准确的定位仍是：

> **人工服务运营增强系统 + AI 审核增强链路**。
>
> 后台运营、订单、分享、渠道同步、AI 审核、规则真相源、专业目录、统一 CLI 回归入口已经形成；
> 用户端 Web 自助链路仍处在**本地 MVP / 目标态过渡**，尚未达到可以稳定对外承诺的完整商业闭环。

### 1.2 严格标准下的总体判断

> **项目有真实实现价值，但当前不宜按“完整 Web 自助产品”对外验收，也不宜按“安全/合规/恢复链已闭环”对外表述。**

更严格标准下，当前核心问题不是“没有代码”，而是：

1. **文档仍混写现状与目标态**，会误导评审、验收和对外承诺。  
2. **验证链仍高估质量**，尤其是 restore 真实性和 coverage 指标。  
3. **存在真实安全/授权/数据治理问题**，且部分已能构成可复现的利用链。  
4. **运行时与交付边界仍有假接线、可复现性不足和环境漂移问题**。  

### 1.3 综合评级

| 维度 | 评级 | 结论 |
| --- | --- | --- |
| 真实状态可追踪性 | B- | `CURRENT_STATE` 清楚，但其他文档持续漂移 |
| 产品定位与对外边界 | C+ | 总口径已收紧，正文仍有误导性承诺 |
| 架构与模块化 | B | 分层务实，域边界基本清楚 |
| 实现质量 | C+ | 主链可运行，但存在授权、文件路径、半实现状态机等问题 |
| 安全与权限边界 | C | 认证存在，授权与能力 URL 边界不足 |
| 数据治理与合规 | C- | 加密/脱敏有基础，但保留期与旁路数据治理仍不完整 |
| 测试与验证可信度 | C | 测试数量多，但 coverage 和部分文档型测试高估质量 |
| 运维与恢复可信度 | C- | 快照路径尚可，live verify 对 WAL 不可信 |
| 对外稳定交付准备度 | D+ | 更接近受控试运行，不是完整对外交付状态 |

---

## 2. 本次评审的事实基础

### 2.1 关键文档

- `docs/CURRENT_STATE.md`
- `README.md`
- `product/PRD.md`
- `product/ROADMAP.md`
- `product/MARKET_RESEARCH.md`
- `docs/TECH_ARCHITECTURE.md`
- `docs/IMPLEMENTATION_PLAN_v2.md`
- `docs/PAYMENT_DOMAIN_DESIGN.md`
- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- `docs/PROJECT_PLANNING_REALIGNMENT_2026-06-16.md`
- `docs/DATA_RETENTION_AND_DELETION.md`
- `docs/LEGAL_PRIVACY_BASELINE.md`
- `docs/PRIVACY_POLICY_DRAFT.md`
- `.github/workflows/ci.yml`
- `docker-compose.yml`
- `Dockerfile`
- `scripts/dev-verify.sh`
- `scripts/backup_snapshot.sh`
- `scripts/backup_verify.sh`

### 2.2 关键代码抽样

- `admin/app.py`
- `admin/auth.py`
- `admin/config.py`
- `admin/routes/auth.py`
- `admin/routes/orders.py`
- `admin/routes/notifications.py`
- `admin/routes/ui.py`
- `admin/routes/web_public.py`
- `admin/share_page.py`
- `admin/users.py`
- `data/orders/models.py`
- `data/orders/schema.py`
- `data/orders/crypto.py`
- `data/orders/intake_store.py`
- `data/orders/deletion_service.py`
- `data/orders/retention_cleanup.py`
- `data/customer_portal/token.py`
- `data/payments/service.py`
- `data/payments/dao.py`
- `data/payments/provider_requirements.py`
- `data/payments/providers/mock_gateway.py`
- `data/payments/providers/alipay_sim.py`
- `data/payments/providers/alipay.py`
- `data/notifications/email_service.py`
- `data/notifications/dispatcher.py`
- `data/share/permission.py`
- `data/share/short_link.py`
- `requirements-admin.txt`
- `requirements-dev.txt`

### 2.3 本次实际命令验证

已实际执行并观察结果：

1. 定点 pytest：

```bash
./.venv/bin/python -m pytest \
  tests/test_audit_engine_major_validation_phase2.py \
  admin/tests/test_payment_alipay_notify.py \
  tests/test_backup_workflow.py \
  tests/test_dev_verify_entrypoint.py \
  tests/test_cli_doctor_phase3.py -q
```

结果：`31 passed, 1 warning in 8.74s`

2. 更严格补充审计 pytest：

```bash
./.venv/bin/python -m pytest \
  admin/tests/test_web_public.py \
  admin/tests/test_order_status_page.py \
  admin/tests/test_p2_4_p2_5_secrets.py \
  tests/test_delivery_notification.py -q
```

结果：`45 passed, 1 warning in 4.49s`

3. 数据治理补充审计 pytest：

```bash
./.venv/bin/python -m pytest \
  admin/tests/test_order_info_upload.py \
  admin/tests/test_share_ui.py \
  admin/tests/test_order_deletion.py \
  admin/tests/test_order_info_form.py::test_portal_deletion_request_is_logged_and_visible_in_admin \
  data/share/tests/test_permission.py -q
```

结果：`54 passed, 1 warning in 2.28s`

4. 统一 CLI doctor：

```bash
./.venv/bin/python scripts/gaokao-cli doctor --json
```

结果要点：

- `ok: true`
- `province_count: 27`
- `active_rule_count: 298`
- `missing_evidence_rule_count: 0`

5. 生产配置 fail-closed 复核：

```bash
set -a && source .env.docker.example && set +a && ./.venv/bin/python - <<'PY'
from admin.config import load_settings
load_settings()
PY
```

结果：按预期失败，报错 `GAOKAO_PAYMENT_PROVIDER=mock 在生产环境被禁止`。

6. 公开健康检查响应复核：

```bash
env GAOKAO_ENV=dev \
  GAOKAO_JWT_SECRET=test-secret-12345678901234567890123456789012 \
  GAOKAO_PORTAL_TOKEN_SECRET=portal-secret-12345678901234567890123456789012 \
  GAOKAO_ORDERS_FERNET_KEY=test-orders-key \
  ./.venv/bin/python - <<'PY'
from admin.app import create_app
from fastapi.testclient import TestClient
app = create_app()
with TestClient(app) as client:
    r = client.get('/health')
    print(r.status_code)
    print(r.json())
PY
```

结果：`200`，且公开返回 `{'status': 'ok', 'env': 'dev', 'db_path': 'data/orders/admin.db', 'service': 'gaokao-admin', 'version': '0.1.0'}`。

7. 低权限后台账号越权复核：

```bash
# 通过 AdminUserRepo.create(..., role='viewer') 建低权限账号
# 再用其 Bearer token 调用后台订单接口
```

结果：`login_status = 200`，`orders_status = 200`。

8. 任意本地文件读取链复核：

```bash
# viewer 账号 PATCH audit_report=/etc/hosts
# 再推进订单到 delivered/completed
# 再访问 /portal/{token}/report
```

结果：`report_status = 200`，`contains_hosts_marker = true`。

9. 本地运行边界复核：

```bash
./.venv/bin/pip freeze | wc -l
python3 - <<'PY'
mods = ['pytest','fastapi','uvicorn','weasyprint','locust']
for name in mods:
    try:
        __import__(name)
        print(name, 'ok')
    except Exception as exc:
        print(name, type(exc).__name__)
PY
GAOKAO_SOURCE_ONLY=1 PYTHON_BIN=python3 bash -c 'source scripts/dev-verify.sh; ensure_venv; python --version' && python3 --version
```

结果：

- 当前本地 `.venv` 已装包数量：`82`
- 当前工作站系统 `python3` 直接导入 `pytest/fastapi/uvicorn/weasyprint/locust` 全部 `ModuleNotFoundError`
- `dev-verify.sh` 复用既有 `.venv` 时，`python --version = 3.11.13`；同机 `python3 --version = 3.12.3`

10. 环境现实边界：系统 `python3` 直接运行并不等于项目可运行；当前验证依赖仓库 `.venv`。

---

## 3. 项目当前真实状态

### 3.1 已验证的真实定位

以下结论被文档真相源与代码/命令共同支撑：

- 当前项目定位是**人工服务运营增强系统**，不是完整 Web 自助 SaaS。  
  证据：`docs/CURRENT_STATE.md:42-59`，`README.md:7-12`
- 已完成主线包括：后台运营、订单、分享、渠道同步、AI 审核、规则真相源、专业目录、统一 CLI 回归入口。  
  证据：`docs/CURRENT_STATE.md:46-51,62-75`
- T12 用户端 Web 自助只能表述为**已启动/实施中**；真实支付 acceptance、线上通知联调、线上交付调度仍未收口。  
  证据：`docs/CURRENT_STATE.md:96-115`
- 当前执行口径是：执行 Phase 1 / 1.5 / 2 已收口；下一阶段是执行 Phase 3 统一 CLI 命令面，未启动。  
  证据：`docs/CURRENT_STATE.md:25-38`

### 3.2 已确认修复的历史问题

以下问题**代码层面已修复**，不应继续按“当前未解决”表述：

- 支付回调不会再把 `refunded` payment 回写成 `paid`。  
  证据：`data/payments/service.py:194-289`
- 生产环境支付 provider fail-closed 已生效；`prod` 下只允许 `alipay`。  
  证据：`admin/config.py:155-173`
- 通知唯一键已包含 `channel`，多渠道事件不再天然冲突。  
  证据：`data/notifications/email_service.py:12-25`
- `audit run` 已从“假壳”变成真实调用 `RuleLoader + MajorsCatalogLoader + AuditEngine`。  
  证据：`data/rules/cli.py`，`data/rules/audit_engine.py`
- `backup_snapshot.sh` 已对 SQLite 使用 `sqlite3.backup()`，不再是裸文件复制。  
  证据：`scripts/backup_snapshot.sh:36-58`
- 公开下单链路要求 `GAOKAO_ORDERS_FERNET_KEY`，缺失即 503，不会降级为明文落盘。  
  证据：`admin/routes/web_public.py:174-183`，`data/orders/crypto.py:46-54`

---

## 4. 主要问题清单

## 4.1 P0 / 严重问题

### P0-1 `backup_verify.sh` 的 live staging 路径对 WAL SQLite 不可信

**问题**

`scripts/backup_verify.sh` 在 live 校验路径对 SQLite 用的是 `cp`，而不是 SQLite backup API，也没有处理 `-wal/-shm`。这意味着：

- 对开启 WAL 的 live DB，复制出来的副本可能**缺表或缺数据**；
- 文档声称“可直接对 live 数据做恢复演练”，但当前只对非 WAL / 已 checkpoint 场景可信。

**证据**

- `scripts/backup_verify.sh:33-43,70-79,128-155`
- `scripts/backup_snapshot.sh:36-58`
- `docs/BACKUP_AND_RECOVERY_PLAN.md:124-130`
- 定点审计实测：同类 WAL 临时库在 `backup_verify.sh <dir> --skip-smoke` 后出现 `tables=none`，而 `backup_snapshot.sh` 快照路径能保留数据。

**影响**

- 恢复演练可能“看起来成功”，实际副本不可恢复。
- 这是当前最重的运维阻断项。

---

### P0-2 coverage gate 被测试代码显著抬高，CI 绿灯不能真实代表业务代码覆盖质量

**问题**

`scripts/dev-verify.sh` 用 `--cov=.` 覆盖整个仓库，`coverage.xml` 明确包含 `tests/**` 和 `admin/tests/**`。这让测试代码覆盖测试代码本身，显著抬高 overall 指标。

**证据**

- `scripts/dev-verify.sh:63-71`
- `scripts/check_coverage_gate.py:16-22,64-83`
- `codecov.yml:30-39`
- 复核结果：
  - overall coverage ≈ `90.35%`
  - 非测试代码 coverage ≈ `82.31%`
  - `test_lines=8902`
  - `non_test_lines=8588`

**影响**

- “overall ≥ 80%”被系统性稀释。
- CI / 本地 verify 的通过不再等价于“应用代码覆盖达标”。

---

### P0-3 `PRD` 与 `TECH_ARCHITECTURE` 仍能误导读者把目标态当现状

**问题**

虽然 `CURRENT_STATE` 已收口，但核心对外文档仍存在两类严重漂移：

1. `PRD` 把 Web 当作当前售卖/交付渠道写入业务与定价；
2. `TECH_ARCHITECTURE` 同时描述 Current/Target，却包含大量不存在的路径、API、CLI 与测试名。

**证据**

- `product/PRD.md:472-523`
- `docs/TECH_ARCHITECTURE.md:384-444,617-628,726`
- `docs/API.md:147-213,244-299`
- 当前真相源反证：`docs/CURRENT_STATE.md:96-115,191-205`

**影响**

- 对外承诺失真
- 验收标准漂移
- 新成员 / 评审 / 商务容易按不存在的能力理解项目

---

### P0-4 订单路径字段可被后台写入任意本地路径，并经 portal 报告页读出

**问题**

`audit_report` / `pdf_path` 是后台允许更新的字段；portal 报告页在阶段满足后会直接读取这些路径指向的本地文件内容或直接下发文件响应，缺少基目录白名单、后缀限制与来源校验。

这不是抽象风险，已经可以组合成**真实本地文件读取链**。

**证据**

- `admin/routes/orders.py:104-106`
- `admin/routes/orders.py:528-555`
- `admin/routes/web_public.py:536-558`
- `admin/routes/web_public.py:2176-2189`
- 定点实跑：把订单 `audit_report` 更新成 `/etc/hosts`，再推进状态到 `delivered/completed` 后访问 `/portal/{token}/report`，结果 `report_status = 200`，`contains_hosts_marker = true`

**影响**

- 应用可读取宿主机本地文本文件并通过 portal 对外返回。
- 一旦再叠加 token 泄露或低权限后台账号，风险进一步扩大。

---

## 4.2 P1 / 高优先级问题

### P1-1 `audit run` 已可执行，但实际规则审计广度远低于文档声称范围

**问题**

`AuditEngine.audit_plan()` 的实际覆盖面仍很窄：

- 省规则侧当前只做 `RULES.max_volunteers`
- major 侧只做 `MAJORS.not_found` / `MAJORS.non_active`
- 没有实现 mode、retrieval_rule、collection_count、subject_mode、数据完整性等检查

**证据**

- `data/rules/audit_engine.py:43-78`
- `data/rules/cli.py` 的 `audit run`
- 对应测试只覆盖 `max_volunteers` 与 major 状态

**影响**

- 当前 CLI 输出“通过”并不等价于方案已通过完整省规则审计。

---

### P1-2 删除/匿名化链路缺少文档要求的保留例外 / 支付审计期门禁

**问题**

删除与匿名化能力已扩围，但仍未真正执行“受保留约束订单不得删除/匿名化”的合规逻辑。

**证据**

- `admin/routes/orders.py:609-645`
- `data/orders/deletion_service.py:50-139`
- `docs/DATA_RETENTION_AND_DELETION.md:23-35`
- 测试主要覆盖 happy path，没有“应拒绝删除”的用例

**影响**

- 支付审计与争议保留策略无法靠代码强制执行。

---

### P1-3 后台只做认证不做角色授权，任意已认证账号都拥有完整订单后台能力

**问题**

后台当前只有“已认证”门槛，没有“角色授权”门槛。`role` 字段存在，但没有被任何后台订单路由使用。

**证据**

- `admin/auth.py:112-141` 的 `get_current_user()` 只校验 token / user / is_active，直接 `return user`
- `admin/routes/orders.py:347-354,377-383,411-445,528-533` 的订单列表/导出/详情/创建/更新只依赖 `Depends(get_current_user)`
- `admin/db.py:130-149` 允许创建任意 `role` 的后台账号
- 全仓未找到 `require_role` 实现或调用
- 定点实跑：`AdminUserRepo.create(..., role='viewer')` 建低权限账号后，`login_status = 200`，随后 `orders_status = 200`

**影响**

- 当前一旦出现非 admin 账号（人工建号、脚本造号、未来扩角色），会直接获得完整后台订单能力。
- 这不是“以后可能有问题”，而是当前角色字段已经存在、但不参与授权决策。

---

### P1-4 Portal token 作为 Bearer 能力被放进 URL / 支付回跳参数，并明文持久化到 payments 表

**问题**

Portal token 当前同时出现在：

- `/portal/{token}/status`、`/portal/{token}/info` 等能力 URL
- 模拟支付 checkout URL 的查询串 `?token=...`
- 真实支付宝 `return_url` 的查询串 `?token=...`
- `payments.checkout_token` 明文字段

**证据**

- `admin/routes/web_public.py:195-205,293-298`
- `data/payments/providers/mock_gateway.py:16-24`
- `data/payments/providers/alipay_sim.py:17-25`
- `data/payments/providers/alipay.py:49-82`
- `data/payments/service.py:159-166`
- `data/payments/dao.py:21-23,71-84,189-191`
- 定点实跑：公开下单返回的 `checkout_url` 包含 token，`portal_status_url` 本身也是能力 URL

**影响**

- Portal token 的泄露面扩展到浏览器历史、代理日志、第三方支付回跳链、数据库快照。
- 由于该 token 能访问状态、资料、通知、报告等整条 portal 链路，风险高于普通临时 query 参数。

---

### P1-5 `retention cleanup` 的 180 天匿名化链路没有处理 `delivery_notifications.payload_json`

**问题**

定时匿名化作业只更新 `orders`、清空 `payments.callback_payload`、清空 `order_intakes.payload_json`，但没有处理 `delivery_notifications.payload_json`。

**证据**

- `data/orders/retention_cleanup.py:70-91`
- `data/orders/deletion_service.py:91-127`
- `data/notifications/email_service.py:12-25`
- `data/notifications/dispatcher.py:81-95,118-145`

**影响**

- 通知审计表仍可残留 `customer_email`、`audit_report`、`plan_file`、`pdf_path`、发送结果等信息。
- 形成“订单已匿名化，但旁路通知数据仍可回溯”的保留期不一致。

---

### P1-6 后台通知与运维审计接口直接返回完整 payload/details，缺少服务端脱敏边界

**问题**

后台通知审计与运维告警审计受 JWT 保护，但返回/展示的是原始 `payload_json` 与 `details`。其中通知 payload 已包含 `customer_email`、`pdf_path` 等敏感或内部路径字段。

**证据**

- `data/orders/dao.py:601-614`
- `admin/routes/notifications.py:139-200`
- `admin/routes/notifications.py:203-267`
- `admin/routes/notifications.py:270-325`

**影响**

- 后台任一拥有 token 的账号可直接获取更多 PII / 内部路径，而不受字段级最小暴露控制。

---

### P1-7 运行时契约与依赖可复现性仍弱

**问题**

当前至少有三层运行时/交付契约没有收敛：

1. `docker-compose` 传入的 `GAOKAO_ADMIN_BIND/PORT` 对应用监听参数不生效；镜像命令把 `--host 0.0.0.0 --port 8000` 写死。  
2. 依赖无锁：仓库只有 `requirements-admin.txt` 与 `requirements-dev.txt`，没有 lock/constraints；CI cache key 还只 hash `requirements-dev.txt`，但会同时安装 `requirements-admin.txt`。  
3. `dev-verify.sh` 会静默复用既有 `.venv`，不会按当前 `PYTHON_BIN` 重建；本地通过不等于覆盖了当前系统解释器或声明矩阵。  

**证据**

- `docker-compose.yml:12-14,33-34`
- `Dockerfile:25`
- `admin/app.py` 只读 CLI host/port，不读对应 env
- `requirements-admin.txt:4-14`
- `requirements-dev.txt:5-18`
- `.github/workflows/ci.yml:36-67`
- `scripts/dev-verify.sh:25-50`
- 定点实跑：
  - 带 `GAOKAO_ADMIN_BIND=9.9.9.9 GAOKAO_ADMIN_PORT=9999` 启动，日志仍是默认监听
  - `GAOKAO_SOURCE_ONLY=1 PYTHON_BIN=python3 ... ensure_venv; python --version` 输出仍为 `3.11.13`
  - 同机 `python3 --version = 3.12.3`

**影响**

- 运行配置存在“假接线”；
- CI / 本地无法证明同提交一定落到同一依赖树；
- 本地验证通过不等于当前系统解释器也被验证过。

---

### P1-8 同意记录落库仍停留在布尔/版本字段，未达到文档自身最低要求

**问题**

文档要求至少记录 `privacy_accepted_at`、`service_terms_accepted_at`、`consent_channel`、`consent_given_at`、`consent_operator` 等字段；当前落库仍只有 `consent_version`、`consent_scope` 与几个布尔值。

**证据**

- `docs/LEGAL_PRIVACY_BASELINE.md:79-92,117-130`
- `admin/routes/web_public.py:1842-1863`
- `data/orders/intake_store.py:68-100`
- 代码中未发现上述审计元字段的实际落库实现

**影响**

- 只能证明“勾选过”，不能证明“何时、由谁、通过什么渠道同意”。

---

### P1-9 联系邮箱 `customer_email` 明文落库，与手机号/身份证加密策略不一致

**问题**

手机号与身份证会加密落盘；联系人邮箱 `customer_email` 则直接明文写进 `orders`，并继续进入通知 payload。

**证据**

- `data/orders/schema.py:26-31`
- `data/orders/models.py:57-63,110-127`
- `data/orders/tests/test_models.py:46-57`
- `data/orders/dao.py:601-614`

**影响**

- 联系邮箱保护强度明显低于手机号/身份证。
- 数据库泄露时，邮箱更容易被直接用于批量营销或钓鱼。

---

### P1-10 失败支付状态机半实现：UI 有 `payment_failed`，代码缺真实落库路径

**问题**

Portal/UI 已建模 `payment_failed` 阶段，但当前并没有真实 `status='failed'` 的业务写入路径；非成功回调直接抛 `PaymentError("payment status not successful")`。

**证据**

- `admin/routes/web_public.py:613-635`
- `data/payments/service.py:194-205`
- `data/payments/dao.py:13-23`

**影响**

- 页面状态机与服务状态机不一致。

---

### P1-11 `backup_verify.sh --from-backup` 可绕过 manifest 严格校验

**问题**

`verify_manifest_if_present()` 在 manifest 缺失时只打印 skip 并继续，因此 `--from-backup` 更像“恢复 smoke”，不是“正式快照完整性校验”。

**证据**

- `scripts/backup_verify.sh:91-125`
- `tests/test_backup_restore_service_level.py`

**影响**

- 恢复 smoke 与正式快照校验语义混淆。

---

### P1-12 `ROADMAP` 状态语义漂移

**问题**

同一能力在不同文档中既像“未来计划”，又像“已本地验证 / 已启动”，缺少以下三层分隔：

- 已本地验证
- 待线上验收
- 目标态里程碑

**证据**

- `docs/CURRENT_STATE.md:52-55,98-115`
- `product/ROADMAP.md:270-288,333-345,427-445`
- `product/README.md:113-123`

**影响**

- 容易同时低估已做工作，又高估线上 readiness。

---

## 4.3 P2 / 中优先级问题

### P2-1 确认页前端使用 `innerHTML` 回填用户输入，存在 DOM XSS sink

**证据**

- `admin/routes/web_public.py:1866-1879`

**说明**

这更偏用户侧 / 自触发 DOM XSS，不如本地文件读取链严重，但按严格标准仍应记录。

---

### P2-2 前台附件上传接口把服务器绝对 `storage_path` 写入 payload 并回传给持 token 用户

**证据**

- `admin/routes/web_public.py:363-385`
- `admin/routes/web_public.py:401-435`
- `data/orders/intake_store.py:68-97`
- `admin/tests/test_order_info_upload.py:59-65`

**影响**

- 持 token 用户可获知服务器目录结构与订单目录命名。

---

### P2-3 前台删除申请日志以明文 JSONL 持久化，但未纳入保留期治理

**证据**

- `admin/routes/web_public.py:112-129`
- `admin/config.py` 默认 `deletion_request_log_path`
- `admin/routes/notifications.py:93-115`
- `admin/tests/test_order_info_form.py::test_portal_deletion_request_is_logged_and_visible_in_admin`

**影响**

- 删除申请本身形成新的旁路 PII 数据集。

---

### P2-4 分享链路 allowlist 与访问遥测边界仍偏宽

**问题**

1. `edit/admin` 分享权限 allowlist 仍允许联系方式、身份证号、内部交付路径等高敏字段进入 `rendered.payload`；  
2. `short_links.db` 中的 `share_link_access_events(visitor_token/ip/user_agent)` 有落盘，但现有保留期文档未把它纳管。  

**证据**

- `data/share/permission.py:47-83,269-309`
- `data/share/tests/test_permission.py:298-300`
- `data/share/short_link.py:298-311,499-536,756-763`

**影响**

- allowlist 已存在，但边界仍过宽；
- 分享访问遥测属于已落盘、未纳管数据。

---

### P2-5 `docker-compose.yml` 是 dev/local smoke 模板，不是生产部署定义

**证据**

- `docker-compose.yml:1-2`
- dev 默认值能通过 `load_settings()`；同值切到 prod 会被 provider fail-closed 拒绝

**影响**

- 容易给出“部署模板已审过”的错误安全感。

---

### P2-6 健康检查公开暴露内部环境与数据库路径

**证据**

- `admin/routes/health.py:13-25`
- 本次实测公开返回 `env` / `db_path` / `service` / `version`

**影响**

- 为外部探测者提供额外环境情报。

---

### P2-7 文档对 `python3` 的直接使用表述过宽，容易掩盖真实前提

**问题**

当前工作站上，系统 `python3` 直接运行并不能导入项目依赖；真实前提是“先建并激活装好依赖的 venv”。

**证据**

- 系统 `python3` 直接导入 `pytest/fastapi/uvicorn/weasyprint/locust` 全部 `ModuleNotFoundError`
- `README.md`、`INSTALL.md` 多处直接写 `python3 ...`
- `dev-verify.sh` 会静默复用既有 `.venv`

**说明**

这不等于“Python 3.12 不支持”。更准确的结论是：**系统解释器直跑不可用；已装依赖的 venv 才是当前真实运行边界。**

---

### P2-8 容器内 PDF 生成边界未被仓库验证闭环

**问题**

宿主 `.venv` 上 WeasyPrint PDF smoke 能成功；但 `Dockerfile` 只做 pip install，没有任何容器内 PDF 生成 smoke 或依赖断言，因此仓库当前**不能证明** `python:3.12-slim` 容器内同样能稳定生成 PDF。

**证据**

- `skills/gaokao-audit/scripts/report_generator.py`
- `requirements-admin.txt:10-11`
- `Dockerfile:16-19`

**说明**

这是“未被证明的交付边界”，不是本次已验证的运行失败事实。

---

## 5. 已确认做得好的部分

这些不是“文档声称”，而是本次确认过的正向事实：

1. **配置 fail-closed 意识明显提升**  
   prod 下支付 provider、portal token secret、payment webhook secret 都有真实门禁。  
   证据：`admin/config.py`

2. **支付与订单状态已明确分离**  
   `PaymentService.handle_webhook()` / `request_refund()` 都在同事务内推进 payment 与 order，且退款终态回调幂等已补齐。  
   证据：`data/payments/service.py`

3. **通知模型比 6/17 评审基线更可信**  
   唯一键已含 `channel`；`station` 与 `email` 生命周期被区分。  
   证据：`data/notifications/email_service.py`，`data/notifications/dispatcher.py`

4. **规则真相源、专业目录、doctor 命令面已初步成形**  
   `gaokao-cli doctor --json` 能给出真实状态，说明 CLI 层已从散乱脚本向统一命令面过渡。  
   本次已实际验证。

5. **仓库对“当前不是完整 Web SaaS”这一总口径已有正确自我约束**  
   这点在 `CURRENT_STATE` 与顶层 `README` 中是清楚的。  
   证据：`docs/CURRENT_STATE.md`，`README.md`

---

## 6. 规划 / 设计 / 实现差距汇总

### 6.1 规划 vs 现状

- 规划文档仍倾向把 Web 自助与支付当成中期主线能力；
- 现状实际上仍以人工服务运营链路为主，Web 只是本地 MVP 过渡。

### 6.2 设计 vs 实现

- 设计文档把规则审计描述得更广；
- 实现目前只有 `max_volunteers + majors status` 这一层。

### 6.3 文档 vs 工程事实

- 文档已说“最小恢复基线已具备”；
- 但 live verify 在 WAL 场景不可信，这说明“备份存在”与“可恢复性成立”之间仍有断层。

### 6.4 测试数字 vs 真实质量

- 定点 pytest 可以过；
- overall coverage 也高；
- 但 coverage 指标被测试代码显著抬高，因此不能直接等价为“业务代码质量高”。

### 6.5 安全与数据治理

- 认证存在，但授权边界不完整；低权限角色与后台能力之间没有真正隔离。  
- Portal token、报告路径、附件路径、删除申请日志、分享遥测与通知 payload 共同说明：系统尚未形成统一的“能力 URL / 敏感路径 / 旁路数据”的最小暴露模型。  
- PII 保护策略不一致：手机号/身份证已加密，邮箱仍明文；删除/匿名化已扩围，但同意记录与保留期治理仍不足。  

### 6.6 依赖与运行时

- 当前可运行性高度依赖本地 `.venv` 现状；仓库缺少锁文件与漏洞审计内建入口。  
- `dev-verify` 证明的是当前 `.venv` 下可过，不等于供应链可复现，也不等于当前系统解释器被重新验证过。  
- 容器交付边界仍有未被证明的部分，特别是 PDF 生成能力。  

---

## 7. 下一阶段建议优先级

## 7.1 必须先做（P0）

1. **修复 `backup_verify.sh` 的 live SQLite staging**  
   与 `backup_snapshot.sh` 一样改为 SQLite backup API，或显式处理 WAL/SHM。

2. **重做 coverage gate 口径**  
   overall 指标排除 `tests/**`、`admin/tests/**`、纯文档/脚本样板；保证 CI 的 overall 代表应用代码。

3. **文档治理：先修 `PRD` 和 `TECH_ARCHITECTURE`**  
   去掉把 Web 当成当前售卖/交付渠道的表达，拆分 Current / Target，删除不存在路径、CLI、API、测试名。

4. **阻断通过订单路径字段触发的本地文件读取链**  
   `audit_report` / `pdf_path` / `plan_file` 必须改成受控基目录、受控来源、受控后缀；portal report/download 不应直接信任任意本地路径。

## 7.2 高优先（P1）

5. **补后台角色授权**  
   至少明确“只有 admin 可访问后台订单写能力”；如果保留 `role` 字段，就必须真正执行 RBAC，而不是只做认证。

6. **收紧 Portal token 传播边界**  
   不再把高权限 token 当 query 参数在支付回跳/checkout URL 中传播；减少或取消 `checkout_token` 明文持久化。

7. **补齐 retention / anonymize 的跨表治理**  
   至少把 `delivery_notifications.payload_json`、删除申请日志、分享遥测纳入统一保留期策略。

8. **决定 `audit run` 的真实 contract**  
   要么把文档降到真实范围；要么补齐 mode / retrieval_rule / collection_count / 数据完整性等检查。

9. **修复运行时契约漂移**  
   - 让 compose 的 host/port/env 契约真实生效，或删除假接线配置  
   - 增加 lock / constraints 机制  
   - 把 CI cache key 与运行依赖对齐  
   - 让 `dev-verify` 显式检查 venv 解释器漂移  

10. **把失败支付做成真实状态机，或删掉死分支**  

11. **把 `backup_verify.sh` 划分成两种模式**  
   `live-smoke` 与 `snapshot-verify`（强制 manifest）。

## 7.3 中优先（P2）

12. **收紧 portal 前端 HTML 安全面**  
   报告 HTML 至少加白名单净化或沙箱 iframe；确认页去掉 `innerHTML` 拼接用户输入。

13. **为后台审计接口建立字段级脱敏 / allowlist**  
   通知 payload、ops alert details、删除申请日志都不应默认全量透传。

14. **补齐同意记录审计字段与邮箱保护策略**  
   至少补 `*_accepted_at`、`consent_channel`、`consent_operator`；明确 `customer_email` 是加密、哈希索引还是显式例外。

15. **把公开健康检查降到最小暴露**  
   只返回 readiness 信号，不返回 `db_path` / `env` / 详细版本。

16. **把文档中的 `python3` 直跑表述改成明确的 venv 前提**  

17. **为容器内 PDF 生成增加真实 smoke / CI 验证**  

---

## 8. 最终判断

### 8.1 如果问题是“这个项目有没有价值？”

有。

它已经不是一个纯文档仓库，也不是只有 demo 的原型。后台、订单、支付域、通知域、规则真相源、专业目录、统一 CLI 都有真实实现和真实测试基础。

### 8.2 如果问题是“它现在是不是一个可稳定对外承诺的完整产品？”

不是。

### 8.3 如果问题是“它最真实的成熟度是什么？”

> **内部可演示 / 受控试运行 / 人工运营增强系统。**  
> 不是完整的 Web 自助商业产品。

### 8.4 如果只用一句话概括本次更严格 review

> **主链代码比 6/17 基线更健康，但授权边界、数据治理、恢复真实性、运行时契约和文档现状仍明显高估了项目的可交付程度。**

---

## 9. 关键证据清单

- `docs/CURRENT_STATE.md:25-38,42-59,96-115,191-205`
- `README.md:7-12`
- `product/PRD.md:472-523`
- `product/ROADMAP.md:270-288,333-345,427-445`
- `product/README.md:113-123`
- `docs/TECH_ARCHITECTURE.md:384-444,617-628,726`
- `admin/auth.py:112-141`
- `admin/routes/orders.py:88-109,347-398,411-445,528-607`
- `admin/routes/notifications.py:139-325`
- `admin/routes/health.py:13-25`
- `admin/routes/web_public.py:112-129,174-183,195-205,293-298,363-385,401-435,536-558,613-677,1842-1879,1955-1967,2176-2189`
- `admin/share_page.py`
- `data/customer_portal/token.py:24-61`
- `data/orders/models.py:57-63,110-127,157-175`
- `data/orders/schema.py:26-31`
- `data/orders/intake_store.py:68-100`
- `data/orders/deletion_service.py:91-127`
- `data/orders/retention_cleanup.py:70-91`
- `data/orders/dao.py:601-614`
- `data/orders/crypto.py:46-54`
- `data/payments/service.py:159-166,194-289`
- `data/payments/dao.py:21-23,71-84,189-191`
- `data/payments/providers/mock_gateway.py:16-24`
- `data/payments/providers/alipay_sim.py:17-25`
- `data/payments/providers/alipay.py:49-82`
- `data/notifications/email_service.py:12-25`
- `data/notifications/dispatcher.py:81-95,118-145`
- `data/share/permission.py:47-83,269-309`
- `data/share/short_link.py:298-311,499-536,756-763,844-922`
- `docs/DATA_RETENTION_AND_DELETION.md:11-18,23-35`
- `docs/LEGAL_PRIVACY_BASELINE.md:79-92,117-130`
- `requirements-admin.txt:4-14`
- `requirements-dev.txt:5-18`
- `Dockerfile:16-25`
- `docker-compose.yml:1-36`
- `.github/workflows/ci.yml:36-67`
- `scripts/dev-verify.sh:25-50,53-81`
- `scripts/backup_snapshot.sh:36-58,176-198`
- `scripts/backup_verify.sh:70-223`

---

## 10. 本次实际验证摘要

- 定点 pytest：`31 passed`
- 更严格补充审计 pytest：`45 passed`
- 数据治理补充审计 pytest：`54 passed`
- `gaokao-cli doctor --json`：`ok=true`
- `.env.docker.example` 在 prod 下按预期 fail-closed
- 低权限账号实测可访问后台订单接口：`orders_status = 200`
- 通过 `audit_report=/etc/hosts` + portal report 可复现本地文件读取：`report_status = 200`，`contains_hosts_marker = true`
- 公开 `/health` 实际暴露 `env` 与 `db_path`
- 当前 `.venv` 已装包数：`82`
- 系统 `python3` 直跑无法导入项目关键依赖；当前真实运行边界依赖 `.venv`
- `dev-verify` 会静默复用既有 `.venv`，未自动纠正解释器漂移

---

本报告对应当前工作树审计结论，不等价于历史报告快照。