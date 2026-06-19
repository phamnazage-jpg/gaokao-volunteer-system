# Strict Review Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 按 2026-06-18 严格 review 报告收口 P0/P1/P2 整改项，先修会造成错误对外承诺、错误安全边界、错误恢复结论和错误验证结论的问题，再补运行时契约、数据治理和文档收口。

**Architecture:** 继续沿用现有 Python/FastAPI/SQLite 单仓架构，不引入新基础设施。先修底层不变量：恢复链真实性、权限边界、路径信任边界、token 传播边界、验证链真实性；再修跨表 retention、运行时契约、同意记录与数据治理；最后补文档、前端 sink 和部署证明。所有任务按 TDD 和最小改动推进，每个任务必须有独立回归测试与独立提交。

**Tech Stack:** Python 3.11/.venv, FastAPI, sqlite3, pytest, bash scripts, Markdown docs, GitHub Actions

---

## Phase 0: Documentation Discovery and Contract Freeze

### Task 0: 固化整改真相源与禁止回归的契约

**Files:**
- Read: `reports/STRICT_COMPREHENSIVE_REVIEW_2026-06-18.md`
- Read: `docs/CURRENT_STATE.md`
- Read: `docs/TECH_ARCHITECTURE.md`
- Read: `docs/DATA_RETENTION_AND_DELETION.md`
- Read: `docs/LEGAL_PRIVACY_BASELINE.md`
- Read: `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- Read: `docs/BACKUP_AND_RECOVERY_PLAN.md`
- Read: `docs/plans/2026-06-17-comprehensive-review-remediation.md`
- Create: `docs/plans/2026-06-18-strict-review-remediation-plan.md`

**Step 1: 提炼唯一真相源**

把本次整改的输入固定为：

- 状态真相：`docs/CURRENT_STATE.md`
- 问题真相：`reports/STRICT_COMPREHENSIVE_REVIEW_2026-06-18.md`
- 运行时门禁：`admin/config.py`, `scripts/dev-verify.sh`, `.github/workflows/ci.yml`
- 数据治理基线：`docs/DATA_RETENTION_AND_DELETION.md`, `docs/LEGAL_PRIVACY_BASELINE.md`

**Step 2: 写计划前的禁止事项**

实施阶段必须遵守：

- 不新增第二套 auth/RBAC 机制；沿用 `admin/auth.py` 与路由依赖模式。
- 不把 `audit_report` / `pdf_path` 继续当任意自由文本路径。
- 不再增加新的 query-token 能力 URL。
- 不用“补文档解释”替代代码修复。
- 不用“跳过 manifest”或“复制 live db”伪造恢复成功。

**Step 3: 计划作者自检**

确认每个后续任务都满足：

- 精确文件路径
- 先写失败测试
- 明确验证命令
- 明确不该做什么

**Verification checklist:**
- 重新打开 `reports/STRICT_COMPREHENSIVE_REVIEW_2026-06-18.md`，确认后续任务覆盖 P0 和前六个 P1。

**Anti-pattern guards:**
- 不发散到“重写系统”
- 不把 P2 任务插队到 P0/P1 前面

---

## Phase 1: P0 Blocking Fixes

### Task 1: 修复 `backup_verify.sh` 的 live SQLite staging，不再对 WAL 数据库做裸复制

**Files:**
- Modify: `scripts/backup_verify.sh`
- Modify: `docs/BACKUP_AND_RECOVERY_PLAN.md`
- Modify: `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- Test: `tests/test_backup_workflow.py`
- Test: `tests/test_backup_restore_service_level.py`

**Step 1: 先写失败测试**

在 `tests/test_backup_workflow.py` 增加一个针对 live WAL 库的回归测试。测试形状：

```python
def test_backup_verify_live_copy_handles_wal_sqlite(tmp_path):
    # 1. 建 WAL sqlite
    # 2. 写入数据但不手动 checkpoint
    # 3. 调 backup_verify.sh 的 live staging 路径
    # 4. 断言 staged 库仍能读到原表和原数据
```

在 `tests/test_backup_restore_service_level.py` 增加一个约束：

```python
def test_backup_verify_live_mode_uses_sqlite_backup_for_db_files(...):
    # 断言 live verify 后的恢复副本不是空库/缺表
```

