# Comprehensive Review Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 收口 2026-06-17 全面系统评审中的 P0/P1 问题，先修复支付一致性、生产 fail-closed、规则审计、灾备链路和文档真相源漂移。

**Architecture:** 先修复“会直接产生错误业务状态或假阳性验收”的底层不变量，再补测试和文档。所有变更都沿用现有 Python/FastAPI/SQLite 架构，不引入新基础设施；优先增强当前 DAO、service、script 和 docs 的真实一致性。

**Tech Stack:** Python 3.11, FastAPI, sqlite3, pytest, bash scripts, Markdown docs

---

### Task 1: 统一项目定位与文档真相源

**Files:**
- Modify: `docs/CURRENT_STATE.md`
- Modify: `README.md`
- Modify: `product/PRD.md`
- Modify: `product/ROADMAP.md`
- Modify: `product/MARKET_RESEARCH.md`
- Modify: `docs/TECH_ARCHITECTURE.md`
- Modify: `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- Test: `tests/test_design_docs_substantive.py`

**Step 1: 写文档一致性回归测试**

在 `tests/test_design_docs_substantive.py` 追加一个轻量一致性测试，锁死以下事实：

```python
def test_product_docs_do_not_claim_complete_web_saas():
    current = (DOCS_DIR / "CURRENT_STATE.md").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    prd = (REPO_ROOT / "product" / "PRD.md").read_text(encoding="utf-8")
    roadmap = (REPO_ROOT / "product" / "ROADMAP.md").read_text(encoding="utf-8")

    assert "不是完整 Web 自助 SaaS" in current
    assert "不是完整用户端 Web 自助产品" in readme
    assert "完整 Web 自助 SaaS" not in prd
    assert "完整 Web 自助 SaaS" not in roadmap
```

**Step 2: 运行测试，确认当前会失败**

Run:

```bash
./.venv/bin/pytest -q tests/test_design_docs_substantive.py::test_product_docs_do_not_claim_complete_web_saas
```

Expected:

- FAIL，原因是 `PRD.md` / `ROADMAP.md` 当前仍在混用“运营增强系统”和“完整自助产品”口径。

**Step 3: 最小改动收口文档**

按下列原则更新文档：

- `README.md` 保持与 `docs/CURRENT_STATE.md` 一致，把当前定位锁成“人工服务运营增强系统 + AI 审核增强链路”。
- `product/PRD.md` 的“Web系统流程”从“当前核心业务流程”降级为“目标态/后续闭环”。
- `product/ROADMAP.md` 统一商业化与 Web 自助里程碑，删掉互相打架的启动时间。
- `product/MARKET_RESEARCH.md` 去掉“纯 AI / 免费低价全流程”这类与当前真相矛盾的表述。
- `docs/TECH_ARCHITECTURE.md` 用 `Current / Target` 双栏表达现状和目标，避免继续把目标态写成现状。
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` 修正 dispatcher 处理状态说明，和代码保持一致。

建议先写一句统一定位：

```md
当前项目定位：人工服务运营增强系统；用户端 Web 自助闭环仅为本地 MVP/目标态，尚未达到可对外承诺的完整 SaaS 水位。
```

**Step 4: 重新运行文档测试**

Run:

```bash
./.venv/bin/pytest -q tests/test_design_docs_substantive.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add tests/test_design_docs_substantive.py docs/CURRENT_STATE.md README.md product/PRD.md product/ROADMAP.md product/MARKET_RESEARCH.md docs/TECH_ARCHITECTURE.md docs/DELIVERY_RETENTION_OPS_RUNBOOK.md
git commit -m "docs: align product positioning with current system truth"
```

---

### Task 2: 生产支付 provider fail-closed

**Files:**
- Modify: `admin/config.py:153-238`
- Modify: `admin/app.py:63-92`
- Modify: `admin/routes/web_public.py:238-279`
- Modify: `.env.docker.example`
- Test: `admin/tests/test_p2_4_p2_5_secrets.py`
- Test: `admin/tests/test_web_public.py`

**Step 1: 先补失败测试**

在 `admin/tests/test_p2_4_p2_5_secrets.py` 增加生产环境 provider 校验：

