# Sprint 3 任务拆解（W4-5 · 22 人天 · 70 子任务）

> **主任务**：T-B-12 ~ T-B-17, T-B-22 ~ T-B-39（22 任务）
> **目标**：8 hook 真实化 + 5 大 V2 新模块 API 对接
> **闸门**：G2（LLM fallback 4 模实测可切换）

## 0. Sprint 3 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-B-12 | 拆 useChat 编排层 | 1.5d | 4 |
| T-B-13 | 真实 sendMessage + typing | 1.0d | 4 |
| T-B-14 | 真实 getHistory + 滚动恢复 | 1.0d | 4 |
| T-B-15 | usePlan/useConsultation 真实化 | 1.5d | 5 |
| T-B-16 | 真实 useProfile | 1.0d | 4 |
| T-B-17 | 真实 useAudit + LLM 增强 | 1.5d | 5 |
| T-B-22 | `POST /api/share-link` | 0.5d | 3 |
| T-B-23 | `DELETE /api/share-link/{id}` | 0.25d | 2 |
| T-B-24 | `GET /api/portal/share-link/latest` | 0.25d | 2 |
| T-B-25 | `GET /api/share-link/{code}/stats` | 0.5d | 3 |
| T-B-26 | `GET /api/data-query/score-line` | 0.5d | 3 |
| T-B-27 | `GET /api/data-query/rank-estimator` | 0.5d | 3 |
| T-B-28 | `GET /api/data-query/majors` + `schools` | 0.5d | 3 |
| T-B-29 | `POST /api/review/start` | 0.5d | 3 |
| T-B-30 | `GET /api/review/{id}/status` | 0.25d | 2 |
| T-B-31 | `POST /api/review/action` | 0.5d | 3 |
| T-B-32 | `GET /api/portal/{token}/cwb` | 0.5d | 3 |
| T-B-33 | `GET /api/portal/{token}/full-plan` | 0.5d | 3 |
| T-B-34 | `POST /api/llm/audit-enhance` | 1.0d | 4 |
| T-B-35 | `POST /api/poster/generate` | 0.5d | 3 |
| **合计** | **20 主任务** | **15d + 缓冲 7d = 22d** | **70** |

---

## T-B-12 · 拆 useChat 编排层（1.5d · 4 子任务）

### ST-S3-B-12.1 抽 chat-fixtures（0.5d）
- **产出**：`apps/web/__mocks__/chat-fixtures.ts`
- **3 套 mock**：广东省物理 620、广东省历史 580、河北省物理 600
- **验收**：
  - [ ] useChat.ts < 300 行（**R-NEW-1**）

### ST-S3-B-12.2 拆 useChat 为 6 子 hook（0.5d）
- **产出**：
  - `useMessageList` —— 消息列表
  - `useSendMessage` —— 发送
  - `useTypingIndicator` —— typing 动画
  - `useHistoryFetch` —— 历史
  - `useScrollRecovery` —— 滚动恢复
  - `useChatOrchestrator` —— 编排
- **验收**：
  - [ ] 6 子 hook 独立单测

### ST-S3-B-12.3 改 useChat 为纯编排（0.25d）
- **验收**：
  - [ ] 无 mock 数据依赖
  - [ ] 0 个 `console.log`

### ST-S3-B-12.4 写编排层单测（0.25d）
- **覆盖**：5 场景切换 consultation

---

## T-B-13 · 真实 sendMessage + typing 动画（1.0d · 4 子任务）

### ST-S3-B-13.1 mutation + optimistic update（0.25d）
- **API**：`useMutation` 立即插入用户消息

### ST-S3-B-13.2 失败回滚 + Toast（0.25d）
- **验收**：
  - [ ] 失败时乐观更新回滚

### ST-S3-B-13.3 typing 动画保留（0.25d）
- **位置**：`page.tsx:173-186`
- **验收**：
  - [ ] 视觉与原型一致（**§1.3 约束**）

### ST-S3-B-13.4 e2e `chat-send.spec.ts`（0.25d）
- **验收**：
  - [ ] 输入消息 → 1s 内用户气泡 → 3s 内 AI 回复
  - [ ] 失败场景覆盖

---

## T-B-14 · 真实 getHistory + 滚动恢复（1.0d · 4 子任务）

### ST-S3-B-14.1 useQuery 拉历史（0.25d）
- **触发**：consultation_id 变化时 refetch

### ST-S3-B-14.2 自动滚动到底部（0.25d）
- **API**：`useEffect` + `messagesEndRef.current?.scrollIntoView()`

