# 2026-07-07 Review Remediation Plan Audit

> 审查对象：`docs/plans/2026-07-07-review-remediation-execution-plan.md`  
> 对照真相源：`reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md`  
> 生成时间：2026-07-07T12:34:18  
> 专业角色：Tech Lead + QA Manager + Security Engineer + Frontend Reviewer + Release Manager

---

## 0. Gate Verdict

**结论：CONDITIONAL / v1 方向正确，但不能保证完全修复 review 报告所有问题；必须升级为 v2 后再执行。**

v1 的优点：
- 已覆盖主要 P0 gate：mypy、i18n、poster/share E2E、truth source sync。
- 有阶段依赖、文件路径、验证命令和提交策略。
- 能作为修复入口，但不是完整闭环计划。

v1 的关键缺口：
- 把 M3/M8/M9/L2 放到 “Phase 5+ 后续”，与用户要求“完全修复 review 报告的所有问题”冲突。
- T3 的 E2E mock 修复依赖 Playwright route 顺序假设，缺少明确排除 fallback 的强契约。
- T4 对 innerHTML / SQL/subprocess 只做“审计”，没有把需修复项转成代码级任务。
- T5 缺少 CI/readback、Chromatic/LHCI 语义、真实后端 E2E 的完整收口策略。
- 若直接按 v1 执行，可能得到“局部门禁全绿”，但仍不能证明 review 报告所有问题被修复。

---

## 1. 覆盖矩阵

| Review finding | v1 覆盖 | 评审结论 | 必须优化 |
|---|---:|---|---|
| H1/H6 truth drift | ✅ | 基本覆盖 | 加 regression 检查，防止文档再次写“Phase 0~5 全部完成” |
| H2 mypy 3 errors | ✅ | 覆盖 | 增加全量 `scripts/dev-verify.sh` 为 Phase 1 exit，而非只跑 mypy |
| H3 Dashboard i18n | ✅ | 覆盖但实现建议需修正 | 不建议直接读 `intl.messages[key]`；用显式 `statusMessageIds` + `intl.formatMessage` 更稳 |
| H4/H7 poster/share E2E | ⚠️ | 部分覆盖 | 必须显式 mock `/api/plans`、排除 fallback 覆盖，并验证按钮 enabled 状态 |
| H5/H8 README secret | ✅ | 覆盖 | 增加实际启动 smoke，验证 `/health.settings_valid=true` |
| H9 CSV injection | ⚠️ | 部分覆盖 | admin 已有 `_csv_safe_value` 和测试；重点补 `data/orders/cli.py`，并统一 helper 或测试覆盖 |
| H10 mock vs real-backend E2E | ⚠️ | 较弱 | 仅加 script 不够；必须补 real-backend smoke spec / 脚本，且区分 mock/real 输出 |
| M1 Playwright browser missing | ✅ | 覆盖 | 补 CI/browser cache/readiness 检查 |
| M3 `web_public.py` 300KB | ❌ | v1 延后，不满足“完全修复” | 新增结构治理 Phase：拆分或至少完成一个低风险模块迁移 |
| M4/M6 invalid escape | ✅ | 覆盖 | 需先 `grep -n '\\s'` 精确定位，并用 warning-as-error 验证 |
| M5 compose mock default | ✅ | 覆盖 | 增加 `docker compose -f docker-compose.yml -f docker-compose.prod.yml config` 验证 |
| M7 SQL/subprocess/innerHTML | ⚠️ | 只审计不修复 | 至少 innerHTML 用户可控拼接必须转成 DOM/textContent 或 escape helper，并补测试 |
| M8 contract quartet | ❌ | v1 延后，不满足完整修复 | 新增 contract matrix artifact + 自动检查脚本 |
| M9 domain data vs LLM prompt | ❌ | v1 延后，不满足完整修复 | 新增数据/规则/prompt 覆盖 gate |
| L1 WAL/SHM | ✅ | 覆盖 | 增加 `git status --short` 作为提交前 gate |
| L2 old artifacts/worktrees noise | ❌ | v1 延后，不满足完整修复 | 新增归档/ignore/报告入口策略 |

---

## 2. Grounded Findings

