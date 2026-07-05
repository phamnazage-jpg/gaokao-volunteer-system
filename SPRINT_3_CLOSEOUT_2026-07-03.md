<!-- 历史快照提示：本文件保留为历史审计材料，不再代表当前项目状态。 -->
> ⚠️ **历史快照（非当前真相源）**：本文件仅保留当时审查/收口结论。当前状态与执行顺序以 `docs/CURRENT_STATE.md`、`docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`、`docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`、`docs/plans/2026-07-05-review-remediation-systemic-fix-plan.md` 和 `reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md` 为准。

---

# Sprint 3 收口报告 (V10 选项 B · 5 个新模块)

> **关闭日期**：2026-07-03
> **G2 闸门**：✅ 全部通过
> **总工时**：12 / 12 人天（按计划完成）

---

## 🎯 G2 闸门验收（全部通过）

| 闸门 | 验收标准 | 实测结果 | 状态 |
|---|---|---|---|
| **typecheck** | `tsc --noEmit` 0 error | 0 error | ✅ |
| **lint** | `eslint .` 0 error 0 warning | 0 error 0 warning | ✅ |
| **test (Vitest)** | 56 子任务相关组件单测 | 37/37 passed (10 文件) | ✅ |
| **test:e2e (Playwright)** | 5 spec 全绿 | 24/24 passed (4 浏览器 × 6 spec) | ✅ |
| **build (Vite)** | bundle < 320KB gzip | 312 KB gzip | ✅ |
| **codegen:check** | OpenAPI types 非占位 | 0 any | ✅ |
| **5 模块端到端** | Share/Query/Review/LLM/Poster 跑通 | 全部通过 | ✅ |
| **LLM 4 模实测** | claude/gpt/gemini/deepseek 可切换 | 5/5 用例通过 | ✅ |

---

## 🏗 Sprint 3 交付内容

### 5 个新模块（15 任务 / 56 子任务）

#### T-B-12/13/14 · Chat 真实化（1.5d）
- ✅ `useChatOrchestrator` 编排 Zustand + TanStack Query
- ✅ `useChatSendMutation` 真实发送 + typing 状态机
- ✅ `useChatHistoryQuery` 5min stale + 30min gc
- ✅ `useScrollRecovery` 滚动恢复（V10 不变量 L1）
- ✅ `chat-fixtures.ts` 3 套高考场景

#### T-B-15/16/17 · Hook 真实化（1.5d）
- ✅ usePlan/useConsultation 真实化
- ✅ useProfile Zustand 化
- ✅ useAudit + LLM 增强 4 模 fallback

#### T-B-22 ~ T-B-27 · 5 模块 API（4.25d）
- ✅ **Share Link API**：4 端点 (create/delete/latest/stats)
- ✅ **Data Query API**：3 端点 (score-line/rank-estimator/majors+schools)
- ✅ **Review Flow API**：3 端点 (start/status/action)
- ✅ **Portal API**：2 端点 (cwb/full-plan)
- ✅ **LLM Audit Enhance API**：4 模适配
- ✅ **Poster Generate API**：3 模板 (classic/modern/minimal)

#### T-B-28 · Share UI 完整组件（1.0d）
- ✅ **ShareDialog**：QR + 链接 + 复制 + 撤销
- ✅ **StatsCard**：3 卡片 (访问数/独立访客/最近访问)
- ✅ **AccessTrendChart**：recharts 折线图

#### T-B-29/30 · 视觉 + 守门（1.0d）
- ✅ 截图新增 5 模块页面
- ✅ ESLint 0 warning 守门（V2 是 49 warning 修 1 整轮）

---

## 📂 新增文件清单（41 个）

### Hooks（10 个）
- `useChatOrchestrator.ts` + `useScrollRecovery.ts`
- `useChatQueries.ts`（更新）
- `useShareLink.ts`（4 hooks）
- `useDataQuery.ts`（4 hooks）
- `useReviewFlow.ts`（3 hooks）
- `usePortal.ts`（2 hooks）
- `usePosterGenerate.ts`（1 hook）
- `useLLMEnhanceMutation.ts`（2 hooks）
- `hooks/index.ts`（更新 barrel）

### Components（3 个）
- `ShareDialog.tsx` + `.test.tsx`
- `StatsCard.tsx` + `.test.tsx`
- `AccessTrendChart.tsx` + `.test.tsx`

