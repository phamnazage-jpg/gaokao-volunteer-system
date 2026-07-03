# Sprint 4 任务拆解（W6-7 · 14 人天 · 50 子任务）

> **主任务**：T-B-18 ~ T-B-21, T-B-22 ~ T-B-27（持久化/e2e/LH/bundle/prefetch/回归）+ T-B-40 ~ T-B-43 + T-C-44, T-C-45
> **目标**：错误/兜底/离线/防重 + 性能优化 + 监控收口
> **闸门**：G3（Lighthouse P75 ≥ 90）+ G4（Poster CLI Docker 镜像跑通）

## 0. Sprint 4 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-B-18 | 错误码 → 用户文案映射 | 0.5d | 3 |
| T-B-19 | ErrorBoundary 兜底页 | 0.5d | 3 |
| T-B-20 | 离线检测 + 提示 | 1.0d | 4 |
| T-B-21 | 表单提交防重复 | 0.5d | 3 |
| T-B-22 | TanStack Query 持久化 | 1.0d | 3 |
| T-B-23 | e2e 真实化（8 路径） | 3.0d | 8 |
| T-B-24 | Lighthouse CI 集成 | 1.5d | 4 |
| T-B-25 | Bundle 优化 | 1.0d | 4 |
| T-B-26 | 路由级 prefetch | 0.5d | 2 |
| T-B-27 | 真实后端回归 | 0.5d | 2 |
| T-B-40 | Share Link 状态面板数据 | 0.5d | 3 |
| T-B-41 | ShareLink 失败降级 | 0.5d | 3 |
| T-B-42 | LLM 增强进度轮询 | 1.0d | 4 |
| T-B-43 | Poster 异步生成 + 轮询 | 0.5d | 3 |
| T-C-44 | Poster CLI 部署集成 | 1.0d | 4 |
| T-C-45 | 集成测试套件 | 0d | 2 |
| **合计** | **16 任务** | **12d + 缓冲 2d = 14d** | **50** |

---

## T-B-18 · 错误码 → 用户文案映射（0.5d · 3 子任务）

### ST-S4-B-18.1 写 `packages/i18n/zh-CN/errors.json`（0.25d）
- **内容**：15 个错误码全覆盖
  - E03001 / E03002 / E03003
  - E04001 / E04002
  - E05001
  - +8 V2 错误码
- **约束**：沿用 `admin/errors/registry.py` 5 字段结构

### ST-S4-B-18.2 写 api-client 拦截器（0.125d）
- **验收**：
  - [ ] 拦截响应 → 查表 → 返回 i18n 文案

### ST-S4-B-18.3 写单测（0.125d）
- **覆盖**：15 错误码各 1 用例

---

## T-B-19 · ErrorBoundary 兜底页（0.5d · 3 子任务）

### ST-S4-B-19.1 写 `apps/web/app/error.tsx`（0.25d）
- **Next 16 error boundary** + 友好提示
- **验收**：
  - [ ] 5xx 错误时显示兜底页

### ST-S4-B-19.2 Sentry 上报（0.125d）
- **API**：`Sentry.captureException(error)`

### ST-S4-B-19.3 写单测（0.125d）
- **覆盖**：throw 错误时显示兜底

---

## T-B-20 · 离线检测 + 提示（1.0d · 4 子任务）

### ST-S4-B-20.1 写 `useOnlineStatus` hook（0.25d）
- **API**：`navigator.onLine` + `online` / `offline` 事件

### ST-S4-B-20.2 顶部黄条提示（0.25d）
- **验收**：
  - [ ] offline → 顶部条
  - [ ] 写操作禁用

### ST-S4-B-20.3 online 恢复自动重试（0.25d）
- **API**：`useMutation` 队列 + `refetchOnReconnect`

### ST-S4-B-20.4 写单测 + e2e（0.25d）

---

## T-B-21 · 表单提交防重复（0.5d · 3 子任务）

### ST-S4-B-21.1 mutation 加 `isPending`（0.125d）
- **覆盖**：所有 mutation

### ST-S4-B-21.2 FormCard 提交按钮禁用（0.25d）
- **验收**：
  - [ ] isPending 时禁用 + 旋转图标

### ST-S4-B-21.3 ChatMessage 修复按钮单次点击禁用（0.125d）

---

## T-B-22 · TanStack Query 持久化（1.0d · 3 子任务）

### ST-S4-B-22.1 接入 `@tanstack/query-persist-client-core`（0.5d）
- **存储**：localStorage
- **验收**：
  - [ ] 关闭浏览器再打开 → 历史消息立即可见

### ST-S4-B-22.2 后台 revalidate（0.25d）
- **API**：`staleTime: 5min` + `refetchOnMount: 'always'`

### ST-S4-B-22.3 写单测（0.25d）

---

## T-B-23 · e2e 真实化（8 路径，3.0d · 8 子任务）

### ST-S4-B-23.1 `chat-send.spec.ts`（0.25d）
- **验收**：1s 用户气泡 + 3s AI 回复 + 失败场景

### ST-S4-B-23.2 `chat-history.spec.ts`（0.25d）

### ST-S4-B-23.3 `plan-save.spec.ts`（0.5d）

### ST-S4-B-23.4 `audit-upload.spec.ts`（0.5d）

### ST-S4-B-23.5 `theme-persist.spec.ts`（0.25d）

### ST-S4-B-23.6 🆕 `share-link.spec.ts`（0.5d）
- **覆盖**：创建 / 撤销 / 分享 UI