### F1 · T3 poster/share E2E 修复必须明确 API shape 与 fallback 排除

`PosterPreviewPage` 当前通过 `usePlansQuery()` 读取 `plansQuery.data?.plans[0]?.id`；v1 给 `/api/plans` 返回 `plans` 数组方向正确，但还必须核对 hook/schema 接受的完整 shape，并在 fallback route 中显式排除 `/api/plans`，不要依赖 Playwright 多 handler 顺序。

证据摘录：

```text
/**
 * V10 option B · usePlanQueries.
 * Replaces the legacy usePlan prototype.
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { PlanListResponseSchema, type PlanListResponse, PlanSchema, type Plan } from '@/lib/api-schemas';

export const planKeys = {
  all: ['plans'] as const,
  list: () => [...planKeys.all, 'list'] as const,
  detail: (id: string) => [...planKeys.all, 'detail', id] as const,
};

export function usePlansQuery() {
  return useQuery<PlanListResponse, Error>({
    queryKey: planKeys.list(),
    queryFn: ({ signal }) => apiClient.get<PlanListResponse>('/plans', PlanListResponseSchema, signal),
    staleTime: 60 * 1000,
  });
}

export function usePlanQuery(id: string | null) {
  return useQuery<Plan, Error>({
    queryKey: id ? planKeys.detail(id) : ['plans', 'detail', 'noop'],
    queryFn: ({ signal }) => apiClient.get<Plan>(`/plans/${id}`, PlanSchema, signal),
    enabled: Boolean(id),
    staleTime: 5 * 60 * 1000,
  });
}
apps/web/src/lib/query-client.test.ts:46:      [planKeys.list(), { plans: [{ id: 'plan-1', title: '广东物理方案' }], total: 1 }],
apps/web/src/lib/api-schemas.ts:68:export const PlanListResponseSchema = z.object({
apps/web/src/lib/api-schemas.ts:69:  plans: z.array(PlanSchema),
apps/web/src/lib/api-schemas.ts:72:export type PlanListResponse = z.infer<typeof PlanListResponseSchema>;
apps/web/src/hooks/usePlanQueries.ts:7:import { PlanListResponseSchema, type PlanListResponse, PlanSchema, type Plan } from '@/lib/api-schemas';
apps/web/src/hooks/usePlanQueries.ts:16:  return useQuery<PlanListResponse, Error>({
apps/web/src/hooks/usePlanQueries.ts:18:    queryFn: ({ signal }) => apiClient.get<PlanListResponse>('/plans', PlanListResponseSchema, signal),
```

建议 v2 改法：
- 新增 E2E helper `mockPlans(page)`，放到 `apps/web/e2e/helpers/mock-api.ts`。
- fallback predicate 显式排除 `/api/plans`、`/api/share-link/latest`、`/api/share-link`、`/api/poster/generate`。
- 点击前增加断言：`await expect(page.getByRole('button', { name: /生成海报/ })).toBeEnabled()`。

### F2 · Share E2E 修复必须确认 `latest.data?.planId` schema

v1 指出 `/api/share-link/latest` 返回 `null` 导致 `selectedPlanId=''` 是正确根因，但 mock 对象必须与 hook/schema 匹配，否则会变成 Zod 校验失败或数据被丢弃。

证据摘录：