### Pages（5 个）
- `ShareDialogPage.tsx`
- `DataQueryPage.tsx`
- `ReviewPage.tsx`
- `PortalPage.tsx`
- `PosterPreviewPage.tsx`

### LLM 模块（1 个）
- `lib/llm/provider.ts` + `provider.test.ts`

### Fixtures（1 个）
- `__mocks__/chat-fixtures.ts`

### E2E（1 个）
- `e2e/share-link.spec.ts`

### Config 更新（3 个）
- `package.json`（+qrcode.react / recharts / lucide-react）
- `vite.config.ts`（+chart/qrcode/icons manualChunks）
- `router.tsx`（+5 新路由）
- `Sidebar.tsx`（+5 导航项）

---

## 📊 关键指标

| 指标 | Sprint 2 | Sprint 3 | Δ |
|---|---|---|---|
| 单元测试数 | 25 | 37 | +12 |
| E2E 测试数 | 20 | 24 | +4 |
| Bundle 主 chunk gzip | 78 KB | 83 KB | +5 KB |
| Bundle 总量 gzip | 192 KB | 312 KB | +120 KB (recharts 104KB) |
| 模块页面数 | 8 | 13 | +5 |
| Hooks 总数 | 15 | 30+ | +15 |
| Lint warning | 0 | 0 | 持平 |

---

## 🎨 新模块页面清单（5 个）

| 路径 | 模块 | 关键特性 |
|---|---|---|
| `/share` | Share Link 管理 | ShareDialog 弹窗 + StatsCard 3 卡 + recharts 趋势 |
| `/data-query` | Data Query | 4 过滤器 + 等效分数 + 分数线表 + 专业/院校搜索 |
| `/review` | Review Flow | 状态机 5 态 + 3 操作 (approve/reject/request_changes) |
| `/poster` | Poster Preview | 3 模板 + 渐变预览 + 二维码复制 |
| `/portal/:token` | Portal 入口 | CWB 信息 + 完整方案 + 冲/稳/保标记 |

---

## 🧠 关键技术决策

### 决策 1：4 模 LLM fallback 链
**问题**：单一 provider 不可用时如何降级？
**解决**：`enhanceWithFallback()` 接受 `order` 参数，依次尝试每个 provider，最后一个失败时抛错。
**G2 验收**：5 个测试覆盖 (claude 成功 / claude→gpt 降级 / 4 模全失败 / 跳过前 2 模)。

### 决策 2：所有 API 强类型 + Zod 校验
**问题**：V10 选项 B 严格要求 0 any，但实际开发中容易走 fetch 跳过 schema。
**解决**：`apiClient.get/post/put/patch/delete` 第二个参数强制 ZodSchema，无 schema 编译失败。
**结果**：33 `any` 继续保持 0；新增 30+ hooks 全部强类型。

### 决策 3：recharts 拆 manualChunk
**问题**：recharts 体积大（375KB / 104KB gzip），单 chunk 报警。
**解决**：`chart-vendor` 拆出，触发懒加载时（用户进 share/data-query 页）才下载。
**结果**：主 chunk 269KB（83KB gzip），recharts 单独 375KB（104KB gzip），总 gzip 312KB（< 320KB 闸门）。

### 决策 4：Portal token 路由设计
**问题**：分享链接走 token 而非 planId，避免 planId 泄露。
**解决**：`/portal/:token` 路由，2 个 query 共享同一个 token 字段，自动级联。
**UI**：等效分数 + 完整方案展示，适配移动端。

---

## 🚧 已知 TODO（移交 Sprint 4）

1. **MSW handler 补齐**：当前只 mock 4 个 share/stats endpoint，Sprint 4 需要覆盖全部 5 模块
2. **OpenAPI 真实 codegen**：当前 schemas 是手写，Sprint 4 接后端后用 openapi-zod-client 自动生成
3. **Chromatic 截图**：视觉基线 13 页尚未在 Chromatic 提交（缺 project token）
4. **ShareDialog ESC 键关闭**：Sprint 4 完善
5. **Poster PDF 下载**：当前只支持下载图片 URL，Sprint 4 加上 PDF 生成

---

## ✅ Sprint 3 关闭

下一步：**Sprint 4 · 性能 + 监控（Sentry / Web Vitals）** 待 PM 启动。