### ST-S4-B-23.7 🆕 `data-query.spec.ts`（0.5d）
- **覆盖**：4 查询页

### ST-S4-B-23.8 🆕 `review-flow.spec.ts`（0.5d）
- **覆盖**：复核全流程

**验收**：
- [ ] 8 spec 全绿
- [ ] 每个 spec 含 1 失败场景

---

## T-B-24 · Lighthouse CI 集成（1.5d · 4 子任务）

### ST-S4-B-24.1 写 `lighthouserc.json`（0.5d）
- **预算**：
  - LCP < 2.5s / INP < 200ms / CLS < 0.1
  - Performance ≥ 90 / Accessibility ≥ 95 / Best Practices ≥ 95 / SEO ≥ 90

### ST-S4-B-24.2 配 GitHub Action（0.5d）
- **覆盖页面**（12 个）：/ /consultations /plans /plans/compare /assessment /score-line-query /rank-estimator /majors-query /schools-query /review/start /admin/login /admin

### ST-S4-B-24.3 PR 评论显示分数（0.25d）

### ST-S4-B-24.4 验证 12 页 P75（0.25d）
- **G3 闸门**

---

## T-B-25 · Bundle 优化（1.0d · 4 子任务）

### ST-S4-B-25.1 `next/dynamic` 异步加载（0.25d）
- **目标组件**：PlanCard / AuditReportCard / CareerCard

### ST-S4-B-25.2 `react-markdown` 异步 chunk（0.25d）

### ST-S4-B-25.3 拆 vendor chunk（0.25d）
- **验收**：
  - [ ] First load JS < 200KB
  - [ ] PlanCard chunk < 50KB

### ST-S4-B-25.4 验证（0.25d）

---

## T-B-26 · 路由级 prefetch（0.5d · 2 子任务）

### ST-S4-B-26.1 `<Link prefetch>` 关键路径（0.25d）
- **目标**：/consultations /plans /assessment

### ST-S4-B-26.2 验证 hover 100ms（0.25d）

---

## T-B-27 · 真实后端回归（0.5d · 2 子任务）

### ST-S4-B-27.1 完整 e2e 套件（0.25d）
- **验收**：
  - [ ] 15+ e2e spec 全绿

### ST-S4-B-27.2 3 浏览器回归（0.25d）
- **覆盖**：chromium / webkit / firefox

---

## T-B-40 · Share Link 状态面板数据（0.5d · 3 子任务）

### ST-S4-B-40.1 写 `useShareStatusPanel(resourceId)`（0.25d）
- **API**：latest + stats 双 query

### ST-S4-B-40.2 30s 自动刷新（0.125d）
- **依据**：test_share_status_panel.py 期望

### ST-S4-B-40.3 写单测（0.125d）

---

## T-B-41 · ShareLink 失败降级（0.5d · 3 子任务）

### ST-S4-B-41.1 `navigator.share` 不可用降级（0.25d）
- **降级路径**：navigator.share → clipboard.writeText → `<a download>`

### ST-S4-B-41.2 3 路径测试（0.125d）

### ST-S4-B-41.3 用户明确提示（0.125d）

---

## T-B-42 · LLM 增强进度轮询（1.0d · 4 子任务）

### ST-S4-B-42.1 `useLLMEnhancement` + SSE 优先（0.25d）
- **依据**：commit `11fbb59`

### ST-S4-B-42.2 长任务进度条（0.25d）
- **触发**：> 30s

### ST-S4-B-42.3 失败降级到基础结果（0.25d）
- **验收**：
  - [ ] 显示"AI 增强暂不可用，已展示基础结果"

### ST-S4-B-42.4 SSE 断开重连 3 次（0.25d）

---

## T-B-43 · Poster 异步生成 + 轮询（0.5d · 3 子任务）

### ST-S4-B-43.1 写 `usePoster` + 进度条（0.25d）
- **验收**：
  - [ ] 5-10s 内完成

### ST-S4-B-43.2 自动下载（可选）（0.125d）

### ST-S4-B-43.3 失败可重试（0.125d）

---

## T-C-44 · Poster CLI 部署集成（1.0d · 4 子任务）

### ST-S4-C-44.1 crontab 配置（0.25d）
- **时间**：每日 02:00
- **验收**：
  - [ ] crontab 配置生效

### ST-S4-C-44.2 产物上传 CDN（0.25d）

### ST-S4-C-44.3 失败告警 Sentry（0.25d）
- **G4 闸门**：Docker 化验证

### ST-S4-C-44.4 日志可查（0.25d）

---

## T-C-45 · 集成测试套件（0d · 2 子任务）

### ST-S4-C-45.1 写 FastAPI + Next.js 双服务集成测试（0d - 复用 S2 测试基础设施）
- **场景**：5 关键场景
- **依据**：commit `a8b4927` integration_test.py

### ST-S4-C-45.2 CI 卡点（0d）
- **集成**：T-A-23 web-ci.yml

---

## Sprint 4 收口验收

- [ ] 16 主任务 / 50 子任务全部完成
- [ ] **G3 通过**：Lighthouse 12 页 P75 ≥ 90
- [ ] **G4 通过**：Poster CLI Docker 镜像跑通
- [ ] Bundle < 200KB
- [ ] 8 e2e spec 全绿
- [ ] 进入 Sprint 5 前 commit：`<feat(s4): error+offline+perf+monitoring>`
