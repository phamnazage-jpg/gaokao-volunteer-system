# Sprint 8 任务拆解（W14-16 · 10 人天 · 50 子任务）— V10 选项 B

> **技术栈**：Vite 5 + React 19 + Zustand 4 + TanStack Query 5 + RHF 7 + Zod
> **目标**：后台管理页面收口（Share/Query/Review/Policy/通知/系统）+ 公共门户 React 化
> **闸门**：G7 最终（生产可发版）
> **V10 变化**：从 8d 增到 10d（+2d = 12 个后台页面，单页平均 0.5d 合理化）
> **PM 决策（2026-07-03）**：整体重写为新实现；Playwright 视觉回归 + Chromatic 验收

---

## ⚠️ V10 关键变化（与 V2 对比）

| 维度 | V2 | V10 选项 B |
|---|---|---|
| 单页估时 | 0.5-1.0d（紧凑） | **0.5-1.0d**（合理化，V2 有压缩） |
| 表单组件 | 手写 | **RHF + Zod**（统一模式） |
| 总估时 | 8d | **10d**（+2d 合理化） |

---

## 0. Sprint 8 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-E-10 | Share Link 列表 | 0.75d | 3 |
| T-E-11 | Share Link 详情 /stats | 0.75d | 3 |
| T-E-12 | Poster 管理 | 0.75d | 3 |
| T-E-13 | 分数线查询 | 0.75d | 3 |
| T-E-14 | 位次估算 | 0.5d | 2 |
| T-E-15 | 专业库 | 1.0d | 4 |
| T-E-16 | 院校库 | 1.0d | 4 |
| T-E-17 | 复核 Dashboard | 1.0d | 4 |
| T-E-18 | LLM 审计日志 | 0.5d | 3 |
| T-E-19 | Policy 中心 | 0.75d | 3 |
| T-E-20 | 通知列表 | 0.5d | 2 |
| T-E-21 | 通知模板编辑（RHF） | 0.75d | 3 |
| T-E-22 | 系统设置 | 0.5d | 2 |
| T-E-23 | 用户管理 | 0.5d | 2 |
| T-E-24 | 公共门户 React 化（10 页） | 1.0d | 4 |
| T-E-25 | Chromatic 收口（S8 最终） | 0.5d | 2 |
| T-E-26 | ESLint 0 warning 守门 | 0.25d | 2 |
| T-E-27 | G7 最终验收 | 0.25d | 1 |
| **合计** | **18 任务** | **10d** | **50** |

---

## T-E-10 · Share Link 列表（0.75d · 3 子任务）

### ST-S8-E-10.1 写 `useShareLinksQuery`（0.125d）
### ST-S8-E-10.2 写 ShareLinksTable（0.5d）
- **V10 集成**：S5-D-01 DataTable + 列筛选 + 删除按钮
### ST-S8-E-10.3 写 story + e2e（0.125d）

---

## T-E-11 · Share Link 详情 /stats（0.75d · 3 子任务）

### ST-S8-E-11.1 写 ShareLinkDetail（0.5d）
- **V10 集成**：Tabs（基础信息/访问统计/操作日志）
### ST-S8-E-11.2 写 StatsChart（0.125d）
- **V10 集成**：recharts LineChart
### ST-S8-E-11.3 写 story + e2e（0.125d）

---

## T-E-12 · Poster 管理（0.75d · 3 子任务）

### ST-S8-E-12.1 写 `usePostersQuery`（0.125d）
### ST-S8-E-12.2 写 PostersGrid（0.5d）
- **V10 集成**：缩略图 + 状态徽章
### ST-S8-E-12.3 写 story + e2e（0.125d）

---

## T-E-13 · 分数线查询（0.75d · 3 子任务）

### ST-S8-E-13.1 写 ScoreLineQueryForm（0.5d）
- **V10 集成**：S6-D-16 DataQueryForm scoreLine 变体
### ST-S8-E-13.2 写 ScoreLineResultTable（0.125d）
### ST-S8-E-13.3 写 story + e2e（0.125d）

---

## T-E-14 · 位次估算（0.5d · 2 子任务）

### ST-S8-E-14.1 写 RankEstimatorForm + Result（0.375d）
- **V10 集成**：S6-D-16 DataQueryForm rankEstimator 变体
### ST-S8-E-14.2 写 story + e2e（0.125d）

---

## T-E-15 · 专业库（1.0d · 4 子任务）

### ST-S8-E-15.1 写 `useMajorsQuery`（0.125d）
### ST-S8-E-15.2 写 MajorsTable（0.5d）
- **V10 集成**：S5-D-01 DataTable + 虚拟滚动
### ST-S8-E-15.3 写 MajorDetailModal（0.25d）
- **V10 集成**：S5-D-04 Modal + Tabs
### ST-S8-E-15.4 写 story + e2e（0.125d）

---

## T-E-16 · 院校库（1.0d · 4 子任务）

### ST-S8-E-16.1 写 `useSchoolsQuery`（0.125d）
### ST-S8-E-16.2 写 SchoolsGrid（0.5d）
- **V10 集成**：卡片网格 + Badge 985/211
### ST-S8-E-16.3 写 SchoolDetailDrawer（0.25d）
- **V10 集成**：S5-D-01 Tabs + Chart
### ST-S8-E-16.4 写 story + e2e（0.125d）

