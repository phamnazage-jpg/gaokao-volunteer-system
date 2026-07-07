# 2026-07-07 Review Remediation 系统性修复方案与分阶段任务清单

> **For Hermes:** 使用 subagent-driven-development skill 按任务逐条执行本计划。
>
> **Goal:** 把 `reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md` 中发现的 P0/P1/P2 问题逐项收敛到本地门禁全绿 + 文档真相同步，为后续线上真实 acceptance 提供干净的基线。
>
> **输入真相源：**
> - `reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md`（本轮 Review 报告，含 H1–H10、M1–M9、L1–L2）
> - 当前 HEAD：`43fc6b2`
>
> **执行原则：** 每个任务 TDD（先写失败测试 → 实现 → 验证通过）→ 提交 → 三远端同步。任一 gate 失败不得继续后续 Phase，先修复或降级并记录。
>
> **重要边界：** 本计划只覆盖本地代码/门禁/文档修复。线上真实支付、域名、真实流量 acceptance 不在本计划范围，将在 Phase 5 完成后单独排期。

---

## 0. 阶段依赖图

```text
Phase 0 Truth Source Sync
  → Phase 1 Backend Gate Fix (mypy)
  → Phase 2 Frontend Unit Gate Fix (i18n)
  → Phase 3 E2E Gate Fix (poster/share + 浏览器环境)
  → Phase 4 Security & Ops Hardening (CSV/escape/README/compose/gitignore)
  → Phase 5 Final Regression & Evidence
```

依赖说明：
- Phase 0 必须先做，否则后续执行者会按"Phase 0~5 已完成"的旧文档误判。
- Phase 1/2/3 可并行（不同技术栈），但 Phase 5 必须在 1/2/3 全部完成后执行。
- Phase 4 可与 Phase 2/3 并行，但 CSV 安全修复应在 Phase 5 回归前完成。

---

## 1. 问题清单与根因映射

| ID | 报告章节 | 根因摘要 | 归属 Phase |
|---|---|---|---|
| H1/H6 | §3/§11.2 | CURRENT_STATE / active board 仍称 Phase 0~5 已完成，与 fresh gates 冲突 | Phase 0 |
| H2 | §3 | `admin/tests/test_sprint3_api_contract.py` helper 用 `dict[str, object]` 后直接做数值比较和 `len()`，mypy 报 3 errors | Phase 1 |
| H3 | §3 | `DashboardPage.tsx:42-52` `statusLabel()` 硬编码中文状态标签 | Phase 2 |
| H4/H7 | §3/§11.2 | poster/share E2E 失败根因：e2e spec 的 fallback mock 返回 `{}`，导致 `usePlansQuery().data.plans[0].id` 为 undefined → `selectedPlanId=null` → 按钮 disabled | Phase 3 |
| H5/H8 | §3/§11.2 | README 启动示例用内联 `$(python ...)` 生成 secret，在 agent/CI 环境会被脱敏为 `***` | Phase 4 |
| H9 | §11.2 | CSV 导出虽有 `_csv_safe_value`（admin/routes/orders.py:300），但 `data/orders/cli.py` 的 CSV 导出无 formula injection 中和 | Phase 4 |
| H10 | §11.2 | E2E 中 Vite proxy 大量 ECONNREFUSED，mock E2E 与 real-backend E2E 边界未分层 | Phase 3 |
| M1 | §4 | Playwright firefox/webkit 浏览器 executable 缺失 | Phase 3 |
| M3 | §4 | `admin/routes/web_public.py` 单文件 300KB，维护风险高 | Phase 5+（后续） |
| M4/M6 | §4/§11.3 | `web_public.py:2665` invalid escape sequence `\s` | Phase 4 |
| M5 | §4 | docker-compose 默认 payment provider=mock | Phase 4 |
| M7 | §11.3 | SQL `execute(f"...")` / subprocess / innerHTML 需白名单审计 | Phase 4 |
| M8 | §11.3 | OpenAPI 66 paths 已生成但 contract quartet 矩阵缺失 | Phase 5+（后续） |
| M9 | §11.3 | domain data 与 LLM prompt 承诺的覆盖率验收未做成 gate | Phase 5+（后续） |
| L1 | §5 | `data/share/short_links.db-shm` / `.db-wal` 未跟踪，`.gitignore` 无 `data/share/` 规则 | Phase 4 |
| L2 | §5 | `.worktrees/` / `.turbo/cache/` / 旧截图噪音 | Phase 5+（后续） |

---

## Phase 0：真相源同步

### T0-01 降级 CURRENT_STATE 状态句

**目标：** 把 `docs/CURRENT_STATE.md` 顶部状态从"本地验证完成（Phase 0~5 全部通过）"降级为"本地门禁回归中 / REQUEST_CHANGES"。

**文件：**
- Modify: `docs/CURRENT_STATE.md`

**步骤：**

1. 读取 `docs/CURRENT_STATE.md` 前 40 行。
2. 把 `状态词:` 行改为：
   ```
   状态词: `本地门禁回归中 / REQUEST_CHANGES / 线上真实 acceptance 待执行`
   ```
3. 把"Review Remediation Phase 0~5 已全部完成"段落改为：
   ```
   - 2026-07-07 二次严格 Review 已完成：`reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md`
   - 当前 fresh gates 结果：后端 mypy 3 errors、前端 i18n gate 1 failed、Playwright E2E poster/share 真实交互失败
   - 修复计划：`docs/plans/2026-07-07-review-remediation-execution-plan.md`
   ```