```python
def test_payment_provider_mock_is_rejected_in_prod(monkeypatch):
    monkeypatch.setenv("GAOKAO_ENV", "prod")
    monkeypatch.setenv("GAOKAO_JWT_SECRET", "x" * 64)
    monkeypatch.setenv("GAOKAO_PORTAL_TOKEN_SECRET", "Z" * 64)
    monkeypatch.setenv("GAOKAO_PAYMENT_WEBHOOK_SECRET", "P" * 32)
    monkeypatch.setenv("GAOKAO_PAYMENT_PROVIDER", "mock")

    with pytest.raises(RuntimeError, match="GAOKAO_PAYMENT_PROVIDER"):
        _reload_settings()
```

在 `admin/tests/test_web_public.py` 增加模拟支付页在 prod 不可用：

```python
def test_mock_payment_routes_are_unavailable_in_prod(client):
    resp = client.get("/pay/mock/some-payment?token=fake")
    assert resp.status_code in {403, 404}
```

**Step 2: 跑定向测试确认失败**

Run:

```bash
./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py
```

Expected:

- FAIL，当前 `prod + mock` 仍可加载，模拟支付页仍可能暴露。

**Step 3: 最小实现**

在 `admin/config.py` 增加生产 provider 校验函数：

```python
def _enforce_payment_provider_policy(settings: Settings) -> None:
    if settings.env != "prod":
        return
    if settings.payment_provider in {"mock", "alipay_sim", ""}:
        raise RuntimeError(
            "GAOKAO_PAYMENT_PROVIDER invalid in prod: mock/alipay_sim are forbidden"
        )
```

在 `load_settings()` 末尾调用该函数。  
在 `admin/routes/web_public.py` 中让 `/pay/mock/*` 与 `/pay/alipay-sim/*` 在 `prod` 直接拒绝。  
把 `.env.docker.example` 的默认 provider 改成空值或明确注释要求显式填真实 provider。

**Step 4: 重新运行测试**

Run:

```bash
./.venv/bin/pytest -q admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add admin/config.py admin/routes/web_public.py .env.docker.example admin/tests/test_p2_4_p2_5_secrets.py admin/tests/test_web_public.py
git commit -m "fix: fail closed for mock payment providers in prod"
```

---

### Task 3: 修复退款后成功回调重入导致的支付状态回写

**Files:**
- Modify: `data/payments/service.py:196-283`
- Test: `data/payments/tests/test_service.py`
- Test: `data/payments/tests/test_webhook.py`

**Step 1: 先写回归测试**

在 `data/payments/tests/test_service.py` 新增：

```python
def test_handle_webhook_keeps_refunded_payment_terminal(settings):
    order = _seed_order(settings.orders_db_path, order_id="GKO-REFUND-REPLAY")
    service = PaymentService.for_db(
        settings.orders_db_path,
        base_url=settings.payment_base_url,
        webhook_secret=settings.payment_webhook_secret,
    )
    checkout = service.create_checkout(order.id, portal_token="portal-token")
    payload, headers = service.provider.build_webhook_request(
        payment_id=checkout.payment_id,
        amount_cents=order.amount_cents,
        provider_trade_no="MOCK-REPLAY-001",
    )
    service.handle_webhook(payload, headers["X-Mock-Signature"])
    service.request_refund(order.id, reason="manual_refund")

    replay = service.handle_webhook(payload, headers["X-Mock-Signature"])
    payment = service.get_payment_by_order(order.id)
    with OrdersDAO.connect(settings.orders_db_path) as dao:
        reloaded = dao.get(order.id)

    assert replay.idempotent is True
    assert payment is not None and payment.status == "refunded"
    assert reloaded.status == "refunded"
```

**Step 2: 跑测试确认失败**

Run:

```bash
./.venv/bin/pytest -q data/payments/tests/test_service.py::test_handle_webhook_keeps_refunded_payment_terminal
```

Expected:

- FAIL，当前实现会把 `payment.status` 回写成 `paid`。

**Step 3: 最小实现**

在 `data/payments/service.py` 的 `handle_webhook()` 中加终态幂等分支：