---

## T-E-17 · 复核 Dashboard（1.0d · 4 子任务）

### ST-S8-E-17.1 写 `useReviewQueueQuery`（0.125d）
### ST-S8-E-17.2 写 ReviewQueueTable（0.5d）
### ST-S8-E-17.3 写 ReviewActions（0.25d）
- **V10 集成**：RHF + Zod 审核表单
### ST-S8-E-17.4 写 story + e2e（0.125d）

---

## T-E-18 · LLM 审计日志（0.5d · 3 子任务）

### ST-S8-E-18.1 写 `useLLMLogsQuery`（0.125d）
### ST-S8-E-18.2 写 LLMLogsTable（0.25d）
- **列**：时间 / 用户 / Provider / 输入 / 输出 / 耗时
### ST-S8-E-18.3 写 story + e2e（0.125d）

---

## T-E-19 · Policy 中心（0.75d · 3 子任务）

### ST-S8-E-19.1 写 `usePoliciesQuery`（0.125d）
### ST-S8-E-19.2 写 PolicyEditor（0.5d）
- **V10 集成**：RHF + Zod + SafeMarkdown 预览
### ST-S8-E-19.3 写 story + e2e（0.125d）

---

## T-E-20 · 通知列表（0.5d · 2 子任务）

### ST-S8-E-20.1 写 NotificationsTable（0.375d）
### ST-S8-E-20.2 写 story + e2e（0.125d）

---

## T-E-21 · 通知模板编辑（RHF · 0.75d · 3 子任务）

### ST-S8-E-21.1 写 TemplateForm（RHF + Zod · 0.5d）
- **字段**：模板名称 / 渠道 / 变量 / 内容
### ST-S8-E-21.2 写变量预览（0.125d）
### ST-S8-E-21.3 写 story + e2e（0.125d）

---

## T-E-22 · 系统设置（0.5d · 2 子任务）

### ST-S8-E-22.1 写 SettingsForm（0.375d）
- **V10 集成**：RHF + Zod
### ST-S8-E-22.2 写 story + e2e（0.125d）

---

## T-E-23 · 用户管理（0.5d · 2 子任务）

### ST-S8-E-23.1 写 UsersTable（0.375d）
### ST-S8-E-23.2 写 story + e2e（0.125d）

---

## T-E-24 · 公共门户 React 化（10 页 · 1.0d · 4 子任务）

### ST-S8-E-24.1 写 10 个公共门户页（0.5d）
- **页面**：首页 / 政策 / 数据 / 帮助 / 关于 / 服务条款 / 隐私政策 / 联系我们 / 招贤纳士 / 友情链接
- **V10 关键**：每页 < 50 行代码（用 design system 组件拼装）

### ST-S8-E-24.2 SEO meta 注入（0.25d）
- **V10 集成**：react-helmet-async

### ST-S8-E-24.3 sitemap.xml + robots.txt（0.125d）

### ST-S8-E-24.4 写 e2e（0.125d）

---

## T-E-25 · Chromatic 收口（S8 最终 · 0.5d · 2 子任务）

### ST-S8-E-25.1 截图所有后台 + 门户页面（0.375d）
- **后台**：12 页 × 3 主题 = 36 截图
- **门户**：10 页 × 2 主题（无 system 主题）= 20 截图
- **总计**：56 截图

### ST-S8-E-25.2 提交基线 + 验证 0 像素 diff（0.125d）

---

## T-E-26 · ESLint 0 warning 守门（0.25d · 2 子任务）

### ST-S8-E-26.1 清理 S8 引入的 any（0.125d）
### ST-S8-E-26.2 清理 S8 引入的 unused（0.125d）

---

## T-E-27 · G7 最终验收（0.25d · 1 子任务）

### ST-S8-E-27.1 跑 G7 闸门清单（0.25d）
- **验收**：G7 清单 100% 通过

---

## V10 验收清单（Sprint 8 G7 最终闸门）

```
G7 闸门（必须全部通过）：
  [ ] 12 个后台页面 + 10 个公共门户页全部完成
  [ ] pnpm typecheck 0 error 0 any
  [ ] pnpm lint 0 error 0 warning
  [ ] pnpm test:storybook 全绿
  [ ] pnpm test:e2e 全绿
  [ ] pnpm chromatic 0 像素 diff
  [ ] Lighthouse P/A/B/S ≥ 95
  [ ] axe-core 0 critical 0 serious
  [ ] bundle < 350KB gzip
  [ ] 真实后端 5 模块 + admin 端到端跑通
  [ ] 生产可发版
```

---

## V10 风险（Sprint 8 特有）

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| V10-S8-R1 | 后台页面工期紧张 | 中 | 已合理化到 10d（V2 8d 不现实） |
| V10-S8-R2 | 公共门户 SEO | 中 | react-helmet-async 注入 meta |
| V10-S8-R3 | G7 收口发现新问题 | 低 | S8 末预留 0.25d 收口 |

---

**Sprint 8 文档状态**：V10 选项 B 重写完成
**总工时**：10 人天（V2 是 8 人天，+2d 合理化）
**总子任务**：50 个（V2 是 48 个）
**下一步**：Sprint 7 完成后立即启动 → G7 收口 → 生产可发版