4. 保留"禁止提前声称"段落不变。

**验证：**
```bash
grep -n '本地门禁回归中\|REQUEST_CHANGES' docs/CURRENT_STATE.md | head -5
grep -c 'Phase 0~5 全部通过' docs/CURRENT_STATE.md  # 应为 0 或仅出现在历史快照段落
```

### T0-02 标记旧 active board 为历史快照

**目标：** 把 `docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md` 和 `docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md` 顶部加历史快照 banner，指向当前真相源。

**文件：**
- Modify: `docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`
- Modify: `docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`

**步骤：**

1. 在每个文件顶部（frontmatter 之后）插入：
   ```markdown
   > ⚠️ **历史快照（2026-07-07）**：本文件所称"Phase 0~5 全部完成"已被 2026-07-07 二次严格 Review 推翻。
   > 当前真相源：`docs/CURRENT_STATE.md` + `reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md`
   > 修复计划：`docs/plans/2026-07-07-review-remediation-execution-plan.md`
   > 本文件仅作历史审计轨迹，不再代表当前 HEAD 的完成状态。
   ```

**验证：**
```bash
grep -l '历史快照（2026-07-07）' docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md
```

### T0-03 更新 README 当前状态行

**目标：** README 顶部"当前状态"行与新真相源一致。

**文件：**
- Modify: `README.md`

**步骤：**

1. 把 README 行 20 的"当前状态"改为：
   ```
   > 当前状态：2026-07-07 二次严格 Review 发现后端 mypy / 前端 i18n / Playwright E2E 三项门禁回归未闭环，正在按 `docs/plans/2026-07-07-review-remediation-execution-plan.md` 系统修复；线上真实支付/域名/真实流量 acceptance 仍未完成。
   ```

**验证：**
```bash
grep -n '2026-07-07 二次严格 Review' README.md
```

### T0-04 提交 Phase 0

```bash
git add docs/CURRENT_STATE.md docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md README.md
git commit -m "docs(truth): T0 sync truth source to 2026-07-07 REQUEST_CHANGES"
git push gitea main && git push origin main && git push tksea main
```

---

## Phase 1：后端 mypy 门禁修复

### T1-01 修 test_sprint3_api_contract.py 类型收窄

**目标：** 消除 `admin/tests/test_sprint3_api_contract.py` 的 3 个 mypy errors。

**根因：** helper 函数签名为 `dict[str, object]`，但直接对 `item[numeric_key]`（类型 `object`）做 `>= 0` 比较和 `len(body["items"])`。

**文件：**
- Modify: `admin/tests/test_sprint3_api_contract.py:125-165`

**Step 1: 先确认当前 mypy 失败**

```bash
.venv/bin/python -m mypy admin/tests/test_sprint3_api_contract.py
```
Expected: 3 errors at lines 133, 141, 162.

**Step 2: 修复 `_assert_admin_share_link_shape`（line 130-133）**

把：
```python
    for numeric_key in ["access_count", "views", "unique_visitors", "uniqueVisitors"]:
        if numeric_key in item and item[numeric_key] is not None:
            assert isinstance(item[numeric_key], int)
            assert item[numeric_key] >= 0
```
改为：
```python
    for numeric_key in ["access_count", "views", "unique_visitors", "uniqueVisitors"]:
        if numeric_key in item and item[numeric_key] is not None:
            value: object = item[numeric_key]
            assert isinstance(value, int)
            assert value >= 0
```

**Step 3: 修复 `_assert_admin_share_link_page`（line 136-141）**

把：
```python
    assert isinstance(body["total"], int)
    assert body["total"] >= len(body["items"])
```
改为：
```python
    total: object = body["total"]
    assert isinstance(total, int)
    items: object = body["items"]
    assert isinstance(items, list)
    assert total >= len(items)
```

**Step 4: 修复 `_assert_admin_poster_page`（line 157-162）**

同样模式：把 `body["total"]` 和 `body["items"]` 先赋给局部 `object` 变量，再 `isinstance` 收窄。

**Step 5: 验证 mypy 通过**

```bash
.venv/bin/python -m mypy admin/tests/test_sprint3_api_contract.py
.venv/bin/python -m mypy .
```
Expected: 0 errors.

**Step 6: 验证 pytest 仍通过**

```bash
.venv/bin/python -m pytest admin/tests/test_sprint3_api_contract.py -q
```
Expected: all passed.

### T1-02 提交 Phase 1

```bash
git add admin/tests/test_sprint3_api_contract.py
git commit -m "fix(types): T1 narrow object types in sprint3 contract test helpers for mypy"
git push gitea main && git push origin main && git push tksea main
```

**Phase 1 完成标准：** `bash scripts/dev-verify.sh` exit=0。

---

## Phase 2：前端 i18n 门禁修复

### T2-01 新增状态标签 i18n keys

**目标：** 把 `DashboardPage.tsx:42-52` 的硬编码中文状态标签迁入 i18n messages。

**文件：**
- Modify: `apps/web/src/i18n/messages/zh-CN.json`
- Modify: `apps/web/src/i18n/messages/en-US.json`

