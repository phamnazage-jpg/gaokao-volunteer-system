# 2026-07-05 项目全面 Review 报告（真实复核版）

> 生成时间：2026-07-05T20:59:15+08:00  
> 审查对象：`/home/long/project/gaokao-volunteer-system`  
> 当前 HEAD：`4059f144c49398aec2fcc3040e639e1312061086`  
> 审查方式：真实读取代码/CI/脚本/现有报告 + 本地门禁执行 + 静态扫描；未把历史报告当作当前事实。  
> 重要边界：本报告是代码库与本地门禁 review，不等同于线上真实支付、真实域名、真实用户流量验收。  
> 复验更新：已在报告初稿后补装前端依赖并复跑 `pnpm typecheck/lint/test/build`，结果已回写到 §1.2 / M0。

---

## 0. 总结结论

**结论：REQUEST_CHANGES / 不能宣称生产级完成。**

本轮 review 发现的当前有效问题：

| 严重级别 | 数量 | 摘要 |
|---|---:|---|
| HIGH | 4 | Admin 导航断链、React Admin mock 登录未接真实 JWT、前端 API client 未注入 Authorization、本地 Python 总门禁 mypy 失败 |
| MEDIUM | 4 | Chromatic token 未配置会阻断 CI、LHCI 启动/端口口径仍有漂移风险、dev-verify 100-case smoke 非阻塞导致主链路回归可能被降级为 warning、前端依赖缺失曾阻断本地 fresh gate（已补装并复验通过） |
| LOW | 2 | 文档中仍大量保留 mock/sandbox 历史语境，旧截图报告目录仍在仓库中易误导；部分静态扫描命中需后续清理白名单 |

已确认的正向事实：

- `main / origin / gitea / tksea` 在上一轮已同步到 `4059f14`，本轮 review 起点工作区为 `## main`。
- `apps/web/src/types/api-generated.d.ts` 与 `apps/web/src/schemas/api-generated.ts` 当前 `any_count=0`。
- `/health` dev readiness 改动已进入 HEAD，`settings_valid` 在 dev 环境允许占位密钥，但 prod fail-closed 仍由配置加载策略覆盖。

---

## 1. Gate 结果（当前真实输出）

### 1.1 Python / 后端总门禁

命令来源：`/tmp/gaokao-review-gates-20260705.log`，由本轮执行：

```bash
bash scripts/dev-verify.sh
```

结果：**FAIL**。关键输出：

```text
admin/routes/sprint3_api.py:292: error: Incompatible types in assignment (expression has type "str", variable has type "Literal['pending', 'in_progress', 'approved', 'rejected', 'changes_requested']")  [assignment]
data/cli_compat_share.py:43: error: Item "None" of "_ArgumentGroup | None" has no attribute "_group_actions"  [union-attr]
data/cli_compat_share.py:44: error: Item "Action" of "Action | Any" has no attribute "add_parser"  [union-attr]
data/share/poster.py:123: error: Argument "candidate_name" to "PosterPayload" has incompatible type "str | None"; expected "str"  [arg-type]
data/share/poster.py:273: error: Incompatible return value type (got "FreeTypeFont", expected "ImageFont")  [return-value]
data/share/poster.py:274: error: Incompatible return value type (got "FreeTypeFont | ImageFont", expected "ImageFont")  [return-value]
data/share/poster.py:319: error: Incompatible return value type (got "float", expected "int")  [return-value]
data/share/poster.py:324: error: Incompatible return value type (got "float", expected "int")  [return-value]
data/share/poster.py:329: error: Library stubs not installed for "qrcode"  [import-untyped]
Found 9 errors in 3 files (checked 268 source files)
DEV_VERIFY_EXIT=1
```

影响：

- 这不是单测功能失败，而是类型门禁失败；按项目质量标准不能用“pytest 局部通过”覆盖。
- 失败集中在 poster / report 相关类型与缺失 third-party stubs，说明分享海报链路仍存在类型质量债。

### 1.2 前端本地门禁

第一轮执行结果：**BLOCKED**，原因是本地缺少 `node_modules` / `turbo`，未进入真实业务门禁。随后已补执行：

```bash
pnpm install --frozen-lockfile
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

复验结果：**PASS**。fresh evidence 来自 `/tmp/gaokao-frontend-gates-20260705.log`：

```text
=== FRONTEND FRESH GATES START ===
--- pnpm install ---
root node_modules exists
apps/web/node_modules exists
--- web typecheck ---
--- web lint ---
--- web test ---
--- web build ---
 Tasks:    2 successful, 2 total
 Tasks:    1 successful, 1 total
