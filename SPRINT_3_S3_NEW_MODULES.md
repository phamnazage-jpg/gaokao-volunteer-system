# Sprint 3 任务拆解（W4-5 · 12 人天 · 62 子任务）— V10 选项 B

> **技术栈**：Vite 5 + React 19 + Zustand 4 + TanStack Query 5 + RHF 7 + Zod
> **目标**：5 大 V2 新模块（Share / Query / Review / LLM / Poster）+ Share Link 统计 + Portal 集成
> **闸门**：G2（LLM fallback 4 模实测可切换 + 5 模块端到端跑通）
> **V10 变化**：从 22d 缩到 12d（节省 10d = 8 hook 真实化用 TanStack Query 替代 + 5 模块统一模式）
> **PM 决策（2026-07-03）**：整体重写为新实现；Playwright 视觉回归 + Chromatic 验收

---

## ⚠️ V10 关键变化（与 V2 对比）

| 维度 | V2 | V10 选项 B |
|---|---|---|
| useChat 拆 6 子 hook | 1.5d | **0.5d**（V10 已用 Zustand 替代，S3 只需补 mock） |
| 真实 sendMessage | 1.0d | **0.5d**（TanStack Query mutation + Zod） |
| useAudit + LLM 增强 | 1.5d | **0.75d**（Zustand + mutation hook） |
| 5 大新模块 | 14d | **8d**（统一 TanStack Query 模式） |
| 视觉回归 | 0d | **+1d**（V10 Chromatic 验证） |
| 总估时 | 22d | **12d** |

---

## 0. Sprint 3 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-B-12 | useChatOrchestrator（V10 重写） | 0.5d | 3 |
| T-B-13 | 真实 sendMessage + typing | 0.5d | 3 |
| T-B-14 | 真实 getHistory + 滚动恢复 | 0.5d | 3 |
| T-B-15 | usePlan/useConsultation 真实化 | 0.75d | 4 |
| T-B-16 | useProfile Zustand 版 | 0.5d | 3 |
| T-B-17 | useAudit + LLM 增强（4 模 fallback） | 0.75d | 4 |
| T-B-22 | Share Link API（4 端点） | 0.75d | 4 |
| T-B-23 | Data Query API（3 端点） | 0.75d | 4 |
| T-B-24 | Review Flow API（3 端点） | 0.75d | 4 |
| T-B-25 | Portal API（2 端点） | 0.5d | 3 |
| T-B-26 | LLM Audit Enhance API | 0.75d | 4 |
| T-B-27 | Poster Generate API | 0.5d | 3 |
| T-B-28 | Share Link 统计 + 分享 UI | 1.0d | 5 |
| T-B-29 | Chromatic 视觉回归（S3 增量） | 0.5d | 3 |
| T-B-30 | ESLint 0 warning 守门（V10 重写） | 0.5d | 3 |
| **合计** | **15 任务** | **9.5d + 缓冲 2.5d = 12d** | **56 + 6 整合 = 62** |

---

## T-B-12 · useChatOrchestrator（V10 重写 · 0.5d · 3 子任务）⚠️ V10 简化

> **V10 收益**：Sprint 2 已建立 Zustand store + TanStack Query，S3 只需组装编排层

### ST-S3-B-12.1 写 chat-fixtures（0.25d）
- **产出**：`apps/web/__mocks__/chat-fixtures.ts`
- **3 套 mock**：广东物理 620 / 广东历史 580 / 河北物理 600

### ST-S3-B-12.2 写 `useChatOrchestrator`（0.125d）
- **产出**：`apps/web/src/hooks/useChatOrchestrator.ts`
- **职责**：Zustand messages + TanStack Query mutation + Typing 状态机
- **V10 收益**：从 1.5d（V2 拆 6 子 hook）→ 0.125d

### ST-S3-B-12.3 接入 8 个 UI 组件（0.125d）
- **覆盖**：MessageList / InputBar / TypingIndicator / PlanCard / ModeIndicator / 等

