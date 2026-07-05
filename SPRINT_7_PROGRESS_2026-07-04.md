# Sprint 7 Progress · 2026-07-04

> **状态**：✅ 非 Docker / 非外部 token 的 Sprint 7 前端可执行项已完成；2026-07-05 已补修 i18n 迁移后的 e2e selector 回归。
> **本轮范围**：T-D-22 react-intl 基础接入、T-D-23 i18n key 覆盖守门、T-E-01 `/admin/login`、T-E-02 `/admin` Dashboard 最小入口、T-E-03 后台 Layout、T-E-04 `/admin/error` 错误兜底、T-E-05 `<RequireAuth>` 权限守卫、T-E-06 订单列表、T-E-07 订单详情、T-E-08/T-E-09 案例列表与详情、T-E-10 本地 a11y 守门。
> **环境说明**：本机暂无 Docker；Chromatic / Storybook baseline 仍依赖外部配置和 token，Docker 验证继续等待本机环境可用。

---

## ✅ 本轮完成

| 任务 | 范围 | 状态 | 证据 |
|---|---|---|---|
| T-D-22 | `react-intl` 依赖安装 | ✅ DONE | `apps/web/package.json`, `pnpm-lock.yaml` |
| T-D-22 | `IntlProvider` 基础接入 | ✅ DONE | `apps/web/src/i18n/AppIntlProvider.tsx`, `apps/web/src/main.tsx` |
| T-D-22 | zh-CN / en-US 基础 messages | ✅ DONE | `apps/web/src/i18n/messages/zh-CN.json`, `apps/web/src/i18n/messages/en-US.json` |
| T-D-22 | LocaleSwitcher 接入后台 Header | ✅ DONE | `apps/web/src/components/shared/LocaleSwitcher.tsx`, `apps/web/src/layouts/AdminLayout.tsx` |
| T-D-23 | zh-CN / en-US key 对齐与空值守门 | ✅ DONE | `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | Sprint 7 管理端错误页文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/admin/ErrorPage.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | 管理端登录页 / 403 页文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/admin/LoginPage.tsx`, `apps/web/src/pages/admin/ForbiddenPage.tsx` |
| T-D-23 | 管理端 Dashboard 文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/admin/DashboardPage.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | 管理端订单列表文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/admin/OrdersPage.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | 管理端案例列表文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/admin/CasesPage.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | 管理端订单详情 / 案例详情文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/admin/OrderDetailPage.tsx`, `apps/web/src/pages/admin/CaseDetailPage.tsx` |
| T-D-23 | 管理端布局 / 登录 / 403 / 错误页 / Dashboard / 订单 / 案例全页硬编码中文回归守门 | ✅ DONE | `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | 全局导航壳层 / AppLayout 文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/components/navigation/*.tsx`, `apps/web/src/layouts/AppLayout.tsx` |
| T-D-23 | Sidebar / MobileNav / ModeIndicator i18n 回归覆盖 | ✅ DONE | `apps/web/src/components/navigation/Sidebar.test.tsx`, `apps/web/src/components/navigation/MobileNav.test.tsx`, `apps/web/src/components/navigation/ModeIndicator.test.tsx` |
| T-D-23 | AboutPage 帮助页文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/AboutPage.tsx`, `apps/web/src/pages/AboutPage.test.tsx` |
| T-D-23 | 通用测试渲染器补齐 IntlProvider / locale 覆盖 | ✅ DONE | `apps/web/src/test/renderWithProviders.tsx` |
| T-D-23 | NotFound / ErrorFallback 全局兜底文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/NotFoundPage.tsx`, `apps/web/src/components/shared/ErrorFallback.tsx` |
| T-D-23 | NotFound / ErrorFallback 中英文回归覆盖 | ✅ DONE | `apps/web/src/pages/NotFoundPage.test.tsx`, `apps/web/src/components/shared/ErrorFallback.test.tsx` |
| T-D-23 | Plans / PlanCompare / PlanDetail 文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/PlansPage.tsx`, `apps/web/src/pages/PlanComparePage.tsx`, `apps/web/src/pages/PlanDetailPage.tsx` |
| T-D-23 | Plans 模块中英文回归覆盖 | ✅ DONE | `apps/web/src/pages/PlansPage.test.tsx`, `apps/web/src/pages/PlanComparePage.test.tsx`, `apps/web/src/pages/PlanDetailPage.test.tsx` |
| T-D-23 | ConsultationsPage 咨询记录页文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/ConsultationsPage.tsx` |
| T-D-23 | ConsultationsPage 中英文回归覆盖 | ✅ DONE | `apps/web/src/pages/ConsultationsPage.test.tsx` |
| T-D-23 | Share 管理模块文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/ShareDialogPage.tsx`, `apps/web/src/components/ShareDialog.tsx`, `apps/web/src/components/SharePanel.tsx`, `apps/web/src/components/ShareStatusPanel.tsx`, `apps/web/src/components/StatsCard.tsx`, `apps/web/src/components/AccessTrendChart.tsx` |
| T-D-23 | Share 管理模块中英文回归覆盖 | ✅ DONE | `apps/web/src/pages/ShareDialogPage.test.tsx`, `apps/web/src/components/ShareDialog.test.tsx`, `apps/web/src/components/SharePanel.test.tsx`, `apps/web/src/components/ShareStatusPanel.test.tsx`, `apps/web/src/components/StatsCard.test.tsx`, `apps/web/src/components/AccessTrendChart.test.tsx` |
| T-D-23 | PosterPreview 海报生成模块文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/PosterPreviewPage.tsx`, `apps/web/src/components/PosterPreview.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | PosterPreview 海报生成模块中英文回归覆盖 | ✅ DONE | `apps/web/src/pages/PosterPreviewPage.test.tsx`, `apps/web/src/components/PosterPreview.test.tsx`, `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | DataQuery 数据查询模块文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/DataQueryPage.tsx`, `apps/web/src/components/DataQueryForm.tsx`, `apps/web/src/components/DataQueryResult.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | DataQuery 数据查询模块中英文回归覆盖 | ✅ DONE | `apps/web/src/pages/DataQueryPage.test.tsx`, `apps/web/src/components/DataQueryForm.test.tsx`, `apps/web/src/components/DataQueryResult.test.tsx`, `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | HomePage / FormCard 首页信息收集模块文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/HomePage.tsx`, `apps/web/src/components/FormCard.tsx`, `apps/web/src/components/shared/ProgressSteps.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | HomePage / FormCard 首页信息收集模块中英文回归覆盖 | ✅ DONE | `apps/web/src/pages/HomePage.test.tsx`, `apps/web/src/components/FormCard.test.tsx`, `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | ReviewFlow / LLMEnhancement / AuditReportCard 审核域文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/ReviewPage.tsx`, `apps/web/src/components/ReviewFlow.tsx`, `apps/web/src/components/LLMEnhancement.tsx`, `apps/web/src/components/AuditReportCard.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | 审核域中英文回归覆盖 | ✅ DONE | `apps/web/src/pages/ReviewPage.test.tsx`, `apps/web/src/components/ReviewFlow.test.tsx`, `apps/web/src/components/LLMEnhancement.test.tsx`, `apps/web/src/components/AuditReportCard.test.tsx`, `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | PlanCard / CareerCard / FileUploadPrompt / UploadBar 聊天卡片与上传入口文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/components/PlanCard.tsx`, `apps/web/src/components/CareerCard.tsx`, `apps/web/src/components/FileUploadPrompt.tsx`, `apps/web/src/components/UploadBar.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | 聊天卡片与上传入口中英文回归覆盖 | ✅ DONE | `apps/web/src/components/PlanCard.test.tsx`, `apps/web/src/components/CareerCard.test.tsx`, `apps/web/src/components/FileUploadPrompt.test.tsx`, `apps/web/src/components/UploadBar.test.tsx`, `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | PortalPage 分享门户页文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/pages/PortalPage.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | PortalPage 分享门户页中英文回归覆盖 | ✅ DONE | `apps/web/src/pages/PortalPage.test.tsx`, `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | ThemeToggle / Toast / Pagination / RouteFallback 共享组件默认文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/components/shared/ThemeToggle.tsx`, `apps/web/src/components/shared/Toast.tsx`, `apps/web/src/components/shared/Pagination.tsx`, `apps/web/src/components/shared/RouteFallback.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | 共享组件默认文案中英文回归覆盖 | ✅ DONE | `apps/web/src/components/shared/ThemeToggle.test.tsx`, `apps/web/src/components/shared/Toast.test.tsx`, `apps/web/src/components/shared/Pagination.test.tsx`, `apps/web/src/components/shared/RouteFallback.test.tsx`, `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | OfflineBanner / DataTable / Skeleton / Charts / Modal / Stepper / Tree / Accordion / SubmitButton / Avatar 共享组件默认文案迁移到 `react-intl` | ✅ DONE | `apps/web/src/components/shared/OfflineBanner.tsx`, `apps/web/src/components/shared/DataTable.tsx`, `apps/web/src/components/shared/Skeleton.tsx`, `apps/web/src/components/shared/Charts.tsx`, `apps/web/src/components/shared/Modal.tsx`, `apps/web/src/components/shared/Stepper.tsx`, `apps/web/src/components/shared/Tree.tsx`, `apps/web/src/components/shared/Accordion.tsx`, `apps/web/src/components/shared/SubmitButton.tsx`, `apps/web/src/components/shared/Avatar.tsx`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | 共享组件扩展默认文案中英文回归覆盖 | ✅ DONE | `apps/web/src/components/shared/OfflineBanner.test.tsx`, `apps/web/src/components/shared/DataTable.test.tsx`, `apps/web/src/components/shared/Skeleton.test.tsx`, `apps/web/src/components/shared/Charts.test.tsx`, `apps/web/src/components/shared/Modal.test.tsx`, `apps/web/src/components/shared/Stepper.test.tsx`, `apps/web/src/components/shared/Tree.test.tsx`, `apps/web/src/components/shared/Accordion.test.tsx`, `apps/web/src/components/shared/SubmitButton.test.tsx`, `apps/web/src/components/shared/Avatar.test.tsx`, `apps/web/src/quality/i18nMessagesCoverage.test.ts` |
| T-D-23 | Chat / LLM runtime 可见文案收口 | ✅ DONE | `apps/web/src/hooks/useChatMutations.ts`, `apps/web/src/hooks/useChatOrchestrator.ts`, `apps/web/src/hooks/useLLMEnhanceMutation.ts`, `apps/web/src/lib/llm/provider.ts`, `apps/web/src/i18n/messages/*.json` |
| T-D-23 | 非生成生产源码中文硬编码清理 | ✅ DONE | `apps/web/src/components/**/*.tsx`, `apps/web/src/hooks/**/*.ts`, `apps/web/src/stores/**/*.ts`, `apps/web/src/lib/**/*.ts`, `apps/web/src/types/**/*.ts`；保留 `api-generated.*` 生成产物 |
| T-E-01 | 管理员登录页 `/admin/login` | ✅ DONE | `apps/web/src/pages/admin/LoginPage.tsx` |
| T-E-01 | RHF + Zod 手机号 / 验证码校验 | ✅ DONE | `apps/web/src/pages/admin/LoginPage.test.tsx` |
| T-E-01 | 本地 mock 登录链路（验证码 `123456`） | ✅ DONE | `apps/web/src/pages/admin/LoginPage.test.tsx` |
| T-E-02 | 后台 Dashboard `/admin` 最小运营入口 | ✅ DONE | `apps/web/src/pages/admin/DashboardPage.tsx` |
| T-E-02 | 4 KPI 卡片 + 订单趋势图 + 最近订单表 | ✅ DONE | `apps/web/src/pages/admin/DashboardPage.test.tsx` |
| T-E-03 | 后台共享 Layout / Sidebar / Header | ✅ DONE | `apps/web/src/layouts/AdminLayout.tsx` |
| T-E-04 | 后台错误兜底页 `/admin/error` | ✅ DONE | `apps/web/src/pages/admin/ErrorPage.tsx` |
| T-E-04 | 刷新重试 / 返回运营概览操作入口 | ✅ DONE | `apps/web/src/pages/admin/ErrorPage.test.tsx` |
| T-E-04 | AdminLayout ErrorBoundary 接入后台专属兜底 | ✅ DONE | `apps/web/src/layouts/AdminLayout.tsx`, `apps/web/src/layouts/AdminLayout.test.tsx` |
| T-E-05 | `<RequireAuth>` 未登录跳 `/admin/login` | ✅ DONE | `apps/web/src/components/admin/RequireAuth.tsx` |
| T-E-05 | 非管理员跳 `/403` | ✅ DONE | `apps/web/src/components/admin/RequireAuth.test.tsx` |
| T-E-05 | user store 支持 `role: user/admin` | ✅ DONE | `apps/web/src/stores/user.ts`, `apps/web/src/stores/stores.test.ts` |
| T-E-06 | 订单列表页 `/admin/orders` | ✅ DONE | `apps/web/src/pages/admin/OrdersPage.tsx` |
| T-E-06 | `useAdminOrdersQuery` 接入 `/api/admin/orders` generated schema | ✅ DONE | `apps/web/src/hooks/useAdminOrders.ts` |
| T-E-06 | 状态 / 来源筛选 + DataTable + 分页入口 | ✅ DONE | `apps/web/src/pages/admin/OrdersPage.test.tsx` |
| T-E-06 | Admin orders MSW mock 补齐 | ✅ DONE | `apps/web/src/test/mocks/handlers.ts` |
| T-E-07 | 订单详情页 `/admin/orders/:orderId` | ✅ DONE | `apps/web/src/pages/admin/OrderDetailPage.tsx` |
| T-E-07 | `useAdminOrderQuery` 接入 `/api/admin/orders/:order_id` generated schema | ✅ DONE | `apps/web/src/hooks/useAdminOrders.ts` |
| T-E-07 | 学生 / 客户 / 状态历史 / 操作按钮组 | ✅ DONE | `apps/web/src/pages/admin/OrderDetailPage.test.tsx` |
| T-E-08 | 案例列表页 `/admin/cases` | ✅ DONE | `apps/web/src/pages/admin/CasesPage.tsx` |
| T-E-08 | `useAdminCasesQuery` 接入 `/api/admin/cases` generated schema | ✅ DONE | `apps/web/src/hooks/useAdminCases.ts` |
| T-E-08 | 类型 / 审核状态筛选 + 网格空态 | ✅ DONE | `apps/web/src/pages/admin/CasesPage.test.tsx` |
| T-E-09 | 案例详情页 `/admin/cases/:caseId` | ✅ DONE | `apps/web/src/pages/admin/CaseDetailPage.tsx` |
| T-E-09 | `useAdminCaseQuery` 接入 `/api/admin/cases/:case_id` generated schema | ✅ DONE | `apps/web/src/hooks/useAdminCases.ts` |
| T-E-09 | SafeMarkdown 案例正文渲染 + 无效 ID 兜底 | ✅ DONE | `apps/web/src/pages/admin/CaseDetailPage.test.tsx` |
| T-E-10 | 后台页面本地 a11y 覆盖守门 | ✅ DONE | `apps/web/src/quality/adminA11yCoverage.test.ts` |
| T-E-10 | 语义地标 / 表单标签 / 焦点可见 / 暗色态静态检查 | ✅ DONE | `npm run test -- src/quality/adminA11yCoverage.test.ts` |
| T-E-10 | 公共入口 / 数据查询 / 后台入口运行时 a11y 烟测 | ✅ DONE | `apps/web/e2e/runtime-accessibility.spec.ts` |
| T-E-11 | Admin portal Chromium e2e 覆盖 | ✅ DONE | `apps/web/e2e/admin-portal.spec.ts` |
| T-E-11 | 登录 / 权限态 / 订单 / 案例 / 错误页路径回归 | ✅ DONE | 临时 Vite dev config + Playwright Chromium |

---

## ✅ 验证结果

| Gate | Command | Result |
|---|---|---|
| Sprint 7 后台基础回归 | `npm run test -- src/components/admin/RequireAuth.test.tsx src/pages/admin/LoginPage.test.tsx src/pages/admin/DashboardPage.test.tsx src/stores/stores.test.ts` | ✅ 4 files / 16 tests |
| Sprint 7 订单列表回归 | `npm run test -- src/pages/admin/OrdersPage.test.tsx src/pages/admin/DashboardPage.test.tsx src/components/admin/RequireAuth.test.tsx` | ✅ 3 files / 6 tests |
| Sprint 7 订单/案例详情回归 | `npm run test -- src/pages/admin/CasesPage.test.tsx src/pages/admin/CaseDetailPage.test.tsx src/pages/admin/OrderDetailPage.test.tsx src/pages/admin/OrdersPage.test.tsx` | ✅ 4 files / 8 tests |
| Sprint 7 错误页回归 | `npm run test -- src/layouts/AdminLayout.test.tsx src/pages/admin/ErrorPage.test.tsx src/quality/adminA11yCoverage.test.ts` | ✅ 3 files / 6 tests |
| Sprint 7 i18n 管理端迁移回归 | `npm run test -- src/pages/admin/ErrorPage.test.tsx src/layouts/AdminLayout.test.tsx src/quality/i18nMessagesCoverage.test.ts src/quality/adminA11yCoverage.test.ts` | ✅ 4 files / 9 tests |
| Sprint 7 登录/403 i18n 回归 | `npm run test -- src/pages/admin/LoginPage.test.tsx src/components/admin/RequireAuth.test.tsx src/quality/i18nMessagesCoverage.test.ts src/pages/admin/ErrorPage.test.tsx src/layouts/AdminLayout.test.tsx` | ✅ 5 files / 11 tests |
| Sprint 7 Dashboard i18n 回归 | `npm run test -- src/pages/admin/DashboardPage.test.tsx src/pages/admin/LoginPage.test.tsx src/quality/i18nMessagesCoverage.test.ts src/layouts/AdminLayout.test.tsx src/pages/admin/ErrorPage.test.tsx` | ✅ 5 files / 9 tests |
| Sprint 7 订单列表 i18n 回归 | `npm run test -- src/pages/admin/OrdersPage.test.tsx src/pages/admin/DashboardPage.test.tsx src/quality/i18nMessagesCoverage.test.ts src/pages/admin/LoginPage.test.tsx src/layouts/AdminLayout.test.tsx` | ✅ 5 files / 10 tests |
| Sprint 7 案例列表 i18n 回归 | `npm run test -- src/pages/admin/CasesPage.test.tsx src/pages/admin/OrdersPage.test.tsx src/quality/i18nMessagesCoverage.test.ts src/pages/admin/DashboardPage.test.tsx src/pages/admin/LoginPage.test.tsx` | ✅ 5 files / 11 tests |
| Sprint 7 详情页 i18n 回归 | `npm run test -- src/pages/admin/OrderDetailPage.test.tsx src/pages/admin/CaseDetailPage.test.tsx src/pages/admin/CasesPage.test.tsx src/pages/admin/OrdersPage.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 5 files / 11 tests |
| Sprint 7 后台全页 i18n/a11y 回归 | `npm run test -- src/components/admin/RequireAuth.test.tsx src/pages/admin/LoginPage.test.tsx src/pages/admin/DashboardPage.test.tsx src/pages/admin/OrdersPage.test.tsx src/pages/admin/OrderDetailPage.test.tsx src/pages/admin/CasesPage.test.tsx src/pages/admin/CaseDetailPage.test.tsx src/pages/admin/ErrorPage.test.tsx src/layouts/AdminLayout.test.tsx src/quality/i18nMessagesCoverage.test.ts src/quality/adminA11yCoverage.test.ts` | ✅ 11 files / 24 tests |
| Sprint 7 导航壳层 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/components/navigation/Sidebar.test.tsx src/components/navigation/MobileNav.test.tsx src/components/navigation/ModeIndicator.test.tsx src/layouts/AppLayout.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 5 files / 11 tests |
| Sprint 7 AboutPage i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/pages/AboutPage.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 2 files / 6 tests |
| Sprint 7 全局兜底 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/pages/NotFoundPage.test.tsx src/components/shared/ErrorFallback.test.tsx src/layouts/AppLayout.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 4 files / 8 tests |
| Sprint 7 Plans 模块 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/pages/PlansPage.test.tsx src/pages/PlanComparePage.test.tsx src/pages/PlanDetailPage.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 4 files / 11 tests |
| Sprint 7 ConsultationsPage i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/pages/ConsultationsPage.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 2 files / 9 tests |
| Sprint 7 Share 管理模块 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/components/AccessTrendChart.test.tsx src/components/StatsCard.test.tsx src/components/ShareStatusPanel.test.tsx src/components/SharePanel.test.tsx src/components/ShareDialog.test.tsx src/pages/ShareDialogPage.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 7 files / 24 tests |
| Sprint 7 PosterPreview 海报模块 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/components/PosterPreview.test.tsx src/pages/PosterPreviewPage.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 3 files / 14 tests |
| Sprint 7 DataQuery 数据查询模块 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/pages/DataQueryPage.test.tsx src/components/DataQueryForm.test.tsx src/components/DataQueryResult.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 4 files / 23 tests |
| Sprint 7 HomePage / FormCard 首页信息收集模块 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/pages/HomePage.test.tsx src/components/FormCard.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 3 files / 10 tests |
| Sprint 7 审核域 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/components/ReviewFlow.test.tsx src/components/LLMEnhancement.test.tsx src/pages/ReviewPage.test.tsx src/components/AuditReportCard.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 5 files / 20 tests |
| Sprint 7 聊天卡片与上传入口 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/components/PlanCard.test.tsx src/components/CareerCard.test.tsx src/components/FileUploadPrompt.test.tsx src/components/UploadBar.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 5 files / 12 tests |
| Sprint 7 PortalPage 分享门户页 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/pages/PortalPage.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 2 files / 6 tests |
| Sprint 7 共享组件默认文案 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/components/shared/ThemeToggle.test.tsx src/components/shared/Toast.test.tsx src/components/shared/Pagination.test.tsx src/components/shared/RouteFallback.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 5 files / 14 tests |
| Sprint 7 共享组件扩展默认文案 i18n 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/components/shared/OfflineBanner.test.tsx src/components/shared/DataTable.test.tsx src/components/shared/Skeleton.test.tsx src/components/shared/Charts.test.tsx src/components/shared/Modal.test.tsx src/components/shared/Stepper.test.tsx src/components/shared/Tree.test.tsx src/components/shared/Accordion.test.tsx src/components/shared/SubmitButton.test.tsx src/components/shared/Avatar.test.tsx src/quality/i18nMessagesCoverage.test.ts` | ✅ 11 files / 36 tests |
| Sprint 7 Chat / LLM runtime 文案回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs src/hooks/useLLMEnhanceMutation.test.tsx src/lib/llm/provider.test.ts src/quality/i18nMessagesCoverage.test.ts` | ✅ 3 files / 9 tests |
| Sprint 7 非生成生产源码中文扫描 | `Get-ChildItem apps\web\src -Recurse -Include *.ts,*.tsx ... excluding tests/messages/mocks/generated/api-generated.* | Select-String '[\u4e00-\u9fff]'` | ✅ 0 findings |
| Sprint 7 前端全量 Vitest 回归 | `vitest run --config %TEMP%\gaokao-vitest-nav\vitest.config.mjs` | ✅ 77 files / 251 tests |
| Sprint 7 production build（临时 outDir） | `vite build --config %TEMP%\gaokao-web-build\vite.build.config.mjs` | ✅ PASS；项目目录写入受限，输出至 `%TEMP%\gaokao-web-dist` |
| Sprint 7 bundle 预算（临时 outDir） | Temp bundle report over `%TEMP%\gaokao-web-dist\assets` | ✅ PASS；main chunk 133.43 KB gzip，total 382.39 KB gzip |
| Sprint 7 admin a11y 本地守门 | `npm run test -- src/quality/adminA11yCoverage.test.ts src/pages/admin/ErrorPage.test.tsx` | ✅ 2 files / 5 tests |
| Sprint 7 runtime a11y 烟测 | `playwright test "e2e/runtime-accessibility.spec.ts" --project=chromium --output=%TEMP%\gaokao-pw-runtime-a11y` | ✅ 3 Chromium tests passed |
| Sprint 7 i18n 基础回归 | `npm run test -- src/components/shared/LocaleSwitcher.test.tsx src/quality/i18nMessagesCoverage.test.ts src/stores/stores.test.ts` | ✅ 3 files / 13 tests |
| Sprint 7 admin e2e | `playwright test admin-portal.spec.ts --config %TEMP%\gaokao-admin-e2e\playwright.admin-e2e.config.ts` | ✅ 3 Chromium tests passed; command hit timeout during dev-server shutdown |
| TypeScript | `cd apps/web && npm run typecheck` | ✅ PASS |
| ESLint | `cd apps/web && npm run lint` | ✅ PASS / 0 warning |
| Codegen | `cd apps/web && npm run codegen:check` | ✅ PASS |

