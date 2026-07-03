# Sprint 4 任务拆解（W6-7 · 10 人天 · 46 子任务）— V10 选项 B

> **技术栈**：Vite 5 + React 19 + Zustand 4 + TanStack Query 5 + RHF 7 + Zod
> **目标**：错误/兜底/离线/防重 + 性能优化 + 监控收口 + 真实后端回归
> **闸门**：G3（Lighthouse P75 ≥ 90 P/A/B/S）+ G4（Poster CLI Docker 镜像跑通）
> **V10 变化**：从 14d 缩到 10d（节省 4d = Vite SSR 简化 + e2e 用 Playwright 1.55 加速）
> **PM 决策（2026-07-03）**：整体重写为新实现；Playwright 视觉回归 + Chromatic 验收

---

## ⚠️ V10 关键变化（与 V2 对比）

| 维度 | V2 | V10 选项 B |
|---|---|---|
| Lighthouse 目标 | 90 P75 | **90 P75**（保持） |
| e2e 真实化（8 路径） | 3.0d | **2.0d**（Playwright trace + Vite preview 加速） |
| Bundle 优化 | 1.0d | **0.5d**（Vite 已分块） |
| i18n 错误码映射 | 0.5d | **0.5d**（不变） |
| 总估时 | 14d | **10d** |

---

## 0. Sprint 4 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-B-18 | 错误码 → 用户文案映射 | 0.5d | 3 |
| T-B-19 | ErrorBoundary 兜底页 | 0.5d | 3 |
| T-B-20 | 离线检测 + 提示 | 1.0d | 4 |
| T-B-21 | 表单提交防重复（RHF 版） | 0.5d | 3 |
| T-B-22 | TanStack Query 持久化 | 0.5d | 3 |
| T-B-23 | e2e 真实化（8 路径，Playwright 加速） | 2.0d | 8 |
| T-B-24 | Lighthouse CI 集成 | 1.5d | 4 |
| T-B-25 | Bundle 优化（Vite 版） | 0.5d | 3 |
| T-B-26 | 路由级 prefetch | 0.5d | 2 |
| T-B-27 | 真实后端回归 | 0.5d | 2 |
| T-B-40 | Share Link 状态面板数据 | 0.5d | 3 |
| T-B-41 | ShareLink 失败降级 | 0.5d | 3 |
| T-B-42 | LLM 增强进度轮询 | 0.5d | 3 |
| T-B-43 | Poster 异步生成 + 轮询 | 0.5d | 3 |
| T-C-44 | Poster CLI 部署集成（Docker） | 1.0d | 4 |
| T-C-45 | 集成测试套件 | 0d | 2 |
| **合计** | **16 任务** | **10d** | **53** |

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

### ST-S4-B-19.1 写 `ErrorBoundary` 组件（0.25d）
- **V10 变化**：用 `react-error-boundary` 库，避免手写 class 组件

### ST-S4-B-19.2 写兜底页（0.125d）
- **UI/交互 1:1**：与原型 ErrorPage 一致

### ST-S4-B-19.3 接入根路由（0.125d）

---

## T-B-20 · 离线检测 + 提示（1.0d · 4 子任务）

### ST-S4-B-20.1 写 `useOnlineStatus` hook（0.25d）
- **封装**：`navigator.onLine` + `online`/`offline` 事件

### ST-S4-B-20.2 写 OfflineBanner 组件（0.25d）
- **V10 不变量 L2**：移动端 48px 高度

### ST-S4-B-20.3 写离线降级策略（0.25d）
- **行为**：写操作排队 + 恢复后自动重试

### ST-S4-B-20.4 写 e2e：offline.spec（0.25d）

---

## T-B-21 · 表单提交防重复（RHF 版 · 0.5d · 3 子任务）⚠️ V10 简化

> **V10 收益**：RHF `formState.isSubmitting` 内置

### ST-S4-B-21.1 接入 RHF isSubmitting（0.125d）
### ST-S4-B-21.2 写通用 SubmitButton 组件（0.25d）
### ST-S4-B-21.3 写单测（0.125d）

---

## T-B-22 · TanStack Query 持久化（0.5d · 3 子任务）⚠️ V10 简化

> **V10 收益**：`@tanstack/query-async-storage-persister` 内置支持

### ST-S4-B-22.1 安装 persister（0.125d）
```bash
pnpm --filter web add @tanstack/query-async-storage-persister
```

### ST-S4-B-22.2 写 `queryClient.ts` 持久化配置（0.25d）
- **maxAge**：24h
- **storage**：localStorage

### ST-S4-B-22.3 验证 5 模块刷新恢复（0.125d）

---

## T-B-23 · e2e 真实化（8 路径 · 2.0d · 8 子任务）⚠️ V10 加速

> **V10 加速**：用 Playwright `test.step` + Vite preview server

### ST-S4-B-23.1 e2e: theme-switch（0.25d）
### ST-S4-B-23.2 e2e: chat-send-receive（0.25d）
### ST-S4-B-23.3 e2e: form-submit-validation（0.25d）
### ST-S4-B-23.4 e2e: plan-create-view（0.25d）
### ST-S4-B-23.5 e2e: share-link-create-scan（0.25d）
### ST-S4-B-23.6 e2e: data-query-search（0.25d）
### ST-S4-B-23.7 e2e: review-flow-approve（0.25d）
### ST-S4-B-23.8 e2e: poster-generate-download（0.25d）