**Step 1: 在 `zh-CN.json` 的 `admin.dashboard` 命名空间新增 keys**

在 `admin.dashboard.orders.statusNeedsRevision` 之后追加：
```json
  "admin.dashboard.orderStatus.pending": "待处理",
  "admin.dashboard.orderStatus.paid": "已支付",
  "admin.dashboard.orderStatus.serving": "服务中",
  "admin.dashboard.orderStatus.delivered": "已交付",
  "admin.dashboard.orderStatus.completed": "已完成",
  "admin.dashboard.orderStatus.refunded": "已退款",
```

**Step 2: 在 `en-US.json` 同步追加对应英文**

```json
  "admin.dashboard.orderStatus.pending": "Pending",
  "admin.dashboard.orderStatus.paid": "Paid",
  "admin.dashboard.orderStatus.serving": "In service",
  "admin.dashboard.orderStatus.delivered": "Delivered",
  "admin.dashboard.orderStatus.completed": "Completed",
  "admin.dashboard.orderStatus.refunded": "Refunded",
```

**Step 3: 验证 zh/en keys 对齐**

```bash
node -e "
const zh=require('./apps/web/src/i18n/messages/zh-CN.json');
const en=require('./apps/web/src/i18n/messages/en-US.json');
const zk=Object.keys(zh).sort(), ek=Object.keys(en).sort();
console.log('zh='+zk.length+' en='+ek.length);
console.log('aligned='+JSON.stringify(zk===ek));
"
```
Expected: `aligned=true`.

### T2-02 改 DashboardPage statusLabel 用 intl

**文件：**
- Modify: `apps/web/src/pages/admin/DashboardPage.tsx:42-52`

**Step 1: 把 `statusLabel` 改为接收 `intl` 并用 `formatMessage`**

把：
```tsx
function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '待处理',
    paid: '已支付',
    serving: '服务中',
    delivered: '已交付',
    completed: '已完成',
    refunded: '已退款',
  };
  return labels[status] ?? status;
}
```
改为：
```tsx
function statusLabel(status: string, intl: IntlShape): string {
  const key = `admin.dashboard.orderStatus.${status}`;
  const message = intl.messages[key];
  return typeof message === 'string' ? message : status;
}
```

**Step 2: 在 `AdminDashboardPage` 组件内更新调用**

把 `accessor: (row) => statusLabel(row.status)` 改为 `accessor: (row) => statusLabel(row.status, intl)`。

**Step 3: 确保 `IntlShape` 已 import**

在文件顶部追加：
```tsx
import type { IntlShape } from 'react-intl';
```

**Step 4: 验证无硬编码中文**

```bash
grep -n '待处理\|已支付\|服务中\|已交付\|已完成\|已退款' apps/web/src/pages/admin/DashboardPage.tsx
```
Expected: 0 matches.

### T2-03 验证 i18n gate

```bash
cd apps/web && pnpm test -- --reporter=verbose src/quality/i18nMessagesCoverage.test.ts
```
Expected: all passed.

### T2-04 提交 Phase 2

```bash
git add apps/web/src/i18n/messages/zh-CN.json apps/web/src/i18n/messages/en-US.json apps/web/src/pages/admin/DashboardPage.tsx
git commit -m "fix(i18n): T2 migrate DashboardPage status labels to i18n messages"
git push gitea main && git push origin main && git push tksea main
```

**Phase 2 完成标准：** `pnpm test` 全绿。

---

## Phase 3：E2E 门禁修复

### T3-01 安装 Playwright 缺失浏览器

**目标：** 消除 firefox/webkit browser executable 缺失导致的 60 个 E2E 失败。

**步骤：**

```bash
cd apps/web
pnpm exec playwright install --with-deps firefox webkit
```

**验证：**
```bash
ls ~/.cache/ms-playwright/ | grep -E 'firefox|webkit'
```
Expected: firefox-*/firefox/firefox 和 webkit-*/... 存在。

### T3-02 修 poster E2E spec：预置 plans mock 数据

**目标：** 消除 poster E2E 中"生成海报"按钮 disabled 的根因。

**根因：** `PosterPreviewPage` 使用 `usePlansQuery()` → `selectedPlanId = plansQuery.data?.plans[0]?.id ?? null`。E2E spec 的 fallback mock 返回 `{}`，导致 `plans` 为 undefined → `selectedPlanId=null` → 按钮 disabled。

**文件：**
- Modify: `apps/web/e2e/poster-generate-download.spec.ts`

**Step 1: 在每个 test 的 fallback mock 之前，新增 `/api/plans` 的精确 mock**

在每个 test 的 `await page.goto('/poster')` 之前，插入：
```typescript
    await page.route('**/api/plans', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          plans: [
            { id: 'plan-e2e-001', title: 'E2E 测试方案', updatedAt: '2026-07-07T00:00:00Z' },
          ],
        }),
      });
    });
```

**Step 2: 确认 fallback mock 不再覆盖 `/api/plans`**

检查 fallback route 的 predicate：`url.pathname.startsWith('/api/') && !url.pathname.includes('/poster/')`。`/api/plans` 会被 fallback 匹配，但 Playwright 按注册顺序调用第一个匹配的 handler，所以 `/api/plans` 的精确 mock 会先命中。

**Step 3: 验证 targeted chromium e2e**

