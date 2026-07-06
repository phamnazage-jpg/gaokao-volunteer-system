# ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION

> 生成时间：2026-07-05T21:33:52+08:00  
> 执行原则：先定义完整修复标准，再按依赖顺序实施。每个任务必须 TDD、验证、提交、三远端同步。
> 状态：Phase 0~4 全部完成；Phase 5 T5-01 已通过，T5-02/T5-03 进行中。
> 更新时间：2026-07-06T08:30:07+08:00  
> 配套方案：`docs/plans/2026-07-05-review-remediation-systemic-fix-plan.md`  
> 配套整改清单：`docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`

---

## 阶段依赖图

```text
Phase 0 Truth Source
  -> Phase 1 Admin Auth/Nav
  -> Phase 2 Payment/Portal/Public Security
  -> Phase 3 Upload/Webhook/Delete/Schema
  -> Phase 4 Gates/Docker/CI
  -> Phase 5 Final Regression/Evidence
```

---

## Phase 0：真相源收敛

### T0-01 更新 CURRENT_STATE 和 README 入口

- 文件：`README.md`, `docs/CURRENT_STATE.md`
- 动作：把当前真相源改为 2026-07-05 Review Remediation 三件套。
- 验证：`grep -n "2026-07-05_REVIEW" README.md docs/CURRENT_STATE.md`
- 完成标准：不再引用旧 HEAD `dbb8fb7` 或旧“当前工作区未提交修改”。

### T0-02 标记旧 review / closeout 为历史快照

- 文件：旧 `reports/*REVIEW*`, `SPRINT_4_CLOSEOUT_2026-07-03_SUPERSEDED.md` 等。
- 动作：顶部加历史快照提示，指向今日报告和 active board。
- 验证：`grep -n "历史快照" <files>`。

### T0-03 补本地前端环境 runbook

- 文件：`README.md` 或 `docs/FRONTEND_GATE_RUNBOOK_2026-07-05.md`
- 动作：明确 `pnpm install --frozen-lockfile`、Node 20/22、turbo 检查。
- 验证：新文档包含 typecheck/lint/test/build 命令。

---

## Phase 1：Admin Auth / Navigation

### T1-01 后端移除或收紧 JWT query fallback

- 文件：`admin/auth.py`, `admin/tests/test_auth.py`
- 测试先行：新增 `test_query_token_is_rejected_for_admin_api`。
- 实现：`get_current_user()` 默认只读 Bearer；如需要 Web 一次性 code，另建独立机制。
- 验证：`.venv/bin/python -m pytest admin/tests/test_auth.py -q`

### T1-02 前端真实登录接入

- 文件：`apps/web/src/pages/admin/LoginPage.tsx`, `apps/web/src/stores/user.ts`, `apps/web/src/lib/api-client.ts`, `apps/web/src/hooks/*admin*`
- 测试先行：LoginPage mock server 返回 JWT；错误登录显示错误。
- 实现：调用 `/api/auth/login`，保存 token + expiry，logout 清理。
- 验证：`pnpm --filter @gaokao/web test LoginPage`

### T1-03 apiClient Bearer 注入

- 文件：`apps/web/src/lib/api-client.ts`, `apps/web/src/lib/api-client.test.ts`
- 测试先行：有 token 时请求 headers 包含 Authorization；无 token 时不包含。
- 实现：注入 token provider，避免每个 hook 手写 headers。
- 验证：`pnpm --filter @gaokao/web test api-client`

### T1-04 RequireAuth 真实校验

- 文件：`apps/web/src/components/admin/RequireAuth.tsx`, `apps/web/src/components/admin/RequireAuth.test.tsx`
- 测试先行：token 过期/无 token/role 非 admin 分别跳转或 403。
- 实现：rehydrate 后调用 `/api/auth/me` 或校验 expiry。
- 验证：`pnpm --filter @gaokao/web test RequireAuth`

### T1-05 修 `/admin/review` 断链与全 nav e2e

- 文件：`apps/web/src/router.tsx`, `apps/web/src/layouts/AdminLayout.tsx`, `apps/web/e2e/admin-portal.spec.ts`
- 选择：新增 admin review page 或移除导航项。推荐新增 route，复用 ReviewPage 或后台专用 Review queue。
- 验证：`pnpm --filter @gaokao/web test:e2e --project=chromium --grep admin`

---

## Phase 2：Payment / Portal / Public API Security

### T2-01 payment-return return_nonce