```python
if payment.status == "refunded":
    order = orders_dao.get(payment.order_id)
    return WebhookHandleResult(
        payment_id=payment.id,
        processed=True,
        idempotent=True,
        order_status=order.status,
    )
```

要求：

- `refunded` 视为终态，不允许被成功回调覆盖。
- 不新增状态，不改现有状态机定义。

**Step 4: 跑支付定向测试**

Run:

```bash
./.venv/bin/pytest -q data/payments/tests/test_service.py data/payments/tests/test_webhook.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add data/payments/service.py data/payments/tests/test_service.py data/payments/tests/test_webhook.py
git commit -m "fix: keep refunded payments terminal on webhook replay"
```

---

### Task 4: 建立“每订单单一活跃支付单”保护

**Files:**
- Modify: `data/payments/dao.py`
- Modify: `data/payments/service.py:137-180`
- Modify: `admin/routes/web_public.py:578-624`
- Test: `data/payments/tests/test_service.py`
- Test: `admin/tests/test_web_public.py`

**Step 1: 先补测试**

新增两个测试：

```python
def test_create_checkout_returns_same_payment_for_paid_order(settings):
    ...
    assert first.payment_id == second.payment_id
```

```python
def test_portal_context_does_not_fall_back_to_pending_after_paid_order(client):
    ...
    assert "待支付" not in page.text
```

再加一个并发/重复创建的最小保护测试，至少锁住“已存在 active payment 时不能再插第二条 pending”。

**Step 2: 跑测试确认当前保护不足**

Run:

```bash
./.venv/bin/pytest -q data/payments/tests/test_service.py admin/tests/test_web_public.py
```

Expected:

- FAIL，或需要先手工补上最小复现再失败。

**Step 3: 最小实现**

优先选最小方案，不做大表重构：

1. 在 `payments` 表上增加“每订单单活跃单”约束，至少满足当前模型。
2. `create_checkout()` 包在单事务里。
3. 对 `pending/paid/refunded` 之外的状态语义做显式处理，避免重复插入。

可选最小实现方向：

```python
existing = payments.get_by_order(order_id)
if existing is not None:
    return PaymentCheckout(...)
```