---

## T-B-13 · 真实 sendMessage + typing（0.5d · 3 子任务）

### ST-S3-B-13.1 写 `useChatSendMutation`（0.25d）
- **封装**：`POST /api/chat/send` + SSE 流式响应
- **类型**：`z.infer<typeof ChatSendSchema>`

### ST-S3-B-13.2 写 `useTypingState` Zustand selector（0.125d）
- **三态**：thinking（旋转）/ paused（静止）/ stopped（隐藏）

### ST-S3-B-13.3 接入 InputBar 真实点击发送（0.125d）
- **验收**：
  - [ ] 点击发送 → 流式输出 → typing 状态切换正确
  - [ ] `any` 数量 0

---

## T-B-14 · 真实 getHistory + 滚动恢复（0.5d · 3 子任务）

### ST-S3-B-14.1 写 `useChatHistoryQuery`（0.125d）
- **封装**：`GET /api/chat/history?sessionId=xxx`
- **缓存策略**：`staleTime: 5min` + `gcTime: 30min`

### ST-S3-B-14.2 写滚动恢复 hook（0.25d）
- **产出**：`useScrollRecovery(ref, [messages.length])`
- **行为**：sessionId 变化时滚到底部；用户上滑时不打断
- **V10 不变量**：UI 1:1 复现（V2 Plan §3.1 L1）

### ST-S3-B-14.3 接入 ChatPanel 组件（0.125d）

---

## T-B-15 · usePlan/useConsultation 真实化（0.75d · 4 子任务）

### ST-S3-B-15.1 写 `usePlanQuery`（0.125d）
### ST-S3-B-15.2 写 `usePlanCreateMutation`（0.25d）
### ST-S3-B-15.3 写 `useConsultationQuery` + `useConsultationMutation`（0.25d）
### ST-S3-B-15.4 接入 PlanCard 真实数据（0.125d）
- **V10 不变量 C1**：PlanCard 3-Tab 切换不重渲染父组件

---

## T-B-16 · useProfile Zustand 版（0.5d · 3 子任务）⚠️ V10 简化

### ST-S3-B-16.1 写 `useUserStore` Zustand（0.25d）
- **V10 收益**：从 1.0d（V2 真实 useProfile）→ 0.25d

### ST-S3-B-16.2 接入 Header 头像/菜单（0.125d）

### ST-S3-B-16.3 接入 Settings 页面（0.125d）

---

## T-B-17 · useAudit + LLM 增强（4 模 fallback · 0.75d · 4 子任务）

> **G2 闸门核心**：LLM 4 模（claude / gpt / gemini / deepseek）实测可切换

### ST-S3-B-17.1 写 LLM provider 适配器（0.25d）
- **产出**：`apps/web/src/lib/llm/provider.ts`
- **4 provider 类型**：`ClaudeProvider` / `GPTProvider` / `GeminiProvider` / `DeepseekProvider`
- **接口**：`enhance(input: AuditInput): Promise<AuditEnhancement>`

### ST-S3-B-17.2 写 `useAuditEnhanceMutation`（0.25d）
- **封装**：`POST /api/llm/audit-enhance` + provider 选择
- **降级链**：claude → gpt → gemini → deepseek

### ST-S3-B-17.3 写 `useLLMConfig` Zustand store（0.125d）
- **状态**：currentProvider / fallbackOrder / availableProviders

### ST-S3-B-17.4 4 模实测切换（0.125d）
- **验收（G2）**：
  - [ ] claude 失败 → 自动降级 gpt
  - [ ] gpt 失败 → 自动降级 gemini
  - [ ] 全部失败 → 走 deepseek
  - [ ] Playwright e2e 覆盖

---

## T-B-22 · Share Link API（4 端点 · 0.75d · 4 子任务）

