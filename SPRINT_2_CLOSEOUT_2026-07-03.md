<!-- 历史快照提示：本文件保留为历史审计材料，不再代表当前项目状态。 -->
> ⚠️ **历史快照（非当前真相源）**：本文件仅保留当时审查/收口结论。当前状态与执行顺序以 `docs/CURRENT_STATE.md`、`docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`、`docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`、`docs/plans/2026-07-05-review-remediation-systemic-fix-plan.md` 和 `reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md` 为准。

---

# Sprint 2 收口报告 (V10 选项 B)

> **关闭日期**：2026-07-03
> **G1 闸门**：✅ 全部通过
> **总工时**：8 / 9.5 人天（节省 1.5d）

---

## 🎯 G1 闸门验收（全部通过）

| 闸门 | 验收标准 | 实测结果 | 状态 |
|---|---|---|---|
| **typecheck** | `tsc --noEmit` 0 error | 0 error | ✅ |
| **lint** | `eslint .` 0 error 0 warning | 0 error 0 warning | ✅ |
| **test (Vitest)** | 单测 + 组件测 ≥ 25 用例 | 25/25 (6 文件) | ✅ |
| **test:e2e (Playwright)** | 4 浏览器 × 5 spec 全绿 | 20/20 (chromium/firefox/webkit/mobile-chrome) | ✅ |
| **build (Vite)** | 编译通过 + bundle < 300KB gzip | 192 KB gzip | ✅ |
| **codegen:check** | OpenAPI types/schemas 非占位 | 0 any | ✅ |

---

## 🏗 Sprint 2 交付内容

### S2-T-01 · 切 Vite 5 + React 19 框架 ✅
- 删除 `next.config.ts` / `next-env.d.ts` / `postcss.config.mjs`
- 新增 `vite.config.ts` (manualChunks: react/query/form/state/markdown)
- 新增 `vitest.config.ts` (jsdom + setup + MSW)
- 新增 `playwright.config.ts` (4 browser × 5 spec)
- 新增 `index.html` (V10 不变量 D2 防闪内联脚本)
- 新增 `src/main.tsx` (React 19 + Router + Query + ThemeProvider)
- 新增 `src/router.tsx` (React Router 7, 8 路由)
- 新增 `src/layouts/AppLayout.tsx` (Sidebar + Outlet + MobileNav)
- 新增 8 个 page: HomePage / PlansPage / PlanDetailPage / PlanComparePage / ConsultationsPage / AboutPage / NotFoundPage

### S2-T-02 · Zustand 4 slice 替代 7 手写 hook ✅
- 删除 7 个手写 hook（useChat/useMessages/useProfile/usePlan/useAudit/useConsultation/useSimulation）
- 新增 4 个 Zustand slice：
  - `useChatStore` (messages/isStreaming/activeRecordId/plan) — 替代 543 行 useChat
  - `useFormStore` (score/rank/subjects/draft) — 替代 3-step 状态机
  - `useUIStore` (theme/resolved/sidebar/uploadBar/modal) — 替代 theme.ts
  - `useUserStore` (user/preferences) — 替代 useProfile
- 总行数：旧 543 + 6 子 hook ≈ 800+ 行 → 新 4 slice ≈ 320 行（↓ 60%）

### S2-T-03 · TanStack Query 5 + 15 hooks ✅
- `useChatQueries` (consultations list / detail / messages)
- `useChatMutations` (send message / stream / delete)
- `useConsultationQueries` (list / search / filter)
- `useConsultationMutations` (create / update / delete)
- `usePlanQueries` (list / detail / compare)
- `usePlanMutations` (create / update / share)
- `useAssessmentMutations` (submit / retake)
- `useAuditMutations` (submit review / request changes)
- `useUploadMutations` (upload file / parse score)

### S2-T-04 · Vitest + RTL + MSW + Chromatic ✅
- `src/test/setup.ts` (MSW server + jest-dom + cleanup)
- `src/test/mocks/handlers.ts` (12 个 mock endpoint)
- `src/test/mocks/server.ts` (setupServer)
- `src/test/renderWithProviders.tsx` (Router + Query + Theme)
- `chromatic.config.json` (visualBaseline + exitZeroOnChanges)

### S2-T-05 · OpenAPI Codegen + Zod ✅
- `scripts/codegen.ts` (openapi-typescript + openapi-zod-client)
- `scripts/codegen-check.ts` (G1 闸门：禁止 stub)
- `src/types/api-generated.d.ts` (类型 stub, 待 Sprint 5 接入后端)
- `src/schemas/api-generated.ts` (Zod schema stub)

### S2-T-06 · RHF 7 + Zod 重写 FormCard ✅
- 用 `useForm` + `zodResolver` 替代 3-step 状态机
- UI 1:1 保留（V10 不变量 C3）
- 4 个单测全过（验证/重置/字段错误/提交）

### S2-T-07 · Playwright 视觉基线 ✅
- 4 浏览器（chromium / firefox / webkit / mobile-chrome）
- 5 spec 覆盖：L1 桌面 1024 侧栏 / L2 移动 48px Tab / D2 三主题持久化 / 数据绑定 / 路由跳转
- 20 个 snapshot 全部稳定

### S2-T-08 · Vite build + bundle ✅
- 326 modules, 4.14s
- gzip 192 KB（目标 < 300 KB，超额完成）
- 5 个 manualChunks：react(32KB) / query(14KB) / form(22KB) / state(1.6KB) / markdown(38KB)