---

## ⏭️ 下一步候选

- T-D-23 全量文案审计：后台入口、登录、403、Dashboard、订单/案例列表与详情、错误页、全局导航壳层、AboutPage、NotFound/ErrorFallback、Plans 模块、ConsultationsPage、Share 管理模块、PosterPreview 海报模块、DataQuery 数据查询模块、HomePage / FormCard 首页信息收集模块、ReviewFlow / LLMEnhancement / AuditReportCard 审核域、PlanCard / CareerCard / FileUploadPrompt / UploadBar 聊天卡片与上传入口、PortalPage 分享门户页、共享默认组件、Chat / LLM runtime 文案已迁移并加守门；非生成生产源码中文硬编码扫描为 0，剩余中文只在测试夹具、mock 数据和 OpenAPI/codegen 生成产物。
- T-B-25 bundle 预算：2026-07-05 最新 `pnpm run build` 通过；main chunk 146.74 KB gzip，total 393.60 KB gzip，仍低于单 chunk 150 KB / total 500 KB 预算。
- T-E-10 axe / Lighthouse 复测：公共入口 / 数据查询 / 后台入口 Chromium 运行时 a11y 烟测已补；LHCI 本机复测可启动页面但当前 Chrome 临时目录清理触发 EPERM，建议留给 CI 或修复本机 Chrome 临时目录权限后复跑。
- T-E-10 e2e 回归复测：`2194f89` 修复 i18n selector 与 mobile admin nav 回归；targeted 8/8、Chromium 29/29、Chromium + WebKit + mobile-chrome 87/87 通过。Firefox 当前为本机 Playwright `browserContext.newPage` 环境异常，需单独环境复验。
- T-D-24/T-E-11 Chromatic：Admin portal Chromium e2e 已补；Chromatic baseline 仍等待 Storybook/Chromatic 配置与 token。
- T-C-44 Docker 构建验证：等待本机 Docker 可用后继续。