**Step 2: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
```

Expected:

- FAIL，原因是当前 `backup_verify.sh` live 路径使用 `cp`，WAL 数据无法可靠复制。

**Step 3: 最小实现**

在 `scripts/backup_verify.sh`：

- 复用 `backup_snapshot.sh` 的 Python `sqlite3.backup()` 方案，不再裸复制 `.db`
- 明确处理 `-wal` / `-shm` 场景
- 把 live staging 与 `--from-backup` staging 逻辑拆开命名，避免混淆

可接受的 shell/Python 片段方向：

```bash
python3 - <<'PY'
import sqlite3
src = sqlite3.connect(source)
dst = sqlite3.connect(target)
src.backup(dst)
dst.close()
src.close()
PY
```

**Step 4: 收口文档**

更新 `docs/BACKUP_AND_RECOVERY_PLAN.md` 和 `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`：

- 明确 live verify 现在如何做 SQLite staging
- 明确 `live-smoke` 与 `snapshot-verify` 的差异

**Step 5: 重新运行测试**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
```

Expected:

- PASS

**Step 6: Commit**

```bash
git add scripts/backup_verify.sh docs/BACKUP_AND_RECOVERY_PLAN.md docs/DELIVERY_RETENTION_OPS_RUNBOOK.md tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
git commit -m "fix: make backup verify safe for wal sqlite"
```

**Anti-pattern guards:**
- 不允许继续用 `cp` 复制 live sqlite
- 不允许只改文档不改脚本

---

### Task 2: 重做 coverage gate，让 CI 指标只代表应用代码

**Files:**
- Modify: `scripts/dev-verify.sh`
- Modify: `scripts/check_coverage_gate.py`
- Modify: `codecov.yml`
- Test: `tests/test_dev_verify_entrypoint.py`
- Create or Modify: `tests/test_coverage_gate_rules.py`

**Step 1: 写失败测试**

在 `tests/test_dev_verify_entrypoint.py` 或新建 `tests/test_coverage_gate_rules.py` 增加两个断言：

```python
def test_dev_verify_excludes_test_packages_from_coverage_args():
    script = Path("scripts/dev-verify.sh").read_text(encoding="utf-8")
    assert "--cov=tests" not in script
    assert "--cov=admin/tests" not in script


def test_coverage_gate_ignores_test_files_in_ratio():
    # 给 check_coverage_gate.py 喂一个包含 tests 和非 tests 的 coverage xml fixture
    # 断言只按非测试代码统计 gate
```

**Step 2: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_dev_verify_entrypoint.py tests/test_coverage_gate_rules.py
```

Expected:

- FAIL，当前脚本与 gate 逻辑仍把测试代码计入 overall。

**Step 3: 最小实现**

- 在 `scripts/dev-verify.sh` 中把覆盖目标改成只针对应用代码目录，例如：
  - `--cov=admin`
  - `--cov=data`
  - 如有脚本要纳管，再单独显式列出
- 在 `scripts/check_coverage_gate.py` 中忽略：
  - `tests/`
  - `admin/tests/`
  - 文档型 fixture / 计划文件
- 在 `codecov.yml` 中同步排除同类路径

**Step 4: 重新跑测试**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_dev_verify_entrypoint.py tests/test_coverage_gate_rules.py
```

Expected:

- PASS

**Step 5: 追加一次真实门禁 smoke**

Run:

```bash
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

Expected:

- PASS
- coverage 计算口径不再把测试代码当主体

**Step 6: Commit**

```bash
git add scripts/dev-verify.sh scripts/check_coverage_gate.py codecov.yml tests/test_dev_verify_entrypoint.py tests/test_coverage_gate_rules.py
git commit -m "fix: make coverage gate reflect application code only"
```

**Anti-pattern guards:**
- 不允许靠降低阈值“修复”问题
- 不允许直接移除 coverage gate

---

### Task 3: 收口产品/架构文档，把 Current 与 Target 明确拆开

**Files:**
- Modify: `docs/CURRENT_STATE.md`
- Modify: `README.md`
- Modify: `product/PRD.md`
- Modify: `product/ROADMAP.md`
- Modify: `product/MARKET_RESEARCH.md`
- Modify: `docs/TECH_ARCHITECTURE.md`
- Modify: `docs/API.md`
- Test: `tests/test_design_docs_substantive.py`

**Step 1: 写失败测试**

在 `tests/test_design_docs_substantive.py` 增加：

```python
def test_prd_and_architecture_do_not_present_web_saas_as_current_state():
    prd = (REPO_ROOT / "product" / "PRD.md").read_text(encoding="utf-8")
    arch = (DOCS_DIR / "TECH_ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "当前完整 Web 自助 SaaS" not in prd
    assert "不存在的路径" not in arch  # 用更精确的字符串断言真实条目
```

再补一个路径存在性测试：

```python
def test_tech_architecture_only_references_existing_current_paths():
    # 从文档中抽取被标为 current 的关键路径并断言仓库存在
```

**Step 2: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_design_docs_substantive.py
```

Expected:

- FAIL，原因是 PRD / TECH_ARCHITECTURE 仍混写目标态或引用不存在对象。

**Step 3: 最小实现**

按以下原则改文档：

- `README.md` 与 `CURRENT_STATE.md` 保持同一定位用语
- `product/PRD.md` 中 Web 自助流程统一改成“目标态 / 试点态 / 本地 MVP”
- `product/ROADMAP.md` 把“已本地验证 / 待线上验收 / 目标态里程碑”拆层
- `docs/TECH_ARCHITECTURE.md` 改成：
  - Current
  - In Progress
  - Target
- 删除 `API.md` / `TECH_ARCHITECTURE.md` 中不存在的路径、接口、CLI、测试名

**Step 4: 重新运行测试**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_design_docs_substantive.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add docs/CURRENT_STATE.md README.md product/PRD.md product/ROADMAP.md product/MARKET_RESEARCH.md docs/TECH_ARCHITECTURE.md docs/API.md tests/test_design_docs_substantive.py
git commit -m "docs: align current state and target architecture claims"
```

**Anti-pattern guards:**
- 不允许保留“假 current”路径
- 不允许仅加免责声明但正文继续写成已上线能力

---

### Task 4: 阻断 `audit_report/pdf_path/plan_file` 任意路径信任链

**Files:**
- Modify: `admin/routes/orders.py`
- Modify: `admin/routes/web_public.py`
- Modify: `data/orders/dao.py` or `data/orders/models.py`（仅在现有模型需要约束时）
- Test: `admin/tests/test_routes_orders.py`
- Test: `admin/tests/test_web_public.py`

**Step 1: 写失败测试**

在 `admin/tests/test_routes_orders.py` 增加：

```python
def test_patch_order_rejects_audit_report_outside_allowed_report_dir(...):
    resp = client.patch(
        "/api/orders/GKO-TEST-1",
        headers=auth_headers,
        json={"updates": {"audit_report": "/etc/hosts"}},
    )
    assert resp.status_code == 422
```

再加一条：

```python
def test_patch_order_rejects_pdf_path_outside_allowed_report_dir(...):
    ...
```

在 `admin/tests/test_web_public.py` 增加：

```python
def test_portal_report_rejects_untrusted_report_path(...):
    # 即使订单里已有脏路径，也不返回本地文件内容
```

**Step 2: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_routes_orders.py admin/tests/test_web_public.py
```

Expected:

- FAIL，当前 `/etc/hosts` 仍可被接受或读出。

**Step 3: 最小实现**

实现原则：

- `admin/routes/orders.py` 中 `_normalize_updates()` 或后续更新流程对 `audit_report` / `pdf_path` / `plan_file` 做受控校验
- 只允许这些字段指向：
  - `settings.share_report_dir`
  - 或现有明确的报告输出目录
- 对路径做：
  - `resolve()`
  - 基目录包含校验
  - 合法后缀校验（如 `.html`, `.json`, `.pdf`, `.md`，按当前真实报告产物收紧）
- `admin/routes/web_public.py` 中 portal 报告读取前再做一次防御性校验，不能只依赖后台写入端

**Step 4: 重新运行测试**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_routes_orders.py admin/tests/test_web_public.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add admin/routes/orders.py admin/routes/web_public.py admin/tests/test_routes_orders.py admin/tests/test_web_public.py
git commit -m "fix: restrict portal report paths to trusted directories"
```

**Anti-pattern guards:**
- 不允许用“只隐藏按钮”代替服务端校验
- 不允许继续让 portal 直接信任任意订单路径字段

---

## Phase 2: P1 Security and Data-Governance Fixes

### Task 5: 为后台订单能力补真正的角色授权

**Files:**
- Modify: `admin/auth.py`
- Modify: `admin/routes/orders.py`
- Modify: `admin/routes/notifications.py`
- Modify: `admin/routes/users.py`（如果列表/详情也需同策略）
- Test: `admin/tests/test_auth.py`
- Test: `admin/tests/test_routes_orders.py`
- Test: `admin/tests/test_notification_audit_page.py`

**Step 1: 写失败测试**

在 `admin/tests/test_routes_orders.py` 增加：

```python
def test_viewer_cannot_list_orders(...):
    resp = client.get("/api/orders", headers=viewer_headers)
    assert resp.status_code == 403


def test_viewer_cannot_patch_order(...):
    resp = client.patch(...)
    assert resp.status_code == 403
```

在 `admin/tests/test_auth.py` 增加：

```python
def test_require_role_rejects_non_admin_user(...):
    ...
```

**Step 2: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_auth.py admin/tests/test_routes_orders.py admin/tests/test_notification_audit_page.py
```

Expected:

- FAIL，当前 viewer 账号仍能访问这些接口。

**Step 3: 最小实现**

在 `admin/auth.py` 增加统一依赖：

```python
def require_role(*allowed_roles: str):
    def _dep(user: AdminUser = Depends(get_current_user)) -> AdminUser:
        if user.role not in allowed_roles:
            raise BusinessError(...)
        return user
    return _dep
```

然后把高权限路由从：

```python
_: AdminUser = Depends(get_current_user)
```

改成：

```python
_: AdminUser = Depends(require_role("admin"))
```

至少覆盖：

- `/api/orders*`
- `/api/admin/orders*`
- 通知审计 / ops alert 审计
- 任何会暴露内部路径或跨用户数据的后台接口

**Step 4: 重新跑测试**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_auth.py admin/tests/test_routes_orders.py admin/tests/test_notification_audit_page.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add admin/auth.py admin/routes/orders.py admin/routes/notifications.py admin/routes/users.py admin/tests/test_auth.py admin/tests/test_routes_orders.py admin/tests/test_notification_audit_page.py
git commit -m "fix: enforce admin role on backend order and audit routes"
```

**Anti-pattern guards:**
- 不允许只在前端隐藏入口
- 不允许继续让 `role` 字段存在但不参与授权

---

### Task 6: 收紧 Portal token 传播边界，不再用 query token 贯穿支付链

**Files:**
- Modify: `data/customer_portal/token.py`
- Modify: `data/payments/service.py`
- Modify: `data/payments/dao.py`
- Modify: `data/payments/models.py`
- Modify: `data/payments/providers/mock_gateway.py`
- Modify: `data/payments/providers/alipay_sim.py`
- Modify: `data/payments/providers/alipay.py`
- Modify: `admin/routes/web_public.py`
- Test: `admin/tests/test_web_public.py`
- Test: `data/payments/tests/test_provider_alipay.py`
- Test: `data/payments/tests/test_service.py`

**Step 1: 先决定 contract**

最保守方案：

- Portal token 继续存在，但不再放进第三方回跳 URL 和公开 checkout query
- 支付回跳改成一次性 payment-bound token 或 server-side lookup key
- `payments.checkout_token` 改为：
  - 不持久化，或
  - 持久化哈希值而非明文

**Step 2: 写失败测试**

```python
def test_checkout_url_does_not_expose_portal_token_in_query(...):
    assert "token=" not in checkout.checkout_url


def test_alipay_return_url_does_not_embed_portal_token(...):
    assert "token=" not in checkout_url
```

如保留数据库字段但改哈希：

```python
def test_payment_does_not_persist_plain_portal_token(...):
    assert payment.checkout_token != raw_portal_token
```

**Step 3: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_web_public.py data/payments/tests/test_provider_alipay.py data/payments/tests/test_service.py
```

Expected:

- FAIL，当前 provider / service 仍在 URL 和表中传播明文 token。

**Step 4: 最小实现**

优先选 boring 方案：

- 支付回跳带 `payment_id` + provider state，不带 portal token
- 服务端根据 `payment_id -> order_id` 找回订单，再单独发起安全跳转
- 若必须有回跳能力标识，则使用短期一次性 nonce，校验后立即失效

**Step 5: 重新跑测试**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_web_public.py data/payments/tests/test_provider_alipay.py data/payments/tests/test_service.py
```

Expected:

- PASS

**Step 6: Commit**

```bash
git add data/customer_portal/token.py data/payments/service.py data/payments/dao.py data/payments/models.py data/payments/providers/mock_gateway.py data/payments/providers/alipay_sim.py data/payments/providers/alipay.py admin/routes/web_public.py admin/tests/test_web_public.py data/payments/tests/test_provider_alipay.py data/payments/tests/test_service.py
git commit -m "fix: stop exposing portal tokens across payment URLs and storage"
```

**Anti-pattern guards:**
- 不允许把旧 portal token 换个 query 参数名继续用
- 不允许“只是缩短 token”但继续明文传播

---

### Task 7: 补齐 retention / anonymize 的跨表治理

**Files:**
- Modify: `data/orders/deletion_service.py`
- Modify: `data/orders/retention_cleanup.py`
- Modify: `admin/routes/web_public.py`
- Modify: `admin/routes/notifications.py`
- Modify: `data/share/short_link.py`
- Modify: `docs/DATA_RETENTION_AND_DELETION.md`
- Modify: `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- Test: `admin/tests/test_order_deletion.py`
- Test: `tests/test_delivery_dispatcher.py`
- Test: `admin/tests/test_order_info_form.py`

**Step 1: 写失败测试**

补三类测试：

```python
def test_anonymize_order_scrubs_delivery_notifications_payload(...):
    ...


def test_retention_cleanup_scrubs_notification_payload_for_expired_orders(...):
    ...


def test_deletion_request_log_is_purged_or_rotated_by_retention_policy(...):
    ...
```

如果分享遥测要纳管，再补：

```python
def test_share_access_events_have_retention_cleanup(...):
    ...
```

**Step 2: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_order_deletion.py tests/test_delivery_dispatcher.py admin/tests/test_order_info_form.py
```

Expected:

- FAIL，当前通知 payload / 删除申请日志 / 分享遥测未被完整纳管。

**Step 3: 最小实现**

- `OrderDeletionService.anonymize_order()` 同步清理或脱敏：
  - `delivery_notifications.payload_json`
- 给 `deletion-requests.jsonl` 制定 retention：
  - 要么纳入清理脚本
  - 要么改成入库并统一治理
- 给分享访问遥测增加最小 retention 清理入口

**Step 4: 更新文档**

在 `docs/DATA_RETENTION_AND_DELETION.md` 和 runbook 中明确：

- 哪些旁路数据集在 retention 范围内
- 匿名化 vs 物理删除分别影响哪些表/文件

**Step 5: 重新跑测试**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_order_deletion.py tests/test_delivery_dispatcher.py admin/tests/test_order_info_form.py
```

Expected:

- PASS

**Step 6: Commit**

```bash
git add data/orders/deletion_service.py data/orders/retention_cleanup.py admin/routes/web_public.py admin/routes/notifications.py data/share/short_link.py docs/DATA_RETENTION_AND_DELETION.md docs/DELIVERY_RETENTION_OPS_RUNBOOK.md admin/tests/test_order_deletion.py tests/test_delivery_dispatcher.py admin/tests/test_order_info_form.py
git commit -m "fix: align retention cleanup across notifications logs and share telemetry"
```

**Anti-pattern guards:**
- 不允许只清订单主表
- 不允许继续让旁路 JSONL/遥测游离在治理范围外

---

### Task 8: 收紧后台审计暴露、同意记录和邮箱保护策略

**Files:**
- Modify: `admin/routes/notifications.py`
- Modify: `admin/routes/web_public.py`
- Modify: `data/orders/intake_store.py`
- Modify: `data/orders/models.py`
- Modify: `data/orders/schema.py`（如需迁移字段）
- Modify: `docs/LEGAL_PRIVACY_BASELINE.md`
- Test: `admin/tests/test_notification_audit_page.py`
- Test: `admin/tests/test_order_info_form.py`
- Test: `data/orders/tests/test_models.py`

**Step 1: 拆成两个最小目标**

A. 后台审计接口不再透传全量 `payload_json` / `details`  
B. 同意记录与邮箱保护策略收口

**Step 2: 先写失败测试**

```python
def test_notification_audit_api_masks_internal_paths_and_customer_email(...):
    ...


def test_portal_intake_persists_consent_audit_fields(...):
    assert payload["privacy_accepted_at"]
    assert payload["service_terms_accepted_at"]
    assert payload["consent_channel"] == "portal"


def test_customer_email_is_not_stored_as_plaintext(...):
    assert row["customer_email"] != "parent@example.com"
```

如果暂时不准备对邮箱做加密，至少先落计划中的显式例外说明，并改测试锁死“必须有策略注释 / 明确豁免”。但更推荐直接与手机号策略统一。

**Step 3: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_notification_audit_page.py admin/tests/test_order_info_form.py data/orders/tests/test_models.py
```

Expected:

- FAIL

**Step 4: 最小实现**

- `admin/routes/notifications.py` 返回 allowlist 字段，不直接回传完整 payload/details
- `web_public.py` 在 intake payload 中补：
  - `privacy_accepted_at`
  - `service_terms_accepted_at`
  - `consent_channel`
  - `consent_given_at`
  - 如有后台代录，再补 `consent_operator`
- `customer_email`：
  - 优先按手机号同类策略加密落盘
  - 如查询需要，增加 hash/索引辅助字段

**Step 5: 迁移与兼容**

如果 schema 变更，补一个最小安全迁移：

- 旧数据可读
- 新写入按新策略走
- 测试覆盖旧行缺字段场景

**Step 6: 重新跑测试**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_notification_audit_page.py admin/tests/test_order_info_form.py data/orders/tests/test_models.py
```

Expected:

- PASS

**Step 7: Commit**

```bash
git add admin/routes/notifications.py admin/routes/web_public.py data/orders/intake_store.py data/orders/models.py data/orders/schema.py docs/LEGAL_PRIVACY_BASELINE.md admin/tests/test_notification_audit_page.py admin/tests/test_order_info_form.py data/orders/tests/test_models.py
git commit -m "fix: tighten audit exposure and consent data handling"
```

**Anti-pattern guards:**
- 不允许只在前端隐藏敏感字段
- 不允许继续把“同意过”只记录成布尔值

---

### Task 9: 收口运行时契约、依赖锁定与 `dev-verify` 漂移检查

**Files:**
- Modify: `scripts/dev-verify.sh`
- Modify: `.github/workflows/ci.yml`
- Modify: `docker-compose.yml`
- Modify: `Dockerfile`
- Create: `requirements.lock.txt` or `constraints.txt`（按项目决定一种）
- Modify: `README.md`
- Modify: `INSTALL.md`
- Test: `tests/test_dev_verify_entrypoint.py`
- Test: `tests/test_docker_compose_env_contract.py`
- Create or Modify: `tests/test_runtime_contracts.py`

**Step 1: 先定方案**

只选一种，不要同时搞多套：

- **锁定机制**：`constraints.txt` 或 `requirements.lock.txt`
- **compose 契约**：
  - 要么真正支持 `GAOKAO_ADMIN_BIND/PORT`
  - 要么删掉这些 env，避免假接线
- **dev-verify 漂移检查**：
  - 比较 `.venv/bin/python --version` 与 `PYTHON_BIN --version`
  - 不一致则报错或要求显式重建

**Step 2: 写失败测试**

```python
def test_dev_verify_detects_python_bin_drift(...):
    ...


def test_compose_does_not_expose_unused_admin_bind_port_env(...):
    ...


def test_ci_cache_key_tracks_all_runtime_requirement_inputs(...):
    ...
```

**Step 3: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_dev_verify_entrypoint.py tests/test_docker_compose_env_contract.py tests/test_runtime_contracts.py
```

Expected:

- FAIL

**Step 4: 最小实现**

- `scripts/dev-verify.sh`
  - 加解释器漂移检测
  - 明确 `recreate_venv` 入口或错误提示
- `.github/workflows/ci.yml`
  - cache key 同时 hash `requirements-admin.txt` + `requirements-dev.txt` + lock/constraints
- `docker-compose.yml` / `Dockerfile`
  - 修正假接线：要么真接，要么删掉
- `README.md` / `INSTALL.md`
  - 所有 `python3 ...` 改成先建/激活 `.venv` 的前置说明

**Step 5: 重新跑测试**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_dev_verify_entrypoint.py tests/test_docker_compose_env_contract.py tests/test_runtime_contracts.py
```

Expected:

- PASS

**Step 6: Commit**

```bash
git add scripts/dev-verify.sh .github/workflows/ci.yml docker-compose.yml Dockerfile requirements.lock.txt constraints.txt README.md INSTALL.md tests/test_dev_verify_entrypoint.py tests/test_docker_compose_env_contract.py tests/test_runtime_contracts.py
git commit -m "build: tighten runtime contracts and dependency reproducibility"
```

**Anti-pattern guards:**
- 不允许新增第二套安装说明而保留旧模糊说法
- 不允许继续让 compose env “看着可配实际上没用”

---

### Task 10: 决定 `audit run` 与 `payment_failed` 的真实 contract

**Files:**
- Modify: `data/rules/audit_engine.py`
- Modify: `data/rules/cli.py`
- Modify: `data/payments/service.py`
- Modify: `admin/routes/web_public.py`
- Modify: `docs/TECH_ARCHITECTURE.md`
- Modify: `docs/CURRENT_STATE.md`
- Test: `tests/test_audit_engine_major_validation_phase2.py`
- Create or Modify: `tests/test_audit_engine_contract.py`
- Create or Modify: `data/payments/tests/test_service.py`

**Step 1: 选一个真实方向**

- `audit run`：
  - 方案 A：收窄文档与 CLI 文案，只承认当前检查面
  - 方案 B：补至少 1-2 个最关键缺失检查
- `payment_failed`：
  - 方案 A：真实落库 + portal 呈现
  - 方案 B：删掉 UI 分支，避免假状态机

优先推荐：**文案先收窄，状态机先收实或删死分支**。

**Step 2: 写失败测试**

```python
def test_audit_run_output_declares_actual_checks_only(...):
    ...


def test_failed_payment_state_is_either_persisted_or_not_rendered(...):
    ...
```

**Step 3: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_audit_engine_major_validation_phase2.py tests/test_audit_engine_contract.py data/payments/tests/test_service.py
```

Expected:

- FAIL

**Step 4: 最小实现**

- `audit run` 的输出与文档只描述真实执行内容
- `payment_failed` 要么真实落状态，要么删掉 portal 分支和文案

**Step 5: 重新跑测试**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_audit_engine_major_validation_phase2.py tests/test_audit_engine_contract.py data/payments/tests/test_service.py
```

Expected:

- PASS

**Step 6: Commit**

```bash
git add data/rules/audit_engine.py data/rules/cli.py data/payments/service.py admin/routes/web_public.py docs/TECH_ARCHITECTURE.md docs/CURRENT_STATE.md tests/test_audit_engine_major_validation_phase2.py tests/test_audit_engine_contract.py data/payments/tests/test_service.py
git commit -m "fix: align audit and payment failure contracts with real behavior"
```

**Anti-pattern guards:**
- 不允许继续让 CLI / UI 说一套、代码做一套

---

## Phase 3: P2 Cleanup, Deployment Proof, and Final Verification

### Task 11: 收口 P2 前端/分享/健康检查边界

**Files:**
- Modify: `admin/routes/web_public.py`
- Modify: `admin/routes/health.py`
- Modify: `data/share/permission.py`
- Test: `admin/tests/test_web_public.py`
- Test: `data/share/tests/test_permission.py`
- Create or Modify: `admin/tests/test_health.py`

**Step 1: 写失败测试**

```python
def test_confirm_summary_does_not_use_innerhtml_for_user_fields(...):
    ...


def test_health_endpoint_returns_minimal_readiness_only(...):
    ...


def test_share_edit_scope_excludes_id_card_and_internal_paths(...):
    ...
```

**Step 2: 跑测试确认失败**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_web_public.py data/share/tests/test_permission.py admin/tests/test_health.py
```

Expected:

- FAIL

**Step 3: 最小实现**

- 去掉确认页 `innerHTML` 拼接用户输入
- `/health` 只返回最小 readiness
- 收紧 `data/share/permission.py` 中 `edit/admin` allowlist，排除身份证号、联系方式、内部路径

**Step 4: 重新跑测试**

Run:

```bash
./.venv/bin/python -m pytest -q admin/tests/test_web_public.py data/share/tests/test_permission.py admin/tests/test_health.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add admin/routes/web_public.py admin/routes/health.py data/share/permission.py admin/tests/test_web_public.py data/share/tests/test_permission.py admin/tests/test_health.py
git commit -m "fix: reduce portal and share exposure surfaces"
```

---

### Task 12: 为容器内 PDF 生成和统一门禁补最终证明

**Files:**
- Modify: `Dockerfile`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `INSTALL.md`
- Create or Modify: `tests/test_pdf_runtime_smoke.py`

**Step 1: 补容器或 CI 级 smoke**

至少选一种：

- Docker build 后在容器内运行最小 WeasyPrint PDF smoke
- 或 CI job 直接执行最小 PDF 生成 smoke，并断言输出文件存在

测试形状：

```python
def test_weasyprint_pdf_smoke(tmp_path):
    from weasyprint import HTML
    out = tmp_path / "smoke.pdf"
    HTML(string="<h1>smoke</h1>").write_pdf(out)
    assert out.exists()
    assert out.stat().st_size > 0
```

**Step 2: 跑测试确认当前门禁不足**

Run:

```bash
./.venv/bin/python -m pytest -q tests/test_pdf_runtime_smoke.py
```

Expected:

- 本地可能 PASS，但 CI / Dockerfile 尚未把这条变成交付证明

**Step 3: 最小实现**

- 如 Dockerfile 缺系统库，则补安装
- 在 CI 中增加 PDF smoke
- 在 README / INSTALL 中明确“哪些环境已验证可生成 PDF”

**Step 4: 运行最终门禁**

Run:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_backup_workflow.py \
  tests/test_backup_restore_service_level.py \
  tests/test_dev_verify_entrypoint.py \
  tests/test_design_docs_substantive.py \
  tests/test_audit_engine_major_validation_phase2.py \
  tests/test_audit_engine_contract.py \
  admin/tests/test_auth.py \
  admin/tests/test_routes_orders.py \
  admin/tests/test_notification_audit_page.py \
  admin/tests/test_web_public.py \
  admin/tests/test_order_deletion.py \
  admin/tests/test_order_info_form.py \
  data/orders/tests/test_models.py \
  data/payments/tests/test_service.py \
  data/payments/tests/test_provider_alipay.py \
  data/share/tests/test_permission.py \
  tests/test_runtime_contracts.py \
  tests/test_pdf_runtime_smoke.py -q
```

然后跑：

```bash
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
./.venv/bin/python -m data.rules.cli doctor --json
```

Expected:

- 全部 PASS
- doctor 返回 `ok: true`

**Step 5: Commit**

```bash
git add Dockerfile .github/workflows/ci.yml README.md INSTALL.md tests/test_pdf_runtime_smoke.py
git commit -m "build: prove pdf runtime and strict remediation gates"
```

**Anti-pattern guards:**
- 不允许用“本机能跑”替代 Docker/CI 交付证明

---

## Final Verification Checklist

1. `backup_verify.sh` live 路径不再裸复制 SQLite。  
2. coverage gate 不再把测试代码算进 overall。  
3. `PRD` / `ROADMAP` / `TECH_ARCHITECTURE` 不再把目标态写成现状。  
4. `audit_report/pdf_path/plan_file` 不可指向任意本地路径。  
5. 非 admin 后台账号无法访问订单后台写能力。  
6. Portal token 不再通过 query 参数贯穿支付链。  
7. retention 覆盖通知 payload、删除申请日志、分享遥测。  
8. 后台审计接口做字段级最小暴露。  
9. consent 记录含时间/渠道/操作者语义。  
10. `customer_email` 策略与 PII 保护策略一致。  
11. `dev-verify` 能发现 `.venv` 解释器漂移。  
12. compose 契约不存在假接线。  
13. `/health` 只返回最小 readiness。  
14. 分享 allowlist 不再包含高敏字段和内部路径。  
15. Docker/CI 对 PDF 生成能力有真实证明。  

## Grep / Anti-pattern Sweep

Run:

```bash
python3 - <<'PY'
from pathlib import Path
bad = [
    "?token=",
    "innerHTML =",
    "--cov=.",
    "Depends(get_current_user)",
]
for needle in bad:
    print(f"== {needle} ==")
    for path in Path('.').rglob('*.py'):
        try:
            text = path.read_text(encoding='utf-8')
        except Exception:
            continue
        if needle in text:
            print(path)
PY
```

人工确认：

- `?token=` 不再出现在支付 URL 构造链
- 高权限后台路由不再只挂 `Depends(get_current_user)`
- `innerHTML =` 不再用于拼接用户输入
- `--cov=.` 不再作为统一 coverage 入口

---

Plan complete and saved to `docs/plans/2026-06-18-strict-review-remediation-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - 我在当前会话按任务逐个执行、每步复核后再推进。  
**2. Parallel Session (separate)** - 开一个新会话，按这个计划批量执行并在阶段点回报。  

**Which approach?**