```bash
cd apps/web && pnpm exec playwright test e2e/poster-generate-download.spec.ts --project=chromium --reporter=line
```
Expected: 3 passed.

### T3-03 修 share E2E spec：预置 share-link/latest mock 数据

**目标：** 消除 share E2E 中"创建分享链接（30天有效）"按钮 disabled 的根因。

**根因：** `ShareDialogPage` 使用 `useShareLinkLatestQuery()` → `selectedPlanId = latest.data?.planId ?? ''`。E2E spec mock `/api/share-link/latest` 返回 `null`，导致 `selectedPlanId=''` → `canCreate=Boolean('')` = false → 按钮 disabled。

**文件：**
- Modify: `apps/web/e2e/share-link-failure-fallback.spec.ts`

**Step 1: 把 `/api/share-link/latest` 的 mock 从返回 `null` 改为返回带 `planId` 的对象**

把：
```typescript
    await page.route((url) => url.pathname === '/api/share-link/latest', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'null',
      });
    });
```
改为：
```typescript
    await page.route((url) => url.pathname === '/api/share-link/latest', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          code: 'share-e2e-latest',
          planId: 'plan-e2e-001',
          resultType: 'review_result',
          createdAt: '2026-07-07T00:00:00Z',
          expiresAt: '2026-08-06T00:00:00Z',
        }),
      });
    });
```

**Step 2: 验证 targeted chromium e2e**

```bash
cd apps/web && pnpm exec playwright test e2e/share-link-failure-fallback.spec.ts --project=chromium --reporter=line
```
Expected: 1 passed.

### T3-04 拆分 mock E2E 与 real-backend E2E 命令

**目标：** 解决 H10——mock E2E 与 real-backend E2E 边界未分层。

**文件：**
- Modify: `apps/web/package.json`
- Create: `docs/FRONTEND_E2E_RUNBOOK_2026-07-07.md`

**Step 1: 在 `apps/web/package.json` 的 scripts 中拆分**

把：
```json
    "test:e2e": "playwright test"
```
改为：
```json
    "test:e2e": "playwright test",
    "test:e2e:mock": "playwright test",
    "test:e2e:real-backend": "GAOKAO_E2E_REAL_BACKEND=1 playwright test"
```

**Step 2: 创建 E2E runbook 文档**

在 `docs/FRONTEND_E2E_RUNBOOK_2026-07-07.md` 中说明：
- `test:e2e:mock`：默认模式，所有 API 通过 Playwright `page.route()` mock，不依赖真实后端。
- `test:e2e:real-backend`：需要先启动 FastAPI 后端（`python -m admin.app --port 8000`），验证 `/health` 返回 `settings_valid=true`，再运行 E2E。
- 当前所有 E2E spec 都是 mock 模式；real-backend 模式将在后续 Phase 补真实后端联调用例。

### T3-05 提交 Phase 3

```bash
git add apps/web/e2e/poster-generate-download.spec.ts apps/web/e2e/share-link-failure-fallback.spec.ts apps/web/package.json docs/FRONTEND_E2E_RUNBOOK_2026-07-07.md
git commit -m "fix(e2e): T3 pre-seed plans/share-link mock data + split mock/real-backend e2e commands"
git push gitea main && git push origin main && git push tksea main
```

**Phase 3 完成标准：** `pnpm --filter @gaokao/web test:e2e --project=chromium` 全绿。

---

## Phase 4：安全与运维加固

### T4-01 补 CSV formula injection 中和到 data/orders/cli.py

**目标：** 消除 H9——`data/orders/cli.py` 的 CSV 导出无 formula injection 中和。

**文件：**
- Modify: `data/orders/cli.py:328-331`
- Modify: `data/orders/tests/test_cli.py`

**Step 1: 先写失败测试**

在 `data/orders/tests/test_cli.py` 中新增：
```python
def test_export_command_neutralizes_csv_formula_injection(tmp_db_path: Path) -> None:
    """CSV 导出必须中和 = + - @ 前缀的危险值。"""
    # seed an order with dangerous name
    ...
    # export
    ...
    # read CSV
    rows = list(csv.DictReader(fh))
    for row in rows:
        for val in row.values():
            if val:
                assert not val.startswith(('=', '+', '-', '@')), f"dangerous prefix in: {val}"
```

**Step 2: 运行测试确认失败**

```bash
.venv/bin/python -m pytest data/orders/tests/test_cli.py::test_export_command_neutralizes_csv_formula_injection -q
```
Expected: FAIL.

**Step 3: 在 `data/orders/cli.py` 的 export 函数中引入 `_csv_safe_value`**

参照 `admin/routes/orders.py:300` 的 `_csv_safe_value` 实现，在 `data/orders/cli.py` 中复用或复制该 helper，并在 `writer.writerow` 前对每个值调用它。

**Step 4: 验证测试通过**

```bash
.venv/bin/python -m pytest data/orders/tests/test_cli.py::test_export_command_neutralizes_csv_formula_injection -q
```
Expected: PASS.

### T4-02 修 web_public.py invalid escape sequence

**目标：** 消除 M6——`admin/routes/web_public.py:2665` 的 `DeprecationWarning: invalid escape sequence '\s'`。

**文件：**
- Modify: `admin/routes/web_public.py`（定位含 `\s` 的 f-string）

**Step 1: 定位**

