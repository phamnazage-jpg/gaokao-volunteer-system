# Sprint 7 任务拆解（W12-13 · 9 人天 · 48 子任务）— V10 选项 B

> **技术栈**：Vite 5 + React 19 + Zustand 4 + TanStack Query 5 + RHF 7 + Zod
> **目标**：i18n + 5 内部页（登录/Dashboard/布局/错误/权限）+ 4 订单案例
> **闸门**：G6.1（生产可发版验收：i18n 全 / Lighthouse 95 / a11y 0 critical）
> **V10 变化**：从 10d 缩到 9d（节省 1d = axe-core S5 已完成 + i18n 用 react-intl 简化）
> **PM 决策（2026-07-03）**：整体重写为新实现；Playwright 视觉回归 + Chromatic 验收

---

## ⚠️ V10 关键变化（与 V2 对比）

| 维度 | V2 | V10 选项 B |
|---|---|---|
| i18n 库 | next-intl（Next.js 专用） | **react-intl 7**（Vite 友好） |
| 权限守卫 | Next.js middleware | **手写 RequireAuth**（Vite 友好） |
| 路由 | Next.js App Router | **React Router 7**（Vite 友好） |
| 总估时 | 10d | **9d** |

---

## 0. Sprint 7 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-D-22 | react-intl 接入 | 1.0d | 4 |
| T-D-23 | 文案审计（中/英双语） | 0.5d | 3 |
| T-D-24 | Chromatic + Lighthouse 收口 | 1.0d | 4 |
| T-E-01 | 登录页 `/admin/login` | 0.5d | 3 |
| T-E-02 | Dashboard `/admin` | 1.0d | 4 |
| T-E-03 | Layout `/admin` shared | 0.5d | 3 |
| T-E-04 | 错误兜底 `/admin/error` | 0.25d | 2 |
| T-E-05 | 权限守卫 `<RequireAuth>` | 0.5d | 3 |
| T-E-06 | 订单列表 | 0.75d | 3 |
| T-E-07 | 订单详情 | 1.0d | 4 |
| T-E-08 | 案例列表 | 0.5d | 3 |
| T-E-09 | 案例详情 | 0.5d | 3 |
| T-E-10 | a11y 全量审计（V10 关键） | 0.75d | 4 |
| T-E-11 | Chromatic 收口（S7 增量） | 0.5d | 3 |
| **合计** | **14 任务** | **9d** | **48** |

---

## T-D-22 · react-intl 接入（1.0d · 4 子任务）⚠️ V10 替换

> **V10 替换**：next-intl → react-intl 7（Vite 友好）

### ST-S7-D-22.1 安装依赖（0.125d）
```bash
pnpm --filter web add react-intl
```

### ST-S7-D-22.2 写 `IntlProvider` 集成（0.25d）
- **V10 关键**：Zustand 存 locale（zh-CN / en-US）

### ST-S7-D-22.3 写 `messages/zh-CN.json` + `en-US.json`（0.5d）
- **内容**：所有用户可见文案
- **结构**：扁平 key + ICU MessageFormat

### ST-S7-D-22.4 写 locale 切换器（0.125d）
- **V10 集成**：Header 下拉菜单

---

## T-D-23 · 文案审计（中/英双语 · 0.5d · 3 子任务）

### ST-S7-D-23.1 提取所有硬编码中文（0.25d）
- **命令**：`grep -rn "[\u4e00-\u9fff]" apps/web/src/`
- **V10 验收**：0 硬编码中文（全部走 i18n）

### ST-S7-D-23.2 英文文案完整性（0.125d）
- **验收**：所有 key 都有 en-US 翻译

### ST-S7-D-23.3 ICU 语法校验（0.125d）
- **工具**：`eslint-plugin-formatjs`

---

## T-D-24 · Chromatic + Lighthouse 收口（1.0d · 4 子任务）

### ST-S7-D-24.1 Chromatic 收口（0.25d）
- **截图**：所有页面 × 3 主题 × 2 locale = 36 截图

### ST-S7-D-24.2 Lighthouse P75 复测（0.25d）
- **目标**：≥ 95

### ST-S7-D-24.3 修复 Lighthouse 警告（0.25d）

### ST-S7-D-24.4 提交最终基线（0.25d）

---

## T-E-01 · 登录页 `/admin/login`（0.5d · 3 子任务）

### ST-S7-E-01.1 写 LoginForm（RHF + Zod · 0.25d）
- **字段**：手机号 / 验证码 / 记住我

### ST-S7-E-01.2 写 mock 登录（0.125d）
- **V10 集成**：`useLoginMutation`

### ST-S7-E-01.3 写 story + e2e（0.125d）

---

## T-E-02 · Dashboard `/admin`（1.0d · 4 子任务）

### ST-S7-E-02.1 写 4 统计卡片（0.25d）
- 总订单 / 待审核 / 总用户 / 总分享

### ST-S7-E-02.2 写趋势图（0.25d）
- **V10 集成**：recharts LineChart

### ST-S7-E-02.3 写最近订单列表（0.25d）
- **V10 集成**：S5-D-01 DataTable

### ST-S7-E-02.4 写 story + e2e（0.25d）