@gaokao/web:build: TOTAL                               │    1.36 MB │  393.60 KB │ ✅
@gaokao/web:build: ✅ T-B-25 验证通过
=== FRONTEND FRESH GATES END ===
```

更新判断：前端本地 typecheck/lint/test/build 当前已有 fresh gate 证据；原 H5 从 HIGH blocker 降级为 MEDIUM 环境/可复现性问题。仍需注意：这不自动证明 Playwright e2e、Chromatic、LHCI 或真实浏览器视觉验收已全部闭环。

---

## 2. HIGH Findings

### H1 · 后台导航 `/admin/review` 真实断链

**证据：**

`apps/web/src/layouts/AdminLayout.tsx` 注册了 `/admin/review`：

  - L12: `const adminNavItems = [`
  - L13: `  { to: '/admin', labelKey: 'admin.nav.dashboard', icon: Home },`
  - L14: `  { to: '/admin/orders', labelKey: 'admin.nav.orders', icon: FileText },`
  - L15: `  { to: '/admin/cases', labelKey: 'admin.nav.cases', icon: Users },`
  - L16: `  { to: '/admin/share-links', labelKey: 'admin.nav.shareLinks', icon: Link2 },`
  - L17: `  { to: '/admin/score-lines', labelKey: 'admin.nav.scoreLines', icon: Database },`
  - L18: `  { to: '/admin/rank-estimator', labelKey: 'admin.nav.rankEstimator', icon: TrendingUp },`
  - L19: `  { to: '/admin/majors', labelKey: 'admin.nav.majors', icon: BarChart3 },`
  - L20: `  { to: '/admin/schools', labelKey: 'admin.nav.schools', icon: School },`
  - L21: `  { to: '/admin/review', labelKey: 'admin.nav.review', icon: ShieldCheck },`
  - L22: `  { to: '/admin/posters', labelKey: 'admin.nav.posters', icon: BarChart3 },`
  - L23: `] as const;`

`apps/web/src/router.tsx` 的 `/admin` 子路由没有 `review`：

  - L64: `  { path: '/admin/login', element: <AdminLoginPage /> },`
  - L65: `  { path: '/403', element: <ForbiddenPage /> },`
  - L66: `  {`
  - L67: `    path: '/admin',`
  - L68: `    element: (`
  - L69: `      <RequireAuth>`
  - L70: `        <AdminLayout />`
  - L71: `      </RequireAuth>`
  - L72: `    ),`
  - L73: `    children: [`
  - L74: `      { index: true, element: <AdminDashboardPage /> },`
  - L75: `      { path: 'orders', element: <AdminOrdersPage /> },`
  - L76: `      { path: 'orders/:orderId', element: <AdminOrderDetailPage /> },`
  - L77: `      { path: 'cases', element: <AdminCasesPage /> },`
  - L78: `      { path: 'cases/:caseId', element: <AdminCaseDetailPage /> },`
  - L79: `      { path: 'share-links', element: <AdminShareLinksPage /> },`
  - L80: `      { path: 'share-links/:code', element: <AdminShareLinkDetailPage /> },`
  - L81: `      { path: 'posters', element: <AdminPostersPage /> },`
  - L82: `      { path: 'score-lines', element: <AdminScoreLinesPage /> },`
  - L83: `      { path: 'rank-estimator', element: <AdminRankEstimatorPage /> },`
  - L84: `      { path: 'majors', element: <AdminMajorsPage /> },`
  - L85: `      { path: 'schools', element: <AdminSchoolsPage /> },`
  - L86: `      { path: 'error', element: <AdminErrorPage /> },`
  - L87: `      { path: '*', element: <NotFoundPage /> },`
  - L88: `    ],`

静态路由对照结果：

```text
nav=['/admin', '/admin/orders', '/admin/cases', '/admin/share-links', '/admin/score-lines', '/admin/rank-estimator', '/admin/majors', '/admin/schools', '/admin/review', '/admin/posters']
admin_routes=['/admin/*', '/admin/cases', '/admin/cases/:caseId', '/admin/error', '/admin/majors', '/admin/orders', '/admin/orders/:orderId', '/admin/posters', '/admin/rank-estimator', '/admin/schools', '/admin/score-lines', '/admin/share-links', '/admin/share-links/:code']
missing=['/admin/review']
```

**影响：** 后台用户点击“复核 / Review”会进入 NotFound，属于真实用户路径断裂。  
**建议修复：** 新增 `/admin/review` 子路由并接入已有 Review 页面或移除导航项；新增 e2e 遍历所有 admin nav links，断言不落入 NotFound。

---

### H2 · React Admin 登录仍是前端 mock，未接 `/api/auth/login`

**证据：**

`apps/web/src/pages/admin/LoginPage.tsx` 只校验固定验证码 `123456`，直接写 user store：

  - L53: `  const onSubmit = async (values: LoginFormValues): Promise<void> => {`
  - L54: `    setSubmitError(null);`
  - L55: `    await new Promise((resolve) => window.setTimeout(resolve, 80));`
  - L56: ``
  - L57: `    if (values.code !== '123456') {`
  - L58: `      setSubmitError(intl.formatMessage({ id: 'admin.login.mockCodeError' }));`
  - L59: `      return;`
  - L60: `    }`
  - L61: ``
  - L62: `    setUser({`
  - L63: `      id: `admin-${values.phone.slice(-4)}`,`
  - L64: `      name: intl.formatMessage({ id: 'admin.login.mockAdminName' }, { suffix: values.phone.slice(-4) }),`
  - L65: `      phone: values.phone,`
  - L66: `      role: 'admin',`
  - L67: `    });`
  - L68: `    toast.success(intl.formatMessage({ id: 'admin.login.toastSuccess' }), {`
  - L69: `      description: intl.formatMessage({ id: 'admin.login.toastSuccessDescription' }),`
  - L70: `    });`
  - L71: `    void navigate(from, { replace: true });`
  - L72: `  };`
  - L102: `              <h2 className="text-2xl font-bold text-slate-950 dark:text-white">`
  - L103: `                <FormattedMessage id="admin.login.title" />`
  - L104: `              </h2>`
  - L105: `              <p className="text-sm text-slate-500 dark:text-slate-400">`
  - L106: `                <FormattedMessage id="admin.login.mockHint" />`
  - L107: `              </p>`
  - L132: `              <div className="relative mt-2">`
  - L133: `                <LockKeyhole className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />`
  - L134: `                <input`
  - L135: `                  id="admin-code"`
  - L136: `                  type="text"`
  - L137: `                  inputMode="numeric"`
  - L138: `                  autoComplete="one-time-code"`
  - L139: `                  placeholder="123456"`
  - L140: `                  className="min-h-12 w-full rounded-2xl border border-slate-200 bg-white px-11 text-sm text-slate-950 shadow-sm transition placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white"`

后端真实登录端点存在：`admin/routes/auth.py` 声明 `POST /api/auth/login : 用户名 + 密码 → JWT`，但 React 登录页没有调用该端点。

**影响：** 真实后端环境会出现“前端显示已登录，但后续 admin API 请求没有 JWT，返回 401/403”的集成失败。  
**建议修复：** 登录页改为调用 `/api/auth/login`；保存 JWT 到明确策略（优先内存/session，避免长期 localStorage）；失败态显示真实错误；补 `LoginPage` 集成测试和 admin e2e 登录主链路。

---

### H3 · `apiClient` 没有统一注入 `Authorization: Bearer`，Admin API 契约未闭环

**证据：**

`apps/web/src/lib/api-client.ts` 只设置 Content-Type / Accept 和调用方传入 headers，没有从 auth/user store 注入 Bearer：

  - L101: `  const init: RequestInit = {`
  - L102: `    method,`
  - L103: `    headers: {`
  - L104: `      'Content-Type': 'application/json',`
  - L105: `      Accept: 'application/json',`
  - L106: `      ...headers,`
  - L107: `    },`
  - L108: `    signal,`
  - L109: `  };`
  - L110: ``
  - L111: `  if (body !== undefined) {`
  - L112: `    init.body = JSON.stringify(body);`
  - L113: `  }`
  - L114: ``
  - L115: `  if (isWriteMethod(method)) {`
  - L116: `    await waitUntilOnline(signal);`
  - L117: `  }`
  - L118: ``
  - L119: `  const res = await fetch(`${BASE_URL}${path}`, init);`
  - L120: ``
  - L155: `export const apiClient = {`
  - L156: `  get: <T>(path: string, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>`
  - L157: `    request(path, schema, { method: 'GET', signal }),`
  - L158: `  post: <T, B = unknown>(path: string, body: B, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>`
  - L159: `    request(path, schema, { method: 'POST', body, signal }),`
  - L160: `  put: <T, B = unknown>(path: string, body: B, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>`
  - L161: `    request(path, schema, { method: 'PUT', body, signal }),`
  - L162: `  patch: <T, B = unknown>(path: string, body: B, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>`
  - L163: `    request(path, schema, { method: 'PATCH', body, signal }),`
  - L164: `  delete: <T>(path: string, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>`
  - L165: `    request(path, schema, { method: 'DELETE', signal }),`
  - L166: `};`

后端 `admin/auth.py` 依赖 `Authorization: Bearer`，还支持 URL query `t=` fallback：

  - L115: `    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_BEARER_SCHEME),`
  - L116: `    settings: Settings = Depends(get_settings),`
  - L117: `) -> AdminUser:`
  - L118: `    """FastAPI 依赖:从 Authorization: Bearer *** JWT,返回 AdminUser。`
  - L119: ``
  - L120: `    缺失/无效/过期一律 401 (走业务错误码 E012xx 系列).`
  - L121: `    支持从 URL query 参数 ``t`` 获取 token（仅用于管理后台 Web 页面场景）。`
  - L122: `    """`
  - L123: `    raw_token: str | None = None`
  - L124: `    if credentials is not None and credentials.scheme.lower() == "bearer":`
  - L125: `        raw_token = credentials.credentials`
  - L126: `    # fallback: URL query 参数 t（管理后台 Web 登录页跳转场景）`
  - L127: `    if raw_token is None:`
  - L128: `        query_token = request.query_params.get("t")`
  - L129: `        if query_token:`
  - L130: `            raw_token = query_token`
  - L131: `    if raw_token is None:`
  - L132: `        raise BusinessError(`
  - L133: `            AUTH_TOKEN_INVALID, detail={"reason": "missing bearer token"}`

**影响：** 即使 H2 修复了登录，如果 apiClient 不统一注入 token，后台订单/案例/分享等受保护 API 仍会失败；若继续依赖 URL `?t=`，token 容易进入浏览器历史、日志或 Referer。  
**建议修复：** 建立 `authStore` / token provider，apiClient 统一注入 Authorization；逐步减少 URL token fallback 的使用范围，仅保留后台 Web 兼容场景并加安全注释和测试。

---

### H4 · Python 总门禁 mypy 当前失败，不能宣称后端质量门禁通过

**证据：** `scripts/dev-verify.sh` 会运行 `python -m mypy .`：

  - L87: `  log "running pytest with coverage gate"`
  - L88: `  # Single source of truth threshold: matches scripts/check_coverage_gate.py`
  - L89: `  if [[ "${SKIP_PRE_EXISTING}" == "1" ]]; then`
  - L90: `    log "skip pre-existing failures: --skip-pre-existing"`
  - L91: `    for node in "${PRE_EXISTING_IGNORES[@]}"; do`
  - L92: `      PYTEST_IGNORE_ARGS+=("--deselect" "$node")`
  - L93: `    done`
  - L94: `  fi`
  - L95: `  python -m pytest admin/tests tests data \`
  - L96: `    --ignore=.venv \`
  - L97: `    --ignore=.worktrees \`
  - L98: `    --cov=admin \`
  - L99: `    --cov=data \`
  - L100: `    --cov=skills \`
  - L101: `    --cov-report=term-missing \`
  - L102: `    --cov-report=xml \`
  - L103: `    --cov-fail-under=80 \`
  - L104: `    -q \`
  - L105: `    "${PYTEST_IGNORE_ARGS[@]}"`
  - L106: ``
  - L107: `  log "running core coverage verifier"`
  - L108: `  python scripts/check_coverage_gate.py coverage.xml`
  - L109: ``
  - L110: `  log "running ruff"`
  - L111: `  python -m ruff check . --exclude .venv,.worktrees`
  - L112: ``
  - L113: `  log "running mypy"`
  - L114: `  python -m mypy .`
  - L115: ``
  - L116: `  log "crowd_db quality summary (防漂移监控)"`
  - L117: `  python -m data.crowd_db.quality_summary --human`
  - L118: ``
  - L119: `  # P1-7/P1-8: 100-case smoke 作为独立验证步骤，失败不阻断核心门禁`
  - L120: `  log "running 100-case smoke e2e (non-blocking)"`
  - L121: `  python scripts/score_range_fullchain_100_e2e.py --batch smoke || log "WARN: 100-case smoke e2e failed (non-blocking, see /tmp/score-range-fullchain-100-e2e.log)"`

本轮执行结果显示 mypy 有 9 个错误，涉及 `data/share/poster.py` 等文件：

```text
admin/routes/sprint3_api.py:292: error: Incompatible types in assignment (expression has type "str", variable has type "Literal['pending', 'in_progress', 'approved', 'rejected', 'changes_requested']")  [assignment]
data/cli_compat_share.py:43: error: Item "None" of "_ArgumentGroup | None" has no attribute "_group_actions"  [union-attr]
data/cli_compat_share.py:44: error: Item "Action" of "Action | Any" has no attribute "add_parser"  [union-attr]
data/share/poster.py:123: error: Argument "candidate_name" to "PosterPayload" has incompatible type "str | None"; expected "str"  [arg-type]
data/share/poster.py:273: error: Incompatible return value type (got "FreeTypeFont", expected "ImageFont")  [return-value]
data/share/poster.py:274: error: Incompatible return value type (got "FreeTypeFont | ImageFont", expected "ImageFont")  [return-value]
data/share/poster.py:319: error: Incompatible return value type (got "float", expected "int")  [return-value]
data/share/poster.py:324: error: Incompatible return value type (got "float", expected "int")  [return-value]
data/share/poster.py:329: error: Library stubs not installed for "qrcode"  [import-untyped]
Found 9 errors in 3 files (checked 268 source files)
DEV_VERIFY_EXIT=1
```

**影响：** 类型门禁失败会影响 poster/share 相关链路长期可维护性，也说明 CI clean env 可能无法稳定通过。  
**建议修复：** 修 `data/share/poster.py` 返回类型；安装/声明 `types-qrcode` 或在 mypy 配置中有边界地忽略；修后复跑 `bash scripts/dev-verify.sh`。

---

---

## 3. MEDIUM Findings

### M0 · 前端本地门禁曾因依赖缺失不可执行；已补装依赖并 fresh gate 通过，但应沉淀环境准备要求

**证据：** 首轮 `/tmp/gaokao-review-gates-20260705.log` 显示 `apps/web/node_modules missing`、`turbo: not found`；补执行 `/tmp/gaokao-frontend-gates-20260705.log` 后，前端 gate 结果为 **PASS**。

```text
=== FRONTEND FRESH GATES START ===
--- pnpm install ---
root node_modules exists
apps/web/node_modules exists
--- web typecheck ---
--- web lint ---
--- web test ---
--- web build ---
 Tasks:    2 successful, 2 total
 Tasks:    1 successful, 1 total
@gaokao/web:build: TOTAL                               │    1.36 MB │  393.60 KB │ ✅
@gaokao/web:build: ✅ T-B-25 验证通过
=== FRONTEND FRESH GATES END ===
```

**影响：** 该问题当前不再是代码质量 blocker，但说明本地 review/交接流程需要先执行依赖安装，否则容易把“环境未准备”误报为“前端 gate 失败”。  
**建议修复：** 在 review runbook / README 的前端 gate 前置条件中加入 `pnpm install --frozen-lockfile`，并在 CI/本地脚本中显式检查 `turbo` 可用后再运行 gate。

---

## 3. MEDIUM Findings

### M1 · Chromatic job 无 token 条件保护，可能阻断 CI

**证据：** `.github/workflows/web-ci.yml` 直接使用 secret：

  - L96: `  chromatic:`
  - L97: `    runs-on: ubuntu-latest`
  - L98: `    needs: ci`
  - L99: `    timeout-minutes: 15`
  - L100: `    if: github.event_name == 'push' || github.event_name == 'pull_request'`
  - L101: `    steps:`
  - L102: `      - uses: actions/checkout@v4`
  - L103: `        with:`
  - L104: `          fetch-depth: 0`
  - L105: ``

**影响：** 未配置 `CHROMATIC_TOKEN` 时，push/PR 可能被 Chromatic 阻断；这与“外部 token 待配置”的状态口径不一致。  
**建议修复：** 给 chromatic job 增加 secret 存在性条件或降级为非阻塞；在报告中明确 Chromatic 是否为 release blocker。

---

### M2 · LHCI 配置与启动口径仍有漂移风险

**证据：** workflow 使用 treosh action + `serverUrl: 8080`，而 lighthouserc 注释仍写“vite preview 启动（8081）”：

`.github/workflows/web-ci.yml`：

  - L106: `      - name: Setup pnpm`
  - L107: `        uses: pnpm/action-setup@v4`
  - L108: `        with:`
  - L109: `          version: 10`
  - L110: ``
  - L111: `      - name: Setup Node.js`
  - L112: `        uses: actions/setup-node@v4`
  - L113: `        with:`
  - L114: `          node-version: '20'`
  - L115: `          cache: 'pnpm'`
  - L116: ``
  - L117: `      - name: Install dependencies`
  - L118: `        run: pnpm install --frozen-lockfile`
  - L119: ``
  - L120: `      - name: Build`
  - L121: `        run: pnpm --filter @gaokao/web build`
  - L122: ``
  - L123: `      - name: Publish to Chromatic`
  - L124: `        uses: chromaui/action@v1`
  - L125: `        with:`
  - L126: `          projectToken: ${{ secrets.CHROMATIC_TOKEN }}`
  - L127: `          workingDir: apps/web`
  - L128: `          buildScriptName: build`
  - L129: `          exitZeroOnChanges: true`
  - L130: ``
  - L131: `  lighthouse:`
  - L132: `    # G3 闸门真实化：P/A/B/S 均 ≥ 90`
  - L133: `    runs-on: ubuntu-latest`
  - L134: `    needs: ci`
  - L135: `    timeout-minutes: 15`
  - L136: `    if: github.event_name == 'push' || github.event_name == 'pull_request'`
  - L137: `    steps:`
  - L138: `      - uses: actions/checkout@v4`
  - L139: ``
  - L140: `      - name: Setup pnpm`
  - L141: `        uses: pnpm/action-setup@v4`
  - L142: ``
  - L143: `      - name: Setup Node.js`
  - L144: `        uses: actions/setup-node@v4`
  - L145: `        with:`
  - L146: `          node-version: '20'`
  - L147: `          cache: 'pnpm'`
  - L148: ``
  - L149: `      - name: Install dependencies`
  - L150: `        run: pnpm install --frozen-lockfile`
  - L151: ``
  - L152: `      - name: Build`
  - L153: `        run: pnpm --filter @gaokao/web build`
  - L154: ``
  - L155: `      - name: Run Lighthouse CI (G3 闸门：P/A/B/S ≥ 90)`
  - L156: `        uses: treosh/lighthouse-ci-action@v12`
  - L157: `        with:`
  - L158: `          configPath: ./apps/web/lighthouserc.cjs`
  - L159: `          uploadArtifacts: true`
  - L160: `          temporaryPublicStorage: true`
  - L161: `          runs: 3`
  - L162: `          serverUrl: http://127.0.0.1:8080/`
  - L163: `          # treosh action 自动启动 vite preview @ 8080`
  - L164: `          url: |`
  - L165: `            http://127.0.0.1:8080/`
  - L166: `            http://127.0.0.1:8080/data-query`
  - L167: `            http://127.0.0.1:8080/plans`
  - L168: `            http://127.0.0.1:8080/about`

`apps/web/lighthouserc.cjs`：

  - L14: `    collect: {`
  - L15: `      // 静态服务器从 vite preview 启动（8081），见 CI workflow`
  - L16: `      url: [`
  - L17: `        'http://127.0.0.1:8080/',`
  - L18: `        'http://127.0.0.1:8080/data-query',`
  - L19: `        'http://127.0.0.1:8080/plans',`
  - L20: `        'http://127.0.0.1:8080/about',`
  - L21: `      ],`
  - L22: `      numberOfRuns: 3, // 取 P75（median）`
  - L23: `      settings: {`
  - L24: `        // P75 算分（默认 median = P50）`
  - L25: `        preset: 'desktop',`
  - L26: `        chromeFlags: '--no-sandbox --headless=new',`
  - L27: `      },`
  - L29: `    assert: {`
  - L30: `      // G3 闸门：每类 ≥ 90`
  - L31: `      assertions: {`
  - L32: `        'categories:performance': ['error', { minScore: 0.9 }],`
  - L33: `        'categories:accessibility': ['error', { minScore: 0.9 }],`
  - L34: `        'categories:best-practices': ['error', { minScore: 0.9 }],`
  - L35: `        'categories:seo': ['error', { minScore: 0.9 }],`
  - L36: `      },`
  - L37: `    },`
  - L38: `    upload: {`
  - L39: `      target: 'temporary-public-storage', // 公开 storage 30 天；后续接 LHCI server`
  - L40: `    },`

**影响：** LHCI 可能在 CI 上因为服务启动机制/端口口径不一致而假失败或假通过。  
**建议修复：** 在 LHCI 配置或 workflow 中显式指定 preview 启动命令、ready pattern、端口；修正文档注释；CI 上保留 artifact。

---

### M3 · `scripts/dev-verify.sh` 将 100-case smoke 设为 non-blocking，主链路回归可能被 warning 化

**证据：**

  - L87: `  log "running pytest with coverage gate"`
  - L88: `  # Single source of truth threshold: matches scripts/check_coverage_gate.py`
  - L89: `  if [[ "${SKIP_PRE_EXISTING}" == "1" ]]; then`
  - L90: `    log "skip pre-existing failures: --skip-pre-existing"`
  - L91: `    for node in "${PRE_EXISTING_IGNORES[@]}"; do`
  - L92: `      PYTEST_IGNORE_ARGS+=("--deselect" "$node")`
  - L93: `    done`
  - L94: `  fi`
  - L95: `  python -m pytest admin/tests tests data \`
  - L96: `    --ignore=.venv \`
  - L97: `    --ignore=.worktrees \`
  - L98: `    --cov=admin \`
  - L99: `    --cov=data \`
  - L100: `    --cov=skills \`
  - L101: `    --cov-report=term-missing \`
  - L102: `    --cov-report=xml \`
  - L103: `    --cov-fail-under=80 \`
  - L104: `    -q \`
  - L105: `    "${PYTEST_IGNORE_ARGS[@]}"`
  - L106: ``
  - L107: `  log "running core coverage verifier"`
  - L108: `  python scripts/check_coverage_gate.py coverage.xml`
  - L109: ``
  - L110: `  log "running ruff"`
  - L111: `  python -m ruff check . --exclude .venv,.worktrees`
  - L112: ``
  - L113: `  log "running mypy"`
  - L114: `  python -m mypy .`
  - L115: ``
  - L116: `  log "crowd_db quality summary (防漂移监控)"`
  - L117: `  python -m data.crowd_db.quality_summary --human`
  - L118: ``
  - L119: `  # P1-7/P1-8: 100-case smoke 作为独立验证步骤，失败不阻断核心门禁`
  - L120: `  log "running 100-case smoke e2e (non-blocking)"`
  - L121: `  python scripts/score_range_fullchain_100_e2e.py --batch smoke || log "WARN: 100-case smoke e2e failed (non-blocking, see /tmp/score-range-fullchain-100-e2e.log)"`

第 119-121 行说明 100-case smoke 失败不阻断核心门禁。

**影响：** 对当前高信任付费/志愿服务项目，100-case fullchain smoke 更接近业务真实回归；长期 non-blocking 可能掩盖主链路问题。  
**建议修复：** 至少把 smoke 结果拆为 `核心门禁 PASS/FAIL` 与 `业务主链路 PASS/FAIL` 两个明确状态；在 release gate 中设置必过子集。

---

## 4. LOW / 文档真相风险

### L1 · 历史 review 与当前 review 容易混用

仓库内存在多个历史 review：`reports/REVIEW_REPORT_V10_FRONTEND_2026-07-05.md`、`REVIEW_REPORT_2026-07-02_SENIOR_DEVELOPER.md`、`STRICT_SYSTEM_REVIEW_*` 等。历史报告仍有价值，但不应替代当前 HEAD + 当前门禁结果。

**建议：** 将本报告作为 2026-07-05 当前全面 review 真相入口；旧报告顶部应逐步加“历史快照”提示或 CURRENT REVIEW 指针。

### L2 · 旧截图报告产物仍在仓库中，易被误当当前前端验收材料

`reports/user_simulation_2026_06_20/` 仍包含旧截图和 captures.json。上一轮已避免把这些旧产物合并进新提交；本轮 review 继续建议把它们标注为历史材料，不作为 V10 当前验收证据。

---

## 5. 已验证不是问题 / 当前正向事实

- `apps/web/src/types/api-generated.d.ts` 与 `apps/web/src/schemas/api-generated.ts` 的 `any_count=0`：

```text
apps/web/src/types/api-generated.d.ts 0
apps/web/src/schemas/api-generated.ts 0
```

- `admin/routes/health.py` 当前 dev readiness 逻辑可解释：

  - L65: `def _check_settings_valid(settings: Settings) -> bool:`
  - L66: `    """检查 prod fail-closed 通过 (JWT + admin password + payment)。`
  - L67: ``
  - L68: `    dev 环境允许占位密钥，仅 prod 环境强制安全密钥。`
  - L69: `    """`
  - L70: `    if settings.env == "dev":`
  - L71: `        # dev 环境允许占位密钥，不做 fail-closed`
  - L72: `        return True`
  - L73: `    secure, _ = is_jwt_secret_secure(settings)`
  - L74: `    return secure`
  - L75: ``
  - L76: ``
  - L77: `@router.get("/health", summary="健康检查")`
  - L78: `def health(settings: Settings = Depends(get_settings_dep)) -> JSONResponse:`
  - L79: `    """公开端点。只返回 readiness, 不暴露环境/路径/版本细节。`
  - L80: ``
  - L81: `    返回结构:`
  - L82: `    - status: "ok" 或 "degraded"（任一 readiness 检查失败时降级）`
  - L83: `    - checks: {db_writable, disk_writable, settings_valid} 子对象`
  - L84: ``
  - L85: `    readiness 语义（2026-06-27 P1-4 修复）:`
  - L86: `    - 所有 checks 通过 → status="ok", HTTP 200`
  - L87: `    - 任一 check 失败 → status="degraded", HTTP 503`
  - L88: `    - K8s/systemd readiness probe 应判 HTTP status，不只判 status 字段`
  - L89: `    """`
  - L90: `    checks = {`
  - L91: `        "db_writable": _check_db_writable(settings),`
  - L92: `        "disk_writable": _check_disk_writable(settings),`
  - L93: `        "settings_valid": _check_settings_valid(settings),`
  - L94: `    }`
  - L95: `    all_ok = all(checks.values())`
  - L96: `    return JSONResponse(`
  - L97: `        status_code=200 if all_ok else 503,`
  - L98: `        content={`
  - L99: `            "status": "ok" if all_ok else "degraded",`
  - L100: `            "checks": checks,`
  - L101: `        },`

- 静态扫描未发现 Python 裸 `except:`。

---

## 6. 建议整改优先级

### P0 / 立即阻断生产完成声明

1. 修复 H1 `/admin/review` 断链并补全 admin nav e2e。
2. 修复 H2/H3：React Admin 真实登录 + JWT 注入 + auth 状态测试。
3. 修复 H4：mypy 9 errors，复跑 `scripts/dev-verify.sh` 到 green。
4. 前端依赖已补装并复跑 typecheck/lint/test/build；后续仍需补 Playwright e2e / LHCI / Chromatic fresh evidence。

### P1 / CI 与验收口径收敛

1. Chromatic token 缺失时不阻断或明确设为必配 release gate。
2. LHCI preview 启动和端口口径统一。
3. 100-case smoke 的 release gate 语义升级，不再只作为 warning。

### P2 / 文档与证据治理

1. 给历史 review 报告加当前真相入口。
2. 标注旧截图/旧 user simulation 产物为历史材料。

---

## 7. 本轮命令与证据索引

```text
## main
4059f144c49398aec2fcc3040e639e1312061086
4059f14 (HEAD -> main, tksea/main, origin/main, gitea/main) fix(health): allow dev placeholder readiness
da99dec docs: add systemic frontend review findings
5d52e07 docs: update frontend review status after e2e fixes
```

本轮主要证据：

- 本地 gate 日志：`/tmp/gaokao-review-gates-20260705.log`
- 当前报告：`reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md`
- 核查文件：
  - `apps/web/src/layouts/AdminLayout.tsx`
  - `apps/web/src/router.tsx`
  - `apps/web/src/pages/admin/LoginPage.tsx`
  - `apps/web/src/lib/api-client.ts`
  - `.github/workflows/web-ci.yml`
  - `apps/web/lighthouserc.cjs`
  - `scripts/dev-verify.sh`
  - `admin/routes/health.py`
  - `admin/auth.py`

---

## 8. 最终判断

**不能宣称项目整体生产级完成。**

可以宣称：

- 本轮已完成一次当前 HEAD 的多维真实 review。
- 已发现并固化当前有效问题到今日 review 报告。
- 当前最大阻断不是“未知”，而是明确集中在：后台真实鉴权闭环、admin nav 路由完整性、Python 类型门禁、Playwright/LHCI/Chromatic 与真实视觉验收 fresh evidence、CI 外部服务口径。

仍不能宣称：

- 前端 V10 全部门禁（含 Playwright e2e / LHCI / Chromatic / 真实视觉验收）当前全部通过。
- Admin 真实 JWT 登录已接通。
- CI/LHCI/Chromatic 生产级验收闭环。
- 线上真实支付/真实域名/真实用户流量验收完成。