```bash
grep -n '\\s' admin/routes/web_public.py | head -10
```

**Step 2: 修复**

根据上下文：
- 如果是 regex `\s`，改为 raw string `r"..."` 或 `\\s`。
- 如果是 HTML/CSS 中的反斜杠，改为 `\\` 或拆出到 `.css` 文件。
- 如果是 f-string 中的字面 `\s`，改为 `\\s`。

**Step 3: 验证 warning 消失**

```bash
.venv/bin/python -W error::DeprecationWarning -c "import admin.routes.web_public"
```
Expected: no DeprecationWarning.

### T4-03 README secret 启动改为 env file 模式

**目标：** 消除 H5/H8——README 内联 secret 生成方式。

**文件：**
- Modify: `README.md:149-155`

**Step 1: 把 README 中的启动示例改为**

```bash
# 生成 secret 到临时 env 文件（避免内联 secret 被 shell/agent 脱敏）
python3 -c "
import secrets
from cryptography.fernet import Fernet
print(f'export GAOKAO_JWT_SECRET={secrets.token_hex(32)}')
print(f'export GAOKAO_PORTAL_TOKEN_SECRET={secrets.token_hex(32)}')
print(f'export GAOKAO_PAYMENT_WEBHOOK_SECRET={secrets.token_hex(32)}')
print(f'export GAOKAO_ORDERS_FERNET_KEY={Fernet.generate_key().decode()}')
" > /tmp/gaokao.env && chmod 600 /tmp/gaokao.env

# source 后启动
set -a; source /tmp/gaokao.env; set +a
python -m admin.app --port 8000

# 验证 settings_valid=true
curl -s http://127.0.0.1:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('settings_valid:', d['checks']['settings_valid'])"
```

### T4-04 docker-compose 拆分 local/prod payment provider 默认值

**目标：** 消除 M5——docker-compose 默认 payment provider=mock。

**文件：**
- Modify: `docker-compose.yml`
- Create: `docker-compose.prod.yml`（或在现有 compose 中用 `profiles` 区分）

**Step 1: 在 `docker-compose.yml` 中保留 `mock` 默认（本地开发用），但加注释**

```yaml
      # 本地开发默认 mock；生产必须用 docker-compose.prod.yml 或显式设置 GAOKAO_PAYMENT_PROVIDER=alipay
      GAOKAO_PAYMENT_PROVIDER: ${GAOKAO_PAYMENT_PROVIDER:-mock}
```

**Step 2: 创建 `docker-compose.prod.yml` override**

```yaml
services:
  gaokao-admin:
    environment:
      GAOKAO_PAYMENT_PROVIDER: ${GAOKAO_PAYMENT_PROVIDER:?GAOKAO_PAYMENT_PROVIDER must be set in prod}
```

### T4-05 .gitignore 补 data/share/ 规则

**目标：** 消除 L1——`data/share/short_links.db-shm` / `.db-wal` 未跟踪。

**文件：**
- Modify: `.gitignore`

**Step 1: 在 `.gitignore` 中追加**

```
/data/share/*.db
/data/share/*.db-*
```

**Step 2: 清理当前未跟踪文件**

```bash
rm -f data/share/short_links.db-shm data/share/short_links.db-wal
git status --short
```
Expected: 无 `?? data/share/` 行。

### T4-06 SQL/subprocess/innerHTML 安全白名单审计

**目标：** 消除 M7——对 H9 扫描命中的危险 API 位置做白名单审计。

**文件：**
- Create: `docs/SECURITY_AUDIT_2026-07-07.md`

**Step 1: 逐项审计命中位置，分类为：**

- **安全（受控表名/列名）**：`data/payments/dao.py:41,44` 的 `PRAGMA table_info({table})` / `ALTER TABLE {table}`（table 来自硬编码常量）。
- **安全（测试用 subprocess）**：`admin/tests/test_order_status_page.py:127`、`tests/test_*.py` 中的 `subprocess.run`（无 `shell=True`，参数为列表）。
- **需修复**：`admin/routes/web_public.py:1281,2921` 的 `innerHTML` 赋值（如果拼接用户输入则需改为 textContent 或 DOMPurify）。
- **安全（vendored）**：`admin/static/vendor/echarts.min.js` 的 `innerHTML`（已做 HTML escape）。

**Step 2: 在审计文档中记录分类结果**

### T4-07 提交 Phase 4

```bash
git add data/orders/cli.py data/orders/tests/test_cli.py admin/routes/web_public.py README.md docker-compose.yml docker-compose.prod.yml .gitignore docs/SECURITY_AUDIT_2026-07-07.md
git commit -m "fix(security,ops): T4 CSV injection guard + escape fix + README env + compose split + gitignore"
git push gitea main && git push origin main && git push tksea main
```

---

## Phase 5：最终回归与证据

### T5-01 全量本地 gate

```bash
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
pnpm typecheck
pnpm lint
pnpm test
pnpm build
pnpm --filter @gaokao/web test:e2e --project=chromium
pnpm --filter @gaokao/web test:e2e --project=firefox
pnpm --filter @gaokao/web test:e2e --project=webkit
pnpm --filter @gaokao/web test:e2e --project=mobile-chrome
pnpm --filter @gaokao/web test:e2e --project=mobile-safari
docker build -f Dockerfile.poster -t gaokao-poster-cli:review-final .
```