### ST-S3-B-22.1 写 `useShareLinkCreate`（0.25d）
- **封装**：`POST /api/share-link`
- **Schema**：`{ planId, expiresIn: 7|30|forever }`

### ST-S3-B-22.2 写 `useShareLinkDelete`（0.125d）
- **封装**：`DELETE /api/share-link/{id}`

### ST-S3-B-22.3 写 `useShareLinkLatestQuery`（0.125d）
- **封装**：`GET /api/portal/share-link/latest`

### ST-S3-B-22.4 写 `useShareLinkStatsQuery`（0.25d）
- **封装**：`GET /api/share-link/{code}/stats`
- **响应**：`{ views, uniqueVisitors, lastAccessedAt }`

---

## T-B-23 · Data Query API（3 端点 · 0.75d · 4 子任务）

### ST-S3-B-23.1 写 `useScoreLineQuery`（0.25d）
- **封装**：`GET /api/data-query/score-line`
- **参数**：`{ province, year, scoreType }`

### ST-S3-B-23.2 写 `useRankEstimatorQuery`（0.25d）
- **封装**：`GET /api/data-query/rank-estimator`
- **V10 变化**：TanStack Query `select` 直接转换位次→等效分数

### ST-S3-B-23.3 写 `useMajorsQuery` + `useSchoolsQuery`（0.25d）
- **封装**：`GET /api/data-query/majors` + `GET /api/data-query/schools`

---

## T-B-24 · Review Flow API（3 端点 · 0.75d · 4 子任务）

### ST-S3-B-24.1 写 `useReviewStartMutation`（0.25d）
- **封装**：`POST /api/review/start`

### ST-S3-B-24.2 写 `useReviewStatusQuery`（0.125d）
- **封装**：`GET /api/review/{id}/status`
- **轮询**：`refetchInterval: 3000`（审核中）

### ST-S3-B-24.3 写 `useReviewActionMutation`（0.25d）
- **封装**：`POST /api/review/action`（approve / reject / request_changes）
- **V10 变化**：Zod discriminated union 处理 3 种 action

### ST-S3-B-24.4 接入 ReviewPanel UI（0.125d）

---

## T-B-25 · Portal API（2 端点 · 0.5d · 3 子任务）

### ST-S3-B-25.1 写 `usePortalCWBQuery`（0.25d）
- **封装**：`GET /api/portal/{token}/cwb`（位次查询）

### ST-S3-B-25.2 写 `usePortalFullPlanQuery`（0.125d）
- **封装**：`GET /api/portal/{token}/full-plan`

### ST-S3-B-25.3 写 Portal 入口页面（0.125d）
- **UI/交互 1:1**：与原型招生门户入口一致

---

## T-B-26 · LLM Audit Enhance API（0.75d · 4 子任务）

### ST-S3-B-26.1 写 `useAuditEnhanceMutation`（0.25d）
- **封装**：`POST /api/llm/audit-enhance`

### ST-S3-B-26.2 写流式响应处理（0.25d）
- **V10 关键技术**：SSE + ReadableStream + Zustand 增量更新
- **复用**：`useChatSendMutation` 的流式逻辑

### ST-S3-B-26.3 写 LLM 结果展示组件（0.125d）

### ST-S3-B-26.4 接入 AuditPanel UI（0.125d）

---

## T-B-27 · Poster Generate API（0.5d · 3 子任务）

### ST-S3-B-27.1 写 `usePosterGenerateMutation`（0.25d）
- **封装**：`POST /api/poster/generate`
- **响应**：`{ posterUrl, qrCode, expiresAt }`

### ST-S3-B-27.2 写海报预览组件（0.125d）
- **V10 视觉**：海报需与原型的视觉风格一致

### ST-S3-B-27.3 接入 ShareDialog UI（0.125d）

---

## T-B-28 · Share Link 统计 + 分享 UI（1.0d · 5 子任务）⚠️ V10 加强

> **V10 加强**：5 个子任务覆盖 UI + 统计图表 + 移动端适配