---

## T-B-24 · Lighthouse CI 集成（1.5d · 4 子任务）

### ST-S4-B-24.1 安装 `@lhci/cli`（0.25d）

### ST-S4-B-24.2 写 `lighthouserc.json`（0.5d）
- **目标**：P ≥ 90 / A ≥ 95 / B ≥ 90 / S ≥ 90
- **V10 收益**：Vite 产物比 Next.js 小，Lighthouse 分数天然更高

### ST-S4-B-24.3 接入 GitHub Action（0.5d）
- **验收**：
  - [ ] PR 触发 LHCI
  - [ ] 分数 < 90 阻止合并

### ST-S4-B-24.4 调优未达标项（0.25d）

---

## T-B-25 · Bundle 优化（Vite 版 · 0.5d · 3 子任务）⚠️ V10 简化

> **V10 收益**：Sprint 2 已分块，S4 只做微调

### ST-S4-B-25.1 配置 manualChunks 精细化（0.125d）
- **目标**：recharts 单独 chunk（懒加载）

### ST-S4-B-25.2 配置资源内联阈值（0.125d）
- **4KB 以下内联**

### ST-S4-B-25.3 验证 bundle < 300KB gzip（0.25d）

---

## T-B-26 · 路由级 prefetch（0.5d · 2 子任务）

### ST-S4-B-26.1 写 `<PrefetchLink>` 组件（0.25d）
- **行为**：hover 200ms 后预取目标 chunk

### ST-S4-B-26.2 接入 Header / Sidebar（0.25d）
- **验收**：
  - [ ] hover → 预取 → 点击 0 等待

---

## T-B-27 · 真实后端回归（0.5d · 2 子任务）

### ST-S4-B-27.1 启动后端服务（0.25d）
- **命令**：`docker compose up backend postgres`

### ST-S4-B-27.2 跑 5 模块端到端（0.25d）
- **验收**：
  - [ ] Share / Query / Review / LLM / Poster 全部 200

---

## T-B-40 · Share Link 状态面板数据（0.5d · 3 子任务）

### ST-S4-B-40.1 写 `useShareLinkStatsQuery`（0.125d）
- **封装**：`GET /api/share-link/{code}/stats`

### ST-S4-B-40.2 写 Stats 组件（0.25d）
- **V10 收益**：Sprint 3 已实现，此处优化

### ST-S4-B-40.3 接入 Dashboard（0.125d）

---

## T-B-41 · ShareLink 失败降级（0.5d · 3 子任务）

### ST-S4-B-41.1 写重试机制（0.25d）
- **V10 收益**：TanStack Query `retry: 3` 内置

### ST-B-41.2 写降级 UI（0.125d）
### ST-S4-B-41.3 写 e2e：share-link-fallback.spec（0.125d）

---

## T-B-42 · LLM 增强进度轮询（0.5d · 3 子任务）⚠️ V10 简化

> **V10 收益**：TanStack Query `refetchInterval` 内置

### ST-S4-B-42.1 写 `useAuditEnhanceStatusQuery`（0.125d）
### ST-S4-B-42.2 写进度条组件（0.25d）
### ST-S4-B-42.3 接入 AuditPanel（0.125d）

---

## T-B-43 · Poster 异步生成 + 轮询（0.5d · 3 子任务）

### ST-S4-B-43.1 写 `usePosterStatusQuery`（0.125d）
### ST-S4-B-43.2 写状态机组件（0.25d）
- **三态**：generating / ready / failed

### ST-S4-B-43.3 接入 PosterDialog（0.125d）

---

## T-C-44 · Poster CLI 部署集成（Docker · 1.0d · 4 子任务）

### ST-C-44.1 写 `Dockerfile.poster`（0.25d）
### ST-C-44.2 写 `docker-compose.yml` 添加 poster 服务（0.25d）
### ST-C-44.3 本地构建 + 启动验证（0.25d）
### ST-C-44.4 CI 集成（0.25d）

---

## T-C-45 · 集成测试套件（0d · 2 子任务）

### ST-C-45.1 写 `tests/integration/` 骨架（0d）
### ST-C-45.2 跑通 3 个集成测试（0d）

---

## V10 验收清单（Sprint 4 G3 + G4 闸门）

```
G3 闸门（必须全部通过）：
  [ ] Lighthouse P75 ≥ 90（P/A/B/S 四项）
  [ ] pnpm build bundle < 300KB gzip
  [ ] 8 e2e spec 全绿
  [ ] 真实后端 5 模块 200

G4 闸门：
  [ ] Poster CLI Docker 镜像本地构建 < 60s
  [ ] docker compose up 启动成功
  [ ] Poster 异步生成端到端跑通
```

---

## V10 风险（Sprint 4 特有）

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| V10-S4-R1 | Lighthouse 分数不达标 | 中 | Vite 产物天然高分；重点优化 LCP 图 |
| V10-S4-R2 | 真实后端回归失败 | 中 | 用 docker compose 隔离环境；失败可回退 mock |
| V10-S4-R3 | Poster CLI Docker 镜像构建慢 | 低 | 多阶段构建 + 缓存 |

---

**Sprint 4 文档状态**：V10 选项 B 重写完成
**总工时**：10 人天（V2 是 14 人天，节省 4d）
**总子任务**：53 个（V2 是 50 个）
**下一步**：Sprint 3 完成后立即启动