**完成标准：**
- `dev-verify.sh` exit=0
- `pnpm test` 0 failed
- `pnpm test:e2e` 0 failed（全 5 个 project）
- Docker poster build PASS

### T5-02 视觉与用户流程验收

- 启动本地服务（用 Phase 4 的 env file 模式）。
- 浏览器走：首页 → review → pricing/checkout → mock payment → portal → admin login → admin nav → poster → share。
- 关键页面截图/vision。
- 验证 `/health` 返回 `settings_valid=true`。

### T5-03 文档状态回写

**文件：**
- Modify: `docs/CURRENT_STATE.md`
- Modify: `docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`（追加 Phase 5 完成回写）
- Modify: `reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md`（追加整改完成回写）

**Step 1: 更新 CURRENT_STATE 顶部状态为：**

```
状态词: `本地门禁全绿（Phase 1~4 修复完成）/ 线上真实 acceptance 待执行`
```

**Step 2: 在 review 报告末尾追加整改完成回写**

```markdown
## 12. 2026-07-07 整改完成回写

- Phase 0 (T0-01~T0-04): 真相源同步完成
- Phase 1 (T1-01~T1-02): mypy 3 errors 修复完成，dev-verify exit=0
- Phase 2 (T2-01~T2-04): Dashboard i18n 硬编码修复完成，pnpm test 全绿
- Phase 3 (T3-01~T3-05): poster/share E2E 修复完成，全 5 project e2e 全绿
- Phase 4 (T4-01~T4-07): CSV/escape/README/compose/gitignore/security audit 完成
- Phase 5 (T5-01~T5-03): 全量门禁 + 视觉验收 + 文档回写完成
- 仍不能宣称生产级完成；线上真实支付/域名/真实流量 acceptance 仍未执行。
```

### T5-04 提交 Phase 5

```bash
git add docs/CURRENT_STATE.md docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md
git commit -m "docs(truth): T5 final regression passed + status sync to local gates green"
git push gitea main && git push origin main && git push tksea main
```

---

## 后续（Phase 5+，不在本计划范围）

以下属于结构性治理 / 长期防复发，不阻塞当前 Phase 0~5 闭环：

- **M3**：拆分 `admin/routes/web_public.py`（300KB → 按业务域拆 5-6 个模块）。
- **M8**：补 OpenAPI → backend route → React api-generated types → frontend caller 的 contract quartet 矩阵。
- **M9**：把 domain data 与 LLM prompt 承诺的覆盖率做成发布前 gate。
- **L2**：清理 `.worktrees/` / `.turbo/cache/` / 旧截图归档。
- **线上 acceptance**：真实支付 / 域名 / 真实流量 / 真实 SMTP / 真实 LLM provider。

---

## 提交策略

- 每个 T 任务独立 commit。
- 每个 Phase 完成后推送 gitea/origin/tksea 三远端。
- 任一 gate 失败不得继续后续 Phase，先修复或降级并记录。
- 提交 message 格式：`<type>(<scope>): T<n> <description>`

---

## 完成标准总表

| Phase | 完成标准 | 验证命令 |
|---|---|---|
| Phase 0 | CURRENT_STATE / active board / README 同步到 REQUEST_CHANGES | `grep` 验证 |
| Phase 1 | dev-verify exit=0，mypy 0 errors | `bash scripts/dev-verify.sh` |
| Phase 2 | pnpm test 0 failed | `pnpm test` |
| Phase 3 | 全 5 project e2e 0 failed | `pnpm --filter @gaokao/web test:e2e` |
| Phase 4 | CSV/escape/README/compose/gitignore/security audit 完成 | 逐项验证 |
| Phase 5 | 全量 gate + 视觉验收 + 文档回写 | T5-01 + T5-02 + T5-03 |

---

## V2 评审优化覆盖声明

> v2 来源：`docs/plans/2026-07-07-review-remediation-plan-audit.md`  
> v2 结论：v1 方向正确但覆盖不完整；v2 将 M3/M8/M9/L2 从 Phase 5+ 提升为必做项，并强化 E2E、Security、CI/readback 验收。

### V2 范围变更

1. **不再把 M3/M8/M9/L2 视为后续可选项**：这些是 review 报告问题，必须有 Phase 5 闭环任务。
2. **T3 E2E 修复必须证明显式 enabled 状态**：不允许只改 mock 后假设点击可用。
3. **M7 安全项必须代码级判断**：innerHTML / SQL execute / subprocess 不只写审计文档，能修的必须修。
4. **最终验收升级为 Phase 6**：加入 working tree clean、三远端 readback、CI 状态、浏览器视觉/真实用户流。

### V2 新阶段依赖图

```text
Phase 0 Truth Source Sync
  → Phase 1 Backend Gate Fix (mypy)
  → Phase 2 Frontend Unit Gate Fix (i18n)
  → Phase 3 E2E Gate Fix (poster/share + mock/real split)
  → Phase 4 Security & Ops Hardening (CSV/escape/README/compose/gitignore/innerHTML)
  → Phase 5 Structural Governance Completion (M3/M8/M9/L2)
  → Phase 6 Final Regression, CI Readback & Evidence
```

---

## Phase 2 v2 修正：Dashboard i18n 实现方式

替换 v1 T2-02 的实现建议：