### ST-S3-B-14.3 Skeleton 加载态（0.25d）
- **复用**：T-D-06 阶段组件（Sprint 5 完成，先用占位）

### ST-S3-B-14.4 写 e2e（0.25d）
- **产出**：`chat-history.spec.ts`
- **验收**：
  - [ ] 切换 consultation_id → 加载历史

---

## T-B-15 · usePlan / useConsultation 真实化（1.5d · 5 子任务）

### ST-S3-B-15.1 删 useChat 中 localStorage 写（0.25d）
- **验收**：
  - [ ] `useChat.ts` 无 localStorage.setItem

### ST-S3-B-15.2 改用 `apiClient.plans.create` mutation（0.25d）

### ST-S3-B-15.3 保留 key 名兼容（0.25d）
- **保留**：`consultationRecords` / `activeConsultationId` / `savedPlans` / `userPreferences`（**R-NEW-2**）
- **验收**：
  - [ ] 断网时本地仍可见上次同步数据

### ST-S3-B-15.4 联网自动 revalidate（0.25d）
- **API**：TanStack Query `refetchOnReconnect: true`

### ST-S3-B-15.5 写单测 + e2e（0.5d）
- **覆盖**：保存方案 → DB 可见

---

## T-B-16 · 真实 useProfile（1.0d · 4 子任务）

### ST-S3-B-16.1 `GET /api/profile`（0.25d）

### ST-S3-B-16.2 `PATCH /api/profile` mutation（0.25d）

### ST-S3-B-16.3 FormCard 提交进度条（0.25d）
- **复用**：`InfoCollectionProgress` 组件

### ST-S3-B-16.4 失败回滚（0.25d）

---

## T-B-17 · 真实 useAudit + LLM 增强（1.5d · 5 子任务）

### ST-S3-B-17.1 multipart upload 真实化（0.25d）
- **4 类型**：Excel/Image/PDF/Paste

### ST-S3-B-17.2 进度条（0.25d）
- **双段**：上传 + AI 处理

### ST-S3-B-17.3 E04001 错误处理（0.25d）
- **验收**：
  - [ ] 上游 AI 失败 → Toast 重试

### ST-S3-B-17.4 LLM 增强异步触发（0.5d）
- **API**：`useLLMEnhancement(auditReportId)`
- **验收**：
  - [ ] 异步追加到 report（不阻塞主结果）

### ST-S3-B-17.5 写 e2e（0.25d）
- **产出**：`audit-upload.spec.ts`

---

## T-B-22 ~ T-B-35（V2 新增 14 端点 · 30 子任务 · 6.5d）

> 以下每个端点统一 3 子任务模板：
> - 对接 OpenAPI 类型（0.125d）
> - 写调用层 / hook（0.25d）
> - 写单测 + e2e 草稿（0.125d）

### T-B-22 `POST /api/share-link`（0.5d · 3 子任务）
- ST-S3-B-22.1 对接 OpenAPI（0.125d）
- ST-S3-B-22.2 `useCreateShareLink` mutation（0.25d）
- ST-S3-B-22.3 写单测（0.125d）

### T-B-23 `DELETE /api/share-link/{id}`（0.25d · 2 子任务）
- ST-S3-B-23.1 写 `useRevokeShareLink` mutation（0.125d）
- ST-S3-B-23.2 写单测（0.125d）

### T-B-24 `GET /api/portal/share-link/latest`（0.25d · 2 子任务）
- ST-S3-B-24.1 写 `useLatestShareLink` query（0.125d）
- ST-S3-B-24.2 写单测（0.125d）

### T-B-25 `GET /api/share-link/{code}/stats`（0.5d · 3 子任务）
- ST-S3-B-25.1 写 `useShareStats` query（0.25d）
- ST-S3-B-25.2 30s 自动刷新（0.125d）
- ST-S3-B-25.3 写单测（0.125d）

### T-B-26 `GET /api/data-query/score-line`（0.5d · 3 子任务）
- ST-S3-B-26.1 写 `useScoreLineQuery`（0.25d）
- ST-S3-B-26.2 缓存 5min（0.125d）
- ST-S3-B-26.3 写单测（0.125d）

### T-B-27 `GET /api/data-query/rank-estimator`（0.5d · 3 子任务）
- ST-S3-B-27.1 写 `useRankEstimator`（0.25d）
- ST-S3-B-27.2 写单测（0.125d）
- ST-S3-B-27.3 性能验证（< 200ms）（0.125d）