- 文件：`data/payments/dao.py`, `data/payments/service.py`, `admin/routes/web_public.py`, `data/payments/tests/*`, `admin/tests/test_payment_alipay_notify.py`
- 测试先行：已支付 payment_id 无 nonce 不能换 token；正确 nonce 一次可用；重复使用失败。
- 实现：checkout 创建 return_nonce；payment_return 校验并消费 nonce。
- 验证：相关 payment/web_public tests。

### T2-02 公共错误脱敏

- 文件：`admin/routes/web_public.py`, `admin/errors/exceptions.py`, `admin/tests/test_errors.py`, `admin/tests/test_web_public.py`
- 测试先行：prod 下 provider unavailable 不返回 env/path/provider detail。
- 实现：公共 route 抛业务错误码；内部错误仅 logger。
- 验证：`GAOKAO_ENV=prod .venv/bin/python -m pytest admin/tests/test_errors.py admin/tests/test_web_public.py -q`

### T2-03 公共下单限流 + 幂等

- 文件：`admin/routes/web_public.py`, `data/orders/*`, `admin/tests/test_web_public.py`
- 测试先行：同 IP/phone 高频返回 429；重复 idempotency key 返回同订单。
- 实现：轻量 SQLite/in-memory limiter + idempotency key。
- 验证：新增限流与幂等测试。

### T2-04 Portal token jti/version/revocation

- 文件：`data/customer_portal/token.py`, `data/orders/schema.py`, `data/orders/dao.py`, `admin/routes/web_public.py`, tests。
- 测试先行：撤销 token 后访问失败；旧 token 兼容策略明确。
- 实现：token payload 加 jti/version；落库 revocation。
- 验证：Portal token tests + portal page tests。

---

## Phase 3：Upload / Webhook / Delete / Migration

### T3-01 附件 magic bytes 校验

- 文件：`admin/routes/web_public.py`, `admin/tests/test_web_public_portal_info.py`, `admin/tests/test_order_info_upload.py`
- 测试先行：`.png` 伪装文本被拒；真实 PDF/PNG 通过。
- 验证：附件测试通过。

### T3-02 Alipay notify body limit

- 文件：`admin/routes/web_public.py`, `admin/tests/test_payment_alipay_notify.py`
- 测试先行：Content-Length 超限返回 413。
- 实现：读取 body 前检查 header，读取后再二次检查。

### T3-03 删除审计强制化

- 文件：`data/orders/dao.py`, `data/orders/deletion_service.py`, `admin/routes/orders.py`, tests。
- 测试先行：物理删除写 audit；actor/reason 缺失失败。

### T3-04 schema_migrations

- 文件：`data/orders/schema.py`, `data/payments/dao.py`, `data/notifications/email_service.py`, tests。
- 测试先行：旧库升级记录 migrations；重复 apply 幂等；失败回滚。

---

## Phase 4：Gates / Docker / CI

### T4-01 修 mypy 9 errors

- 文件：`admin/routes/sprint3_api.py`, `data/cli_compat_share.py`, `data/share/poster.py`, requirements/types。
- 验证：`.venv/bin/python -m mypy .`

### T4-02 Poster Docker 可复现构建

- 文件：`Dockerfile.poster`, `.github/workflows/ci.yml`, `tests/test_poster_cli_docker_contract.py`
- 验证：`docker build -f Dockerfile.poster -t gaokao-poster-cli:review .`

### T4-03 compose healthcheck 端口一致

- 文件：`docker-compose.yml`, tests。
- 验证：非默认端口 compose config / healthcheck 测试。

### T4-04 LHCI / Chromatic / smoke gate 语义

- 文件：`.github/workflows/web-ci.yml`, `apps/web/lighthouserc.cjs`, `scripts/dev-verify.sh`
- 验证：workflow lint + 本地 lhci dry run（可行时）+ smoke gate 明确状态。

---

## Phase 5：最终回归

### T5-01 全量本地 gate

```bash
bash scripts/dev-verify.sh
pnpm typecheck
pnpm lint
pnpm test
pnpm build
pnpm --filter @gaokao/web test:e2e
```

### T5-02 视觉与用户流程验收

- 启动本地服务。
- 浏览器走：首页 → review → pricing/checkout → portal → admin login → admin nav。
- 关键页面截图/vision 或等价视觉基线。

### T5-03 文档状态回写

- 更新 Review 报告状态。
- 更新 CURRENT_STATE。
- 标记 ACTIVE_REMEDIATION 已完成/待线上 acceptance。

---

## 提交策略

- 每个 T 任务独立 commit。
- 每个 Phase 完成后推送 gitea/origin/tksea。
- 任一 gate 失败不得继续后续 Phase，先修复或降级并记录。