```tsx
import type { IntlShape } from 'react-intl';

const statusMessageIds: Record<string, string> = {
  pending: 'admin.dashboard.orderStatus.pending',
  paid: 'admin.dashboard.orderStatus.paid',
  serving: 'admin.dashboard.orderStatus.serving',
  delivered: 'admin.dashboard.orderStatus.delivered',
  completed: 'admin.dashboard.orderStatus.completed',
  refunded: 'admin.dashboard.orderStatus.refunded',
};

function statusLabel(status: string, intl: IntlShape): string {
  const id = statusMessageIds[status];
  return id ? intl.formatMessage({ id }) : status;
}
```

新增验证：

```bash
pnpm --filter @gaokao/web test src/pages/admin/DashboardPage.test.tsx src/quality/i18nMessagesCoverage.test.ts
pnpm test
```

---

## Phase 3 v2 修正：E2E mock/real 分层必须可验证

### T3-02-v2 建立 E2E mock helper

**文件：**
- Create: `apps/web/e2e/helpers/mock-api.ts`
- Modify: `apps/web/e2e/poster-generate-download.spec.ts`
- Modify: `apps/web/e2e/share-link-failure-fallback.spec.ts`

**实现要求：**

```ts
import type { Page, Route } from '@playwright/test';

export async function mockPlans(page: Page): Promise<void> {
  await page.route('**/api/plans', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        plans: [{ id: 'plan-e2e-001', title: 'E2E 测试方案', updatedAt: '2026-07-07T00:00:00Z' }],
      }),
    });
  });
}

export async function mockLatestShareLink(page: Page): Promise<void> {
  await page.route('**/api/share-link/latest', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 'share-e2e-latest',
        planId: 'plan-e2e-001',
        resultType: 'review_result',
        createdAt: '2026-07-07T00:00:00Z',
        expiresAt: '2026-08-06T00:00:00Z',
      }),
    });
  });
}
```

**强制测试断言：**

```ts
await expect(page.getByRole('button', { name: /生成海报/ })).toBeEnabled();
await expect(page.getByRole('button', { name: '创建分享链接（30天有效）' })).toBeEnabled();
```

**fallback 修正规则：**

不要依赖 route 注册顺序。fallback predicate 必须显式排除：

```ts
const passthroughMockExclusions = new Set(['/api/plans', '/api/share-link/latest', '/api/share-link']);
await page.route((url) =>
  url.pathname.startsWith('/api/') &&
  !passthroughMockExclusions.has(url.pathname) &&
  !url.pathname.includes('/poster/'),
  async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  },
);
```

### T3-04-v2 新增 real-backend smoke

**文件：**
- Create: `apps/web/e2e/real-backend-smoke.spec.ts`
- Modify: `apps/web/package.json`
- Modify: `docs/FRONTEND_E2E_RUNBOOK_2026-07-07.md`

**验收命令：**

```bash
set -a; source /tmp/gaokao.env; set +a
python -m admin.app --port 8000 &
curl -fsS http://127.0.0.1:8000/health | grep 'settings_valid'
pnpm --filter @gaokao/web test:e2e:real-backend -- --project=chromium e2e/real-backend-smoke.spec.ts
```

---

## Phase 4 v2 修正：Security & Ops 必须代码级闭环

### T4-06-v2 innerHTML 修复任务

**目标：** 对 review 命中的 `admin/routes/web_public.py:1281,2921` 做代码级收口。

**文件：**
- Modify: `admin/routes/web_public.py`
- Test: `admin/tests/test_web_public_content_pages.py` 或新增 `admin/tests/test_web_public_xss_safety.py`

**步骤：**
1. 定位 `innerHTML` 数据来源。
2. 若拼接值可能来自用户输入或 URL/query/form，改为 `textContent` 或 DOM 构造。
3. 若只来自常量，添加注释与安全审计记录。
4. 新增测试注入 `<img src=x onerror=alert(1)>` 或 `<script>`，断言响应不包含未转义脚本/事件处理器。

### T4-08-v2 compose prod 验证

```bash
docker compose -f docker-compose.yml config >/tmp/compose.local.yml
GAOKAO_PAYMENT_PROVIDER=alipay docker compose -f docker-compose.yml -f docker-compose.prod.yml config >/tmp/compose.prod.yml
! grep -q 'GAOKAO_PAYMENT_PROVIDER: mock' /tmp/compose.prod.yml
```

---

## Phase 5 v2：Structural Governance Completion

### T5-01-v2 web_public.py 拆分第一步

**目标：** 不把 M3 无限期延后。先完成低风险结构治理：抽出 policy/content pages renderer 或 shared public shell helper。

**建议第一刀：**
- Create: `admin/routes/public_content_pages.py` 或 `admin/web_public/content_pages.py`
- Move/Extract: `/privacy`, `/service-terms`, `/policy-center`, `/deletion-policy` 的 markdown/content render helper
- Keep router registration unchanged or use sub-router include，确保 URL 不变。

**验证：**

```bash
.venv/bin/python -m pytest admin/tests/test_web_public_content_pages.py -q
python3 - <<'PY'
from pathlib import Path
p=Path('admin/routes/web_public.py')
print(p.stat().st_size)
assert p.stat().st_size < 300094
PY
```

### T5-02-v2 Contract Quartet Matrix