### T-B-28 `GET /api/data-query/majors` + `schools`（0.5d · 3 子任务）
- ST-S3-B-28.1 写 `useMajorsQuery` + `useSchoolsQuery`（0.25d）
- ST-S3-B-28.2 分页 + 搜索（0.125d）
- ST-S3-B-28.3 写单测（0.125d）

### T-B-29 `POST /api/review/start`（0.5d · 3 子任务）
- ST-S3-B-29.1 写 `useStartReview` mutation（0.25d）
- ST-S3-B-29.2 异步触发 LLM（0.125d）
- ST-S3-B-29.3 写单测（0.125d）

### T-B-30 `GET /api/review/{id}/status`（0.25d · 2 子任务）
- ST-S3-B-30.1 写 `useReviewStatus`（轮询 2s）（0.125d）
- ST-S3-B-30.2 写单测（0.125d）

### T-B-31 `POST /api/review/action`（0.5d · 3 子任务）
- ST-S3-B-31.1 写 `useReviewAction` mutation（0.25d）
- ST-S3-B-31.2 3 action 类型（approve/reject/revise）（0.125d）
- ST-S3-B-31.3 写单测（0.125d）

### T-B-32 `GET /api/portal/{token}/cwb`（0.5d · 3 子任务）
- ST-S3-B-32.1 写 `useCWB` query（0.25d）
- ST-S3-B-32.2 字段对齐 PlanCard（**§1.5 约束**）（0.125d）
- ST-S3-B-32.3 写单测（0.125d）

### T-B-33 `GET /api/portal/{token}/full-plan`（0.5d · 3 子任务）
- ST-S3-B-33.1 写 `useFullPlan` query（0.25d）
- ST-S3-B-33.2 含 LLM 增强（0.125d）
- ST-S3-B-33.3 写单测（0.125d）

### T-B-34 `POST /api/llm/audit-enhance`（1.0d · 4 子任务）
- ST-S3-B-34.1 写 `useLLMEnhancement` mutation（0.25d）
- ST-S3-B-34.2 多模型 fallback（commit `11fbb59`）（0.25d）
- ST-S3-B-34.3 30s 超时降级（**R-NEW-7**）（0.25d）
- ST-S3-B-34.4 写单测（0.25d）
- **G2 闸门**：4 模实测可切换

### T-B-35 `POST /api/poster/generate`（0.5d · 3 子任务）
- ST-S3-B-35.1 写 `useGeneratePoster` mutation（0.25d）
- ST-S3-B-35.2 3 模板支持（0.125d）
- ST-S3-B-35.3 写单测（0.125d）

---

## T-B-36 ~ T-B-39（V2 4 个 hook · 14 子任务 · 4.5d）

### T-B-36 useShareLink Hook（1.0d · 4 子任务）
- ST-S3-B-36.1 写 useShareLink（创建/撤销/刷新）（0.5d）
- ST-S3-B-36.2 QR 码集成 `qrcode.react`（0.25d）
- ST-S3-B-36.3 写单测（0.125d）
- ST-S3-B-36.4 写 e2e（0.125d）

### T-B-37 useDataQuery Hook（4 独立 hook，1.5d · 5 子任务）
- ST-S3-B-37.1 useScoreLineQuery（0.25d）
- ST-S3-B-37.2 useRankEstimator（0.25d）
- ST-S3-B-37.3 useMajorsQuery + useSchoolsQuery（0.5d）
- ST-S3-B-37.4 staleTime 5min + 错误降级（0.25d）
- ST-S3-B-37.5 写单测（0.25d）

### T-B-38 useReview Hook（1.5d · 4 子任务）
- ST-S3-B-38.1 写 useReview（start/poll/action）（0.5d）
- ST-S3-B-38.2 SSE 优先 + 轮询降级（0.5d）
- ST-S3-B-38.3 进度 100% 跳转（0.25d）
- ST-S3-B-38.4 写单测 + e2e（0.25d）

### T-B-39 usePoster Hook（0.5d · 3 子任务）
- ST-S3-B-39.1 写 usePoster（0.25d）
- ST-S3-B-39.2 进度显示（5-10s）（0.125d）
- ST-S3-B-39.3 写单测（0.125d）

---

## Sprint 3 收口验收

- [ ] 20 主任务 / 70 子任务全部完成
- [ ] **G2 通过**：LLM fallback 4 模实测可切换
- [ ] 22 端点全部对接
- [ ] 8 hook 全部真实化
- [ ] 进入 Sprint 4 前 commit：`<feat(s3): 5 v2 modules + 8 hooks + llm fallback>`
