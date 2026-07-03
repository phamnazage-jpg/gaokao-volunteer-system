# Sprint 7 任务拆解（W12-13 · 10 人天 · 52 子任务）

> **主任务**：T-D-22, T-D-23, T-D-24 + T-E-01 ~ T-E-09
> **目标**：i18n + 性能 + 5 内部页 + 4 订单案例
> **闸门**：G6.1（生产可发版验收）

## 0. Sprint 7 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-D-22 | next-intl 接入 | 1.5d | 5 |
| T-D-23 | 文案审计 | 0.5d | 2 |
| T-D-24 | Chromatic + Lighthouse 收口 | 1.5d | 4 |
| T-E-01 | 登录页 `/admin/login` | 0.5d | 3 |
| T-E-02 | Dashboard `/admin` | 1.5d | 5 |
| T-E-03 | Layout `/admin` shared | 1.0d | 4 |
| T-E-04 | 错误兜底 `/admin/error.tsx` | 0.5d | 3 |
| T-E-05 | 权限守卫 | 0.5d | 3 |
| T-E-06 | 订单列表 | 1.0d | 4 |
| T-E-07 | 订单详情 | 1.5d | 5 |
| T-E-08 | 案例列表 | 0.75d | 3 |
| T-E-09 | 案例详情 | 0.75d | 3 |
| **合计** | **12 任务** | **10d + 缓冲 0d = 10d** | **52** |

---

## D.5 国际化基础（2 任务 · 7 子任务 · 2d）

### T-D-22 · next-intl 接入（1.5d · 5 子任务）
- ST-S7-D-22.1 写 `packages/i18n/zh-CN/{chat,plans,common,errors,share,dataQuery,review,poster}.json`（0.5d）
- ST-S7-D-22.2 写 `packages/i18n/en-US/{...}.json`（占位空字典）（0.125d）
- ST-S7-D-22.3 路由级 locale 切换（0.5d）
- ST-S7-D-22.4 所有硬编码中文移到词条（0.25d）
- ST-S7-D-22.5 切到 en-US 显示 key 而非中文（0.125d）
- **约束**：**§0.1 R-NEW-5**（quickPrompts 三态文案抽到 `chat.json`）

### T-D-23 · 文案审计（0.5d · 2 子任务）
- ST-S7-D-23.1 i18n key 命名规范文档（0.25d）
- ST-S7-D-23.2 验证 `git grep "[\u4e00-\u9fff]"` 在 `apps/web/src/` 仅命中 `i18n/` 目录（0.25d）

---

## D.6 性能 + 视觉回归（1 任务 · 4 子任务 · 1.5d）

### T-D-24 · Chromatic + Lighthouse 收口（1.5d · 4 子任务）
- ST-S7-D-24.1 Chromatic 所有 Storybook stories 跑通（0.5d）
- ST-S7-D-24.2 Lighthouse CI 收口（0.5d）
- ST-S7-D-24.3 路由级 `loading.tsx` 补全（0.25d）
- ST-S7-D-24.4 `next/image` / `next/font` 优化（0.25d）
- **验收**：
  - [ ] 50+ stories baseline（V2 增量）
  - [ ] LCP P75 < 1.8s
  - [ ] Bundle < 150KB

---

## E.1 运营后台基础（5 任务 · 18 子任务 · 4d）

### T-E-01 · 登录页 `/admin/login`（0.5d · 3 子任务）
- ST-S7-E-01.1 复用 T-A-09 Button + T-A-10 Input（0.125d）
- ST-S7-E-01.2 调 `POST /api/admin/auth/login`（0.25d）
- ST-S7-E-01.3 URL token 支持（commit `2af1d06`）（0.125d）

### T-E-02 · Dashboard `/admin`（1.5d · 5 子任务）
- ST-S7-E-02.1 echarts 集成（0.5d）
- ST-S7-E-02.2 订单/咨询趋势（0.25d）
- ST-S7-E-02.3 4 个 KPI 卡片（0.25d）
- ST-S7-E-02.4 URL token 自动认证（commit `0ec5bdf`）（0.25d）
- ST-S7-E-02.5 写 e2e（0.25d）

### T-E-03 · Layout `/admin` shared（1.0d · 4 子任务）
- ST-S7-E-03.1 顶部 nav（0.25d）
- ST-S7-E-03.2 侧边栏（0.25d）
- ST-S7-E-03.3 暗色支持（0.25d）
- ST-S7-E-03.4 响应式（0.25d）

### T-E-04 · 错误兜底 `/admin/error.tsx`（0.5d · 3 子任务）
- ST-S7-E-04.1 同 T-B-19 ErrorBoundary（0.25d）
- ST-S7-E-04.2 写单测（0.125d）
- ST-S7-E-04.3 写 e2e（0.125d）

### T-E-05 · 权限守卫（0.5d · 3 子任务）
- ST-S7-E-05.1 middleware 写未登录跳 /admin/login（0.25d）
- ST-S7-E-05.2 写单测（0.125d）
- ST-S7-E-05.3 写 e2e（0.125d）

---

## E.2 订单 + 案例（4 任务 · 15 子任务 · 4d）

### T-E-06 · 订单列表 `/admin/orders`（1.0d · 4 子任务）
- ST-S7-E-06.1 表格 + 分页（0.25d）
- ST-S7-E-06.2 筛选（状态/时间/支付方式）（0.25d）
- ST-S7-E-06.3 调 `GET /api/admin/orders`（0.25d）
- ST-S7-E-06.4 写 e2e（0.25d）

### T-E-07 · 订单详情 `/admin/orders/{id}`（1.5d · 5 子任务）
- ST-S7-E-07.1 订单基本信息（0.25d）
- ST-S7-E-07.2 支付信息（0.25d）
- ST-S7-E-07.3 关联方案（0.25d）
- ST-S7-E-07.4 操作历史（0.25d）
- ST-S7-E-07.5 写 e2e（0.5d）

### T-E-08 · 案例列表 `/admin/cases`（0.75d · 3 子任务）
- ST-S7-E-08.1 卡片式列表（0.25d）
- ST-S7-E-08.2 调 `GET /api/admin/cases`（0.25d）
- ST-S7-E-08.3 写 e2e（0.25d）

### T-E-09 · 案例详情 `/admin/cases/{id}`（0.75d · 3 子任务）
- ST-S7-E-09.1 案例详情（0.25d）
- ST-S7-E-09.2 调 `GET /api/admin/cases/{id}`（0.25d）
- ST-S7-E-09.3 写 e2e（0.25d）

---

## Sprint 7 收口验收

- [ ] 12 主任务 / 52 子任务全部完成
- [ ] i18n 词条覆盖
- [ ] 5 运营后台页 + 4 订单/案例页全绿
- [ ] 50+ Chromatic stories
- [ ] 进入 Sprint 8 前 commit：`<feat(s7): i18n+admin pages>`