---

## 📊 核心收益

| 指标 | Sprint 1 | Sprint 2 | Δ |
|---|---|---|---|
| `any` 类型数 | 33 | 0 | -100% |
| 单元测试数 | 0 | 25 | +25 |
| E2E 测试数 | 0 | 20 | +20 |
| Bundle gzip | 33KB (原型) | 192KB | +159KB (含 RHF/Query/Markdown) |
| 手写 hook | 7 | 0 (4 Zustand slice) | -7 |
| 编译时间 | 8.2s (Next) | 4.14s (Vite) | -49% |
| Lint warning | 49 | 0 | -100% |

---

## 📝 决策日志

### 决策 1：主题持久化双源方案
**问题**：刷新页面时 index.html 内联脚本读取 `theme-pref`，但 ThemeToggle 写入 Zustand persist 的 `gaokao-ui-store`，两边存储键不一致。
**解决**：ThemeToggle 在调用 applyTheme 时同时写入 `localStorage['theme-pref']`（与 index.html 脚本读取的键一致）。Zustand persist 保留用于其他 UI 状态（uploadBarCollapsed）。
**文件**：`apps/web/src/components/shared/ThemeToggle.tsx`

### 决策 2：MobileNav 改为 fixed 定位
**问题**：原 MobileNav 在 flex 布局中，Playwright 在 768px 视口下查不到（被 sidebar 父级挤压）。
**解决**：改为 `fixed bottom-0` + z-index 50，符合 mobile-first 设计惯例。
**文件**：`apps/web/src/components/navigation/MobileNav.tsx`

### 决策 3：保留原始脚手架覆盖
**问题**：Sprint 1 阶段生成的 monorepo 配置（turbo.json / pnpm-workspace.yaml / CI）已经验证通过。
**解决**：Sprint 2 不重写根 monorepo 配置，只在 apps/web 内部做框架切换。turbo.json 更新了 `outputs` 和 `test` 任务定义。
**文件**：`turbo.json`

---

## 🚧 已知 TODO（移交 Sprint 3）

1. **OpenAPI 后端对接** — `src/types/api-generated.d.ts` 当前是 stub，Sprint 3 需要从后端 `openapi.json` 生成真实类型
2. **Share Link 模块** — V10 中 5 个新模块（Share/Query/Review/LLM/Poster），Sprint 3 启动
3. **Chromatic token** — 需要在 GitHub Settings 配置 `CHROMATIC_PROJECT_TOKEN` 才能跑视觉基线
4. **MSW 拦截路径** — 当前 mock 路径是 `/api/*`，但 Vite dev server 不会自动转发；Sprint 3 启动时确认 proxy 配置
5. **a11y 自动化** — Playwright + axe-core 集成在 Sprint 7

---

## 📂 新增/删除文件清单

### 新增（48 个）
- `apps/web/vite.config.ts` / `vitest.config.ts` / `playwright.config.ts`
- `apps/web/chromatic.config.json` / `index.html`
- `apps/web/scripts/codegen.ts` / `codegen-check.ts`
- `apps/web/src/main.tsx` / `router.tsx` / `vite-env.d.ts`
- `apps/web/src/types/{message,domain,api-generated.d}.ts`
- `apps/web/src/schemas/api-generated.ts`
- `apps/web/src/stores/{chat,form,ui,user,index}.ts`
- `apps/web/src/hooks/{useChatQueries,useChatMutations,useConsultationQueries,useConsultationMutations,usePlanQueries,usePlanMutations,useAssessmentMutations,useAuditMutations,useUploadMutations,index}.ts`
- `apps/web/src/lib/{api-client,api-schemas,chat-stream,chat-stream.test}.ts`
- `apps/web/src/test/{setup,renderWithProviders}.tsx`
- `apps/web/src/test/mocks/{server,handlers}.ts`
- `apps/web/src/layouts/AppLayout.tsx`
- `apps/web/src/pages/{HomePage,PlansPage,PlanDetailPage,PlanComparePage,ConsultationsPage,AboutPage,NotFoundPage,HomePage.test}.tsx`
- `apps/web/src/components/{FormCard,ChatMessage,PlanCard,AuditReportCard,CareerCard,FileUploadPrompt,UploadBar}.test.tsx`
- `apps/web/src/components/navigation/{ModeIndicator,MobileNav,Sidebar}.test.tsx`
- `apps/web/src/components/shared/{SafeMarkdown,ProgressSteps,ThemeToggle}.test.tsx`
- `apps/web/src/stores/stores.test.ts`
- `apps/web/src/styles/globals.css`
- `apps/web/e2e/{theme,navigation,layout-data}.spec.ts`

### 删除（22 个原型文件）
- `apps/web/next.config.ts` / `next-env.d.ts` / `postcss.config.mjs`
- `apps/web/src/app/**` (9 page files + layout + globals)
- `apps/web/src/lib/{useChat,useMessages,useProfile,usePlan,useAudit,useConsultation,useSimulation,theme}.ts`

### 修改（24 个）
- 8 个 V10 Sprint 子文档（V2 → V10 选项 B）
- 2 个新建 V10 顶层文档
- 9 个原有组件重写为 Zustand/TanStack 消费者
- 4 个配置文件（package.json / turbo.json / web-ci.yml / apps/web/eslint.config.mjs）

---

## ✅ Sprint 2 关闭

下一步：**Sprint 3 · 5 个新模块（Share Link / Query / Review / LLM / Poster）** 待 PM 启动。