### ST-S3-B-28.1 写 ShareDialog 组件（0.25d）
- **UI/交互 1:1**：与原型分享弹窗一致
- **V10 不变量**：移动端 48px 触发区

### ST-S3-B-28.2 写 QR Code 展示组件（0.125d）
- **依赖**：`qrcode.react`

### ST-S3-B-28.3 写 Stats 统计卡片（0.25d）
- **3 卡片**：访问数 / 独立访客 / 最近访问
- **图标**：lucide-react

### ST-S3-B-28.4 写访问趋势 mini chart（0.25d）
- **依赖**：`recharts`
- **V10 收益**：Sprint 5 chart 任务的预演

### ST-S3-B-28.5 写 e2e：share-link.spec（0.125d）

---

## T-B-29 · Chromatic 视觉回归（S3 增量 · 0.5d · 3 子任务）⚠️ V10 新增

### ST-S3-B-29.1 截图新增 5 模块页面（0.25d）
- **页面**：ShareDialog / Stats / DataQuery / ReviewPanel / Poster Preview

### ST-S3-B-29.2 提交 Chromatic 增量基线（0.125d）

### ST-S3-B-29.3 Chromatic diff 阈值告警（0.125d）
- **CI**：`pnpm chromatic --exit-zero-on-changes`

---

## T-B-30 · ESLint 0 warning 守门（V10 重写 · 0.5d · 3 子任务）

> **V10 关键**：S3 完成后 ESLint 必须 0 warning（V2 是 49 warning 缓慢修）

### ST-S3-B-30.1 清理 S3 引入的 any（0.25d）
- **验收**：`grep -r "any" apps/web/src/` 0 结果

### ST-S3-B-30.2 清理 S3 引入的 unused vars（0.125d）

### ST-S3-B-30.3 升级 Sprint 1 临时 warn 规则为 error（0.125d）
- **规则**：`@typescript-eslint/no-explicit-any` / `react-hooks/set-state-in-effect`
- **目的**：阻止 Sprint 4-8 倒退

---

## V10 验收清单（Sprint 3 G2 闸门）

```
G2 闸门（必须全部通过）：
  [ ] 5 大新模块端到端跑通（Share / Query / Review / LLM / Poster）
  [ ] LLM 4 模实测可切换 + 自动降级
  [ ] pnpm typecheck 0 error 0 any
  [ ] pnpm lint 0 error 0 warning
  [ ] pnpm test 100% 覆盖新增 56 个子任务相关组件
  [ ] pnpm test:e2e 5 spec 全绿
  [ ] pnpm build bundle < 320KB gzip（+20KB for new modules）
  [ ] pnpm chromatic 视觉基线 13 页全提交
  [ ] 原型 7 个手写 hook + 1 个 lib/ 全部删除
  [ ] ESLint 0 warning（V2 是 49 warning 修 1 整轮）
```

---

## V10 风险（Sprint 3 特有）

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| V10-S3-R1 | LLM 4 模 provider 适配成本高 | 中 | 抽象统一接口；先实现 1 模，再快速复制 3 模 |
| V10-S3-R2 | SSE 流式响应与 TanStack Query 兼容 | 中 | 用 `onMutate` + Zustand 增量更新，绕过 React Query 的缓存机制 |
| V10-S3-R3 | 5 新模块并发开发协调 | 中 | 串行实施：T-B-22 → T-B-23 → T-B-24 → T-B-26 → T-B-27 |
| V10-S3-R4 | Chromatic 商业服务配额 | 低 | Sprint 2 已用 1 次，S3 再用 1 次，剩余 8 次给 S4-S8 |

---

**Sprint 3 文档状态**：V10 选项 B 重写完成
**总工时**：12 人天（V2 是 22 人天，节省 10d）
**总子任务**：62 个（V2 是 70 个）
**下一步**：Sprint 2 完成后立即启动