加上数据库层唯一约束：

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_order_unique ON payments(order_id);
```

如果保留“一单多支付历史”需求，则改成“活跃状态唯一”前先不要做大设计；当前按 YAGNI 优先先止血。

**Step 4: 运行测试**

Run:

```bash
./.venv/bin/pytest -q data/payments/tests/test_service.py admin/tests/test_web_public.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add data/payments/dao.py data/payments/service.py admin/routes/web_public.py data/payments/tests/test_service.py admin/tests/test_web_public.py
git commit -m "fix: enforce single active payment per order"
```

---

### Task 5: 让 `gaokao-cli audit run` 真正执行省规则

**Files:**
- Modify: `data/rules/audit_engine.py:22-80`
- Modify: `data/rules/cli.py:196-203`
- Test: `tests/test_audit_cli_major_validation_phase2.py`
- Test: `tests/test_audit_engine_major_validation_phase2.py`

**Step 1: 先写失败测试**

在 CLI 测试里增加“超志愿数应失败”：

```python
def test_audit_run_cli_fails_when_volunteer_count_exceeds_province_limit(tmp_path):
    truth_root, catalog_root, _ = _write_truth_and_catalog(tmp_path)
    plan_path = tmp_path / "too-many.json"
    plan_path.write_text(
        json.dumps(
            {"province": "湖南", "items": [{"school_name": f"学校{i}", "major_names": []} for i in range(46)]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    result = subprocess.run([...], ...)
    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["overall_pass"] is False
    assert any(issue["rule_id"] == "RULES.max_volunteers" for issue in payload["issues"])
```

再在引擎单测里补一条 `AuditEngine.audit_plan()` 级别测试。

**Step 2: 跑测试确认当前失败**

Run:

```bash
./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py
```

Expected:

- FAIL，当前只校验 majors。

**Step 3: 最小实现**

在 `data/rules/audit_engine.py` 中新增最小省规则校验函数：

```python
def _validate_province_rules(self, snapshot: ProvinceRuleSnapshot, plan: dict[str, Any]) -> list[dict[str, object]]:
    issues = []
    if snapshot.max_volunteers is not None and len(plan.get("items", [])) > int(snapshot.max_volunteers):
        issues.append({
            "rule_id": "RULES.max_volunteers",
            "severity": "critical",
            "title": f"志愿数量超过上限 {snapshot.max_volunteers}",
            "message": f"当前方案包含 {len(plan.get('items', []))} 个志愿单位",
            "suggestion": "请删除超出上限的志愿单位后重新审计",
        })
    return issues
```

并在 `audit_plan()` 中：

```python
snapshot = self.get_province_snapshot(province)
issues.extend(self._validate_province_rules(snapshot, plan))
issues.extend(self._validate_majors(plan))
```

当前只做 `max_volunteers`，不要顺手扩到所有规则，保持 YAGNI。

**Step 4: 跑测试**

Run:

```bash
./.venv/bin/pytest -q tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add data/rules/audit_engine.py data/rules/cli.py tests/test_audit_cli_major_validation_phase2.py tests/test_audit_engine_major_validation_phase2.py
git commit -m "fix: enforce province volunteer limits in audit cli"
```

---

### Task 6: 修复备份快照对 WAL 管理库和真实业务文件的覆盖

**Files:**
- Modify: `scripts/backup_snapshot.sh`
- Modify: `docs/BACKUP_AND_RECOVERY_PLAN.md`
- Modify: `ops/systemd/gaokao-backup.service`
- Modify: `ops/cron/gaokao-backup.crontab.example`
- Test: `tests/test_backup_workflow.py`
- Test: `tests/test_backup_restore_service_level.py`

**Step 1: 先补失败测试**

在 `tests/test_backup_workflow.py` 增加：

```python
def test_backup_snapshot_preserves_admin_db_schema_under_wal(settings, tmp_path):
    ...
    conn = sqlite3.connect(snapshot_dir / "db" / "admin.db")
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert "admin_users" in tables
```

再补 portal 上传目录覆盖：

```python
def test_backup_snapshot_copies_portal_upload_dir(settings, tmp_path):
    ...
    assert (snapshot_dir / "files" / "portal_uploads" / "ORDER-1" / "score.pdf").is_file()
```

**Step 2: 跑测试确认失败**

Run:

```bash
./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
```

Expected:

- FAIL，当前 `admin.db` 空壳，portal 上传目录未备份。

**Step 3: 最小实现**

在 `backup_snapshot.sh` 中做两件事：

1. 对 `admin.db` 做 SQLite 在线备份或 `wal_checkpoint` 后复制，不再裸 `cp`。
2. 新增 `GAOKAO_PORTAL_UPLOAD_DIR` 支持并复制到快照。

推荐最小实现：

```bash
sqlite3 "$ADMIN_DB" "PRAGMA wal_checkpoint(FULL);"
cp "$ADMIN_DB" "$SNAPSHOT_DIR/db/$(basename "$ADMIN_DB")"
```

或更稳妥地用 Python `sqlite3.Connection.backup()`。

新增变量：

```bash
PORTAL_UPLOAD_DIR="${GAOKAO_PORTAL_UPLOAD_DIR:-${ROOT_DIR}/data/portal_uploads}"
copy_dir_to "$PORTAL_UPLOAD_DIR" "$SNAPSHOT_DIR/files/portal_uploads"
```

同步更新：

- `manifest.json` 的 source_paths
- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- systemd / cron 示例环境变量

**Step 4: 跑测试**

Run:

```bash
./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add scripts/backup_snapshot.sh docs/BACKUP_AND_RECOVERY_PLAN.md ops/systemd/gaokao-backup.service ops/cron/gaokao-backup.crontab.example tests/test_backup_workflow.py tests/test_backup_restore_service_level.py
git commit -m "fix: make backup snapshots wal-safe and include portal uploads"
```

---

### Task 7: 提升 restore smoke 真实性，并清理过期的 `dev-verify` 忽略项

**Files:**
- Modify: `scripts/backup_restore_smoke.py`
- Modify: `scripts/dev-verify.sh`
- Modify: `tests/test_backup_workflow.py`
- Modify: `tests/test_dev_verify_entrypoint.py`

**Step 1: 先写测试**

补两类测试：

```python
def test_backup_restore_smoke_requires_realistic_env_contract(...):
    ...
```

```python
def test_dev_verify_skip_install_does_not_attempt_pip_network(...):
    ...
```

再加一条对 `PRE_EXISTING_IGNORES` 的约束测试，只保留当前确认仍然不稳定的用例。

**Step 2: 跑测试确认当前失败**

Run:

```bash
./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_dev_verify_entrypoint.py
```

Expected:

- FAIL，当前 restore smoke 会强制注入默认密钥和 `mock` provider。
- FAIL，当前 `--skip-install` 仍会升级 pip。

**Step 3: 最小实现**

在 `scripts/backup_restore_smoke.py` 中：

- 不再强制覆盖 `GAOKAO_PAYMENT_PROVIDER=mock`
- 若快照缺失关键恢复配置，则输出明确失败原因
- 将“默认秘密”只作为 `dev`/测试显式模式使用，不要在通用恢复链里自动兜底

在 `scripts/dev-verify.sh` 中：

- 把 `python -m pip install --upgrade pip` 挪进 `SKIP_INSTALL != 1` 分支
- 收紧 `PRE_EXISTING_IGNORES`，移除已恢复稳定的用例

最小调整示例：

```bash
if [[ "${SKIP_INSTALL}" != "1" ]]; then
  python -m pip install --upgrade pip >/dev/null
fi
```

**Step 4: 跑测试**

Run:

```bash
./.venv/bin/pytest -q tests/test_backup_workflow.py tests/test_dev_verify_entrypoint.py
```

Expected:

- PASS

**Step 5: Commit**

```bash
git add scripts/backup_restore_smoke.py scripts/dev-verify.sh tests/test_backup_workflow.py tests/test_dev_verify_entrypoint.py
git commit -m "fix: harden restore smoke and dev verify entrypoint"
```

---

### Task 8: 全量回归与发布前核对

**Files:**
- Modify: `reports/COMPREHENSIVE_SYSTEM_REVIEW_2026-06-17.md`
- Modify: `docs/CURRENT_STATE.md`
- Test: `admin/tests`
- Test: `data/payments/tests`
- Test: `tests`

**Step 1: 跑本次变更涉及的定向测试**

Run:

```bash
./.venv/bin/pytest -q \
  admin/tests/test_p2_4_p2_5_secrets.py \
  admin/tests/test_web_public.py \
  data/payments/tests/test_service.py \
  data/payments/tests/test_webhook.py \
  tests/test_audit_cli_major_validation_phase2.py \
  tests/test_audit_engine_major_validation_phase2.py \
  tests/test_backup_workflow.py \
  tests/test_backup_restore_service_level.py \
  tests/test_dev_verify_entrypoint.py \
  tests/test_design_docs_substantive.py
```

Expected:

- PASS

**Step 2: 跑一轮离线验证口径**

Run:

```bash
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh --skip-pre-existing
```

Expected:

- 不再出现 `pypi.org` DNS 重试
- pytest / coverage / ruff / mypy 按当前环境实际通过

**Step 3: 更新评审报告状态**

在 `reports/COMPREHENSIVE_SYSTEM_REVIEW_2026-06-17.md` 顶部或结尾补一节：

```md
## 修复状态更新
- P0-2 已修复
- P0-3 已修复
- P0-4 已修复
- P0-5 已修复
...
```

同时在 `docs/CURRENT_STATE.md` 中把已收口项从“有效问题”移入“已修复历史问题”。

**Step 4: 最终提交**

```bash
git add reports/COMPREHENSIVE_SYSTEM_REVIEW_2026-06-17.md docs/CURRENT_STATE.md
git commit -m "docs: update review and current state after remediation"
```

**Step 5: 发布前人工复核**

人工检查：

- `README`、`CURRENT_STATE`、`PRD` 是否仍然一致
- `prod` 环境是否还能加载 `mock/alipay_sim`
- 快照里的 `db/admin.db` 是否真有表
- `audit run` 对超志愿数是否返回失败

---

Plan complete and saved to `docs/plans/2026-06-17-comprehensive-review-remediation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