```text
apps/web/src/hooks/useAdminShareLinks.ts:5:export type AdminShareLinkStatus = 'active' | 'revoked' | 'expired';
apps/web/src/hooks/useAdminShareLinks.ts:6:export type AdminShareLinkResultType = 'review_result' | 'report';
apps/web/src/hooks/useAdminShareLinks.ts:8:export const AdminShareLinkSchema = z
apps/web/src/hooks/useAdminShareLinks.ts:34:    const status: AdminShareLinkStatus = revoked ? 'revoked' : isExpired ? 'expired' : 'active';
apps/web/src/hooks/useAdminShareLinks.ts:52:export const AdminShareLinksResponseSchema = z
apps/web/src/hooks/useAdminShareLinks.ts:57:    items: z.array(AdminShareLinkSchema),
apps/web/src/hooks/useAdminShareLinks.ts:59:  .or(z.array(AdminShareLinkSchema).transform((items) => ({ total: items.length, limit: items.length || 1, offset: 0, items })));
apps/web/src/hooks/useAdminShareLinks.ts:61:export const AdminShareLinkStatsSchema = z
apps/web/src/hooks/useAdminShareLinks.ts:76:export const AdminShareLinkTrendPointSchema = z
apps/web/src/hooks/useAdminShareLinks.ts:82:export const AdminShareLinkAuditLogSchema = z
apps/web/src/hooks/useAdminShareLinks.ts:99:export const AdminShareLinkDetailSchema = z.object({
apps/web/src/hooks/useAdminShareLinks.ts:100:  link: AdminShareLinkSchema,
apps/web/src/hooks/useAdminShareLinks.ts:101:  stats: AdminShareLinkStatsSchema,
apps/web/src/hooks/useAdminShareLinks.ts:102:  trend: z.array(AdminShareLinkTrendPointSchema),
apps/web/src/hooks/useAdminShareLinks.ts:103:  auditLogs: z.array(AdminShareLinkAuditLogSchema).optional(),
apps/web/src/hooks/useAdminShareLinks.ts:104:  audit_logs: z.array(AdminShareLinkAuditLogSchema).optional(),
apps/web/src/hooks/useAdminShareLinks.ts:112:export type AdminShareLink = z.infer<typeof AdminShareLinkSchema>;
apps/web/src/hooks/useAdminShareLinks.ts:113:export type AdminShareLinksResponse = z.infer<typeof AdminShareLinksResponseSchema>;
apps/web/src/hooks/useAdminShareLinks.ts:114:export type AdminShareLinkStats = z.infer<typeof AdminShareLinkStatsSchema>;
apps/web/src/hooks/useAdminShareLinks.ts:115:export type AdminShareLinkTrendPoint = z.infer<typeof AdminShareLinkTrendPointSchema>;
apps/web/src/hooks/useAdminShareLinks.ts:116:export type AdminShareLinkAuditLog = z.infer<typeof AdminShareLinkAuditLogSchema>;
apps/web/src/hooks/useAdminShareLinks.ts:117:export type AdminShareLinkDetail = z.infer<typeof AdminShareLinkDetailSchema>;
apps/web/src/hooks/useAdminShareLinks.ts:119:export interface AdminShareLinksParams {
apps/web/src/hooks/useAdminShareLinks.ts:122:  status?: AdminShareLinkStatus;
apps/web/src/hooks/useAdminShareLinks.ts:123:  resultType?: AdminShareLinkResultType;
apps/web/src/hooks/useAdminShareLinks.ts:126:export const adminShareLinkKeys = {
apps/web/src/hooks/useAdminShareLinks.ts:128:  list: (params: AdminShareLinksParams) => [...adminShareLinkKeys.all, 'list', params] as const,
apps/web/src/hooks/useAdminShareLinks.ts:129:  detail: (code: string) => [...adminShareLinkKeys.all, 'detail', code] as const,
apps/web/src/hooks/useAdminShareLinks.ts:132:function toQueryString(params: AdminShareLinksParams): string {
apps/web/src/hooks/useAdminShareLinks.ts:144:export function useAdminShareLinksQuery(params: AdminShareLinksParams) {
apps/web/src/hooks/useAdminShareLinks.ts:145:  return useQuery<AdminShareLinksResponse>({
apps/web/src/hooks/useAdminShareLinks.ts:146:    queryKey: adminShareLinkKeys.list(params),
apps/web/src/hooks/useAdminShareLinks.ts:147:    queryFn: () => apiClient.get<AdminShareLinksResponse>(`/admin/sha
```

建议 v2 改法：
- 用 `useShareLinkLatestQuery` / schema 实际字段作为 mock 真相。
- 点击前增加：`await expect(page.getByRole('button', { name: '创建分享链接（30天有效）' })).toBeEnabled()`。

### F3 · M7 不能只“白名单审计”，innerHTML 命中项必须有代码级收口

Review 报告已把 innerHTML / subprocess / SQL 动态 execute 列为安全审计项。v1 只创建 `docs/SECURITY_AUDIT_2026-07-07.md`，没有要求对 `web_public.py` 命中项做代码级判断和测试。

证据摘录：

```text
toast.className = 'state-toast state-toast--' + (type || 'info');
  toast.textContent = msg;
  stack.appendChild(toast);
  requestAnimationFrame(function() { toast.classList.add('state-toast--visible'); });
  setTimeout(function() {
    toast.classList.remove('state-toast--visible');
    setTimeout(function() { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
  }, 3000);
};
window.showLoading = function(container, msg) {
  if (!container) return null;
  var el = document.createElement('div');
  el.className = 'state-loading';
  el.innerHTML = '<div class="state-loading__spinner"></div><p class="state-loading__text">' + (msg || '加载中…') + '</p>';
  container.appendChild(el);
  return el;
};
window.hideLoading = function(el) {
  if (el && el.parentNode) el.parentNode.removeChild(el);
};
</script>"""


---
              showFieldError(goal, validateGoal());
              // 全局提示
              var globalHint = document.getElementById('consult-error-hint');
              if (!globalHint) {{
                globalHint = document.createElement('div');
                globalHint.id = 'consult-error-hint';
                globalHint.className = 'field-error-hint';
                globalHint.setAttribute('role', 'alert');
                form.appendChild(globalHint);
              }}
              if (allErrs.length) {{
                globalHint.innerHTML = allErrs.join('；');
                globalHint.style.display = 'block';
              }} else {{
                globalHint.style.display = 'none';
              }}
              return allErrs.length === 0;
            }}

            form.addEventListener('submit', function(e) {{
              if (!validateAll()) e.preventDefault();
```

建议 v2 改法：
- `globalHint.innerHTML = allErrs.join('；')` 如果 `allErrs` 来自受控错误文本，需在审计文档证明；否则改为 `textContent`。
- `el.innerHTML = ... + msg + ...` 必须确认 `msg` 是否只来自常量；若可变，改 DOM 构造或 escape helper。
- 加 TestClient/HTML 静态测试：页面中不能渲染 `<script>` / event handler 注入字符串。

### F4 · M3/M8/M9/L2 不能全部放 Phase 5+，否则不满足用户目标

用户要求“确保优化方案能完全修复 review 报告的所有问题”。v1 明确把 M3/M8/M9/L2 放到 Phase 5+，这会造成范围不完整。

证据摘录：

```text
748 /home/long/project/gaokao-volunteer-system/docs/plans/2026-07-07-review-remediation-execution-plan.md
45:| H10 | §11.2 | E2E 中 Vite proxy 大量 ECONNREFUSED，mock E2E 与 real-backend E2E 边界未分层 | Phase 3 |
46:| M1 | §4 | Playwright firefox/webkit 浏览器 executable 缺失 | Phase 3 |
47:| M3 | §4 | `admin/routes/web_public.py` 单文件 300KB，维护风险高 | Phase 5+（后续） |
48:| M4/M6 | §4/§11.3 | `web_public.py:2665` invalid escape sequence `\s` | Phase 4 |
50:| M7 | §11.3 | SQL `execute(f"...")` / subprocess / innerHTML 需白名单审计 | Phase 4 |
51:| M8 | §11.3 | OpenAPI 66 paths 已生成但 contract quartet 矩阵缺失 | Phase 5+（后续） |
52:| M9 | §11.3 | domain data 与 LLM prompt 承诺的覆盖率验收未做成 gate | Phase 5+（后续） |
54:| L2 | §5 | `.worktrees/` / `.turbo/cache/` / 旧截图噪音 | Phase 5+（后续） |
77:   - 当前 fresh gates 结果：后端 mypy 3 errors、前端 i18n gate 1 failed、Playwright E2E poster/share 真实交互失败
122:   > 当前状态：2026-07-07 二次严格 Review 发现后端 mypy / 前端 i18n / Playwright E2E 三项门禁回归未闭环，正在按 `docs/plans/2026-07-07-review-remediation-execution-plan.md` 系统修复；线上真实支付/域名/真实流量 acceptance 仍未完成。
338:### T3-01 安装 Playwright 缺失浏览器
383:检查 fallback route 的 predicate：`url.pathname.startsWith('/api/') && !url.pathname.includes('/poster/')`。`/api/plans` 会被 fallback 匹配，但 Playwright 按注册顺序调用第一个匹配的 handler，所以 `/api/plans` 的精确 mock 会先命中。
437:### T3-04 拆分 mock E2E 与 real-backend E2E 命令
439:**目标：** 解决 H10——mock E2E 与 real-backend E2E 边界未分层。
455:    "test:e2e:real-backend": "GAOKAO_E2E_REAL_BACKEND=1 playwright test"
461:- `test:e2e:mock`：默认模式，所有 API 通过 Playwright `page.route()` mock，不依赖真实后端。
462:- `test:e2e:real-backend`：需要先启动 FastAPI 后端（`python -m admin.app --port 8000`），验证 `/health` 返回 `settings_valid=true`，再运行 E2E。
463:- 当前所有 E2E spec 都是 mock 模式；real-backend 模式将在后续 Phase 补真实后端联调用例。
469:git commit -m "fix(e2e): T3 pre-seed plans/share-link mock data + split mock/real-backend e2e commands"
523:### T4-02 修 web_public.py invalid escape sequence
525:**目标：** 消除 M6——`admin/routes/web_public.py:2665` 的 `DeprecationWarning: invalid escape sequence '\s'`。
528:- Modify: `admin/routes/web_public.py`（定位含 `\s` 的 f-string）
533:grep -n '\\s' admin/routes/web_public.py | head -10
624:### T4-06 SQL/subprocess/innerHTML 安全白名单审计
635:- **需修复**：`admin/routes/web_public.py:1281,2921` 的 `innerHTML` 赋值（如果拼接用户输入则需改为 textContent 或 DOMPurify）。
636:- **安全（vendored）**：`admin/static/vendor/echarts.min.js` 的 `innerHTML`（已做 HTML escape）。
643:git add data/orders/cli.py data/orders/tests/test_cli.py admin/routes/web_public.py README.md docker-compose.yml docker-compose.prod.yml .gitignore docs/SECURITY_AUDIT_2026-07-07.md
718:## 后续（Phase 5+，不在本计划范围）
722:- **M3**：拆分 `admin/routes/web_public.py`（300KB → 按业务域拆 5-6 个模块）。
723:- **M8**：补 OpenAPI → backend route → React api-generated types → frontend caller 的 contract quartet 矩阵。
724:- **M9**：把 domain data 与 LLM prompt 承诺的覆盖率做成发布前 gate。
```

建议 v2 增加：
- Phase 5：Structural Governance Completion。
- M3 至少完成 `web_public.py` 拆分第一刀：抽出 content/policy pages 或 shared shell helper。
- M8 创建 contract quartet matrix 与检查脚本。
- M9 创建 prompt-data coverage gate。
- L2 建立 artifact 归档/ignore 策略并执行一次清理。

### F5 · T2 i18n 实现建议需避免 `intl.messages[key]` 动态访问弱类型

v1 建议直接读 `intl.messages[key]`，可行但较脆弱。更稳妥的是：显式维护 `statusMessageIds` 映射，使用 `intl.formatMessage({ id })`。

建议 v2 改为：

```tsx
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

### F6 · Final Regression 缺少“CI/readback + working tree clean”

v1 T5 有本地 gate，但缺少：
- `git status --short` clean check。
- 三远端 readback SHA 一致。
- CI workflow 本地静态校验 / GitHub Actions 触发后的状态检查。
- `pnpm test:e2e` 全项目前，必须先安装 browsers，否则会重复环境失败。

---

## 3. Recommendation

**建议不要直接执行 v1。**

推荐动作：
1. 使用 `docs/plans/2026-07-07-review-remediation-execution-plan-v2.md` 作为唯一执行入口。
2. v1 已标记为历史草案，仅保留审计轨迹。
3. 后续执行前先 commit 文档：plan audit + v2 plan，防止实现过程丢失设计依据。

Gate verdict: **CONDITIONAL**。

- 若采用 v2：方案可以覆盖 review 报告全部问题。
- 若继续执行 v1：只能覆盖 P0/P1 主干，不能保证完全修复 M3/M8/M9/L2 和 M7 代码级安全风险。