---

## T-E-03 · Layout `/admin` shared（0.5d · 3 子任务）

### ST-S7-E-03.1 写 Sidebar（0.25d）
- **V10 不变量 L1**：≥ 1024px 显示侧栏
### ST-S7-E-03.2 写 Header（0.125d）
### ST-S7-E-03.3 写响应式折叠（0.125d）

---

## T-E-04 · 错误兜底 `/admin/error`（0.25d · 2 子任务）

### ST-S7-E-04.1 写 ErrorPage（0.125d）
### ST-S7-E-04.2 接入 ErrorBoundary（0.125d）

---

## T-E-05 · 权限守卫 `<RequireAuth>`（0.5d · 3 子任务）⚠️ V10 重写

> **V10 替换**：Next.js middleware → React Router 7 loader + RequireAuth 组件

### ST-S7-E-05.1 写 `useAuth` Zustand selector（0.125d）
### ST-S7-E-05.2 写 `<RequireAuth>` 组件（0.25d）
- **行为**：未登录跳 /admin/login；权限不足跳 /403
### ST-S7-E-05.3 接入路由配置（0.125d）

---

## T-E-06 · 订单列表（0.75d · 3 子任务）

### ST-S7-E-06.1 写 `useOrdersQuery`（0.125d）
### ST-S7-E-06.2 写 OrdersTable（S5-D-01 集成 · 0.5d）
- **V10 集成**：TanStack Table + 排序 + 筛选 + 分页
### ST-S7-E-06.3 写 story + e2e（0.125d）

---

## T-E-07 · 订单详情（1.0d · 4 子任务）

### ST-S7-E-07.1 写 `useOrderQuery`（0.125d）
### ST-S7-E-07.2 写 OrderDetail 组件（0.5d）
- **V10 集成**：Tabs（Sprint 1）+ DataTable + Chart
### ST-S7-E-07.3 写操作按钮组（0.25d）
- 审核通过 / 拒绝 / 申请修改
### ST-S7-E-07.4 写 story + e2e（0.125d）

---

## T-E-08 · 案例列表（0.5d · 3 子任务）

### ST-S7-E-08.1 写 `useCasesQuery`（0.125d）
### ST-S7-E-08.2 写 CasesGrid（0.25d）
### ST-S7-E-08.3 写 story + e2e（0.125d）

---

## T-E-09 · 案例详情（0.5d · 3 子任务）

### ST-S7-E-09.1 写 `useCaseQuery`（0.125d）
### ST-S7-E-09.2 写 CaseDetail（0.25d）
- **V10 集成**：SafeMarkdown 渲染案例正文
### ST-S7-E-09.3 写 story + e2e（0.125d）

---

## T-E-10 · a11y 全量审计（0.75d · 4 子任务）⚠️ V10 关键

> **PM 决策（2026-07-03）**：Chromatic + axe-core 双重验收

### ST-S7-E-10.1 axe-core 全量扫描（0.25d）
- **覆盖**：所有页面 + 所有业务组件

### ST-S7-E-10.2 键盘导航全路径测试（0.25d）
- **验收**：所有交互可仅用键盘完成

### ST-S7-E-10.3 屏幕阅读器测试（0.125d）
- **验收**：VoiceOver + NVDA 都能正确朗读

### ST-S7-E-10.4 WCAG AA 报告（0.125d）
- **工具**：Lighthouse a11y 100 分

---

## T-E-11 · Chromatic 收口（S7 增量 · 0.5d · 3 子任务）

### ST-S7-E-11.1 截图所有 admin 页面（0.25d）
### ST-S7-E-11.2 提交基线（0.125d）
### ST-S7-E-11.3 验证 0 像素 diff（0.125d）

---

## V10 验收清单（Sprint 7 G6.1 闸门）

```
G6.1 闸门（必须全部通过）：
  [ ] i18n 中/英双语全覆盖，0 硬编码
  [ ] admin 模块 5 页面 + 4 订单/案例全部完成
  [ ] 权限守卫正确工作
  [ ] axe-core 0 critical 0 serious
  [ ] Lighthouse P ≥ 95 / A ≥ 95 / B ≥ 95 / S ≥ 95
  [ ] pnpm typecheck 0 error 0 any
  [ ] pnpm lint 0 error 0 warning
  [ ] pnpm test:storybook 全绿
  [ ] pnpm chromatic 0 像素 diff
  [ ] pnpm test:e2e 全绿（含 5 admin 路径）
  [ ] bundle < 320KB gzip
```

---

## V10 风险（Sprint 7 特有）

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| V10-S7-R1 | react-intl 切换语言闪烁 | 中 | 提前注入 locale 到 html lang 属性 |
| V10-S7-R2 | RequireAuth 与 React Router 7 loader 兼容 | 低 | 官方推荐模式 |
| V10-S7-R3 | i18n key 命名冲突 | 低 | 强制命名空间 `module.component.field` |

---

**Sprint 7 文档状态**：V10 选项 B 重写完成
**总工时**：9 人天（V2 是 10 人天，节省 1d）
**总子任务**：48 个（V2 是 52 个）
**下一步**：Sprint 6 完成后立即启动