**目标：** 关闭 M8。

**文件：**
- Create: `docs/CONTRACT_QUARTET_MATRIX_2026-07-07.md`
- Create: `scripts/check_contract_quartet.py`
- Test: `tests/test_contract_quartet_matrix.py`

矩阵至少覆盖：
- `/api/auth/login`
- `/api/admin/stats/dashboard`
- `/api/public/orders`
- `/api/public/payments/alipay/notify`（注意当前 OpenAPI 探针显示 `False`，必须解释 include_in_schema 或文档边界）
- `/portal/{token}/cwb`
- `/portal/{token}/full-plan`
- `/api/llm/config`
- `/api/llm/{provider}/enhance`

每行必须包含：runtime route、OpenAPI path / include_in_schema reason、frontend generated type/schema、frontend caller/hook/page、test evidence。

### T5-03-v2 LLM/domain data coverage gate

**目标：** 关闭 M9。

**文件：**
- Create: `scripts/check_llm_domain_data_coverage.py`
- Test: `data/llm/tests/test_domain_data_coverage.py`
- Docs: `docs/LLM_DOMAIN_DATA_COVERAGE_2026-07-07.md`

检查逻辑：
- 从 `data/llm/prompts.py` 抽取特殊项目/路径名称。
- 从 `data/crowd_db/special_programs.json` 读取 `programs` / `program_schools`。
- 从 `data/rules/special_programs_rules.json` 读取 rules。
- 断言 prompt 提到的每个 program_type 在 data 和 rules 中都有对应项。
- 每类至少有最低 school count 或明确豁免 reason。

### T5-04-v2 Artifact governance

**目标：** 关闭 L2。

**文件：**
- Modify: `.gitignore`
- Create: `docs/ARTIFACT_GOVERNANCE_2026-07-07.md`
- Optional: `scripts/check_repo_artifacts.py`

规则：
- `.worktrees/`、`.turbo/cache/`、Playwright `test-results/`、旧截图目录必须有归档/忽略策略。
- 当前 review 证据目录保留，历史截图目录标注历史快照。
- 提交前 gate：`git status --short` 不得有 test artifact / db wal / cache。

---

## Phase 6 v2：Final Regression, CI Readback & Evidence

### T6-01-v2 全量本地门禁

```bash
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
pnpm typecheck
pnpm lint
pnpm test
pnpm build
pnpm --filter @gaokao/web test:e2e
```

### T6-02-v2 本地真实后端 + 视觉验收

- 使用 env file 启动 FastAPI。
- `/health.settings_valid=true`。
- 浏览器走：首页 → pricing → checkout → payment-success → portal/status → portal/info → admin login → dashboard → poster → share。
- 使用 screenshot/vision 保存证据到 `reports/t6_visual_acceptance_YYYYMMDD/`。

### T6-03-v2 Docker/compose gate

```bash
docker build -f Dockerfile.poster -t gaokao-poster-cli:review-final .
GAOKAO_PAYMENT_PROVIDER=alipay docker compose -f docker-compose.yml -f docker-compose.prod.yml config >/tmp/compose.prod.yml
```

### T6-04-v2 working tree clean + 三远端 readback

```bash
git status --short
LOCAL_SHA=$(git rev-parse HEAD)
for remote in gitea origin tksea; do
  git push "$remote" main
  REMOTE_SHA=$(git ls-remote "$remote" refs/heads/main | awk '{print $1}')
  test "$LOCAL_SHA" = "$REMOTE_SHA"
done
```

### T6-05-v2 文档最终回写

- `docs/CURRENT_STATE.md`：改为“本地门禁全绿 / 线上真实 acceptance 待执行”。
- `reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md`：追加整改完成证据。
- `docs/plans/2026-07-07-review-remediation-execution-plan-v2.md`：标记 completed evidence。

---

## v2 完成标准总表

| Phase | 完成标准 | 验证命令 |
|---|---|---|
| Phase 0 | truth docs 不再误称 Phase 0~5 completed | grep + read_file |
| Phase 1 | mypy/dev-verify 全绿 | `bash scripts/dev-verify.sh` |
| Phase 2 | i18n + frontend unit 全绿 | `pnpm test` |
| Phase 3 | mock E2E targeted/full 全绿，real-backend smoke 可运行 | `pnpm --filter @gaokao/web test:e2e` + real-backend smoke |
| Phase 4 | CSV/innerHTML/escape/README/compose/gitignore 均闭环 | targeted pytest + compose config + git status |
| Phase 5 | M3/M8/M9/L2 均有代码/脚本/文档级闭环 | contract/data/artifact scripts pass |
| Phase 6 | 本地全量 + 视觉 + Docker + 三远端 readback | T6-01~T6-05 |


---

## Phase 6 Completion Evidence

> 更新时间: 2026-07-07T13:14:04

- Core gates: PASS，详见 `reports/PHASE6_LOCAL_GATE_EVIDENCE_2026-07-07.md`。
- Runtime smoke: PASS，`/health.settings_valid=true`，核心页面 HTTP 200。
- Browser snapshots: PASS for `/`, `/pricing`, `/admin/login` accessibility snapshots。
- Visual acceptance: BLOCKED，原因是 `browser_vision` / `vision_analyze` provider key expired。
- Online real acceptance: pending，真实支付/域名/真实流量未执行。
