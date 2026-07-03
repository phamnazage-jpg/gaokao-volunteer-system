# Sprint 8 任务拆解（W14-16 · 8 人天 · 48 子任务）

> **主任务**：T-E-10 ~ T-E-24
> **目标**：内部页 React 化收口（Share 管理 / Data Query / Review / Policy / 通知 / 公共门户）
> **闸门**：生产可发版（**G7 最终**）

## 0. Sprint 8 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-E-10 | Share Link 列表 | 1.0d | 4 |
| T-E-11 | Share Link 详情 /stats | 1.0d | 4 |
| T-E-12 | Poster 管理 | 1.0d | 4 |
| T-E-13 | 分数线查询 | 1.0d | 4 |
| T-E-14 | 位次估算 | 0.75d | 3 |
| T-E-15 | 专业库 | 1.0d | 4 |
| T-E-16 | 院校库 | 1.25d | 4 |
| T-E-17 | 复核 Dashboard | 1.25d | 5 |
| T-E-18 | LLM 审计日志 | 0.75d | 3 |
| T-E-19 | Policy 中心 | 1.0d | 4 |
| T-E-20 | 通知列表 | 1.0d | 3 |
| T-E-21 | 通知模板编辑 | 1.5d | 4 |
| T-E-22 | 系统设置 | 1.5d | 4 |
| T-E-23 | 用户管理 | 1.0d | 4 |
| T-E-24 | 公共门户 React 化（10 页） | 1.0d | 5 |
| **合计** | **15 任务** | **15d 实际 8d + 缓冲 7d = 15d** | **48** |

> 警告：S8 任务密度最大（15 任务 / 8d），每个 0.5d 紧凑；缓冲 7d 用于延期 / 整改

---

## E.3 Share Link 管理（3 任务 · 12 子任务 · 3d）

### T-E-10 · Share Link 列表 `/admin/share-links`（1.0d · 4 子任务）
- ST-S8-E-10.1 表格 + 分页（0.25d）
- ST-S8-E-10.2 调 `GET /api/share-link`（待后端补全）（0.25d）
- ST-S8-E-10.3 撤销按钮 + 过期筛选（0.25d）
- ST-S8-E-10.4 写 e2e（0.25d）

### T-E-11 · Share Link 详情 `/admin/share-links/{code}/stats`（1.0d · 4 子任务）
- ST-S8-E-11.1 点击量 / 转化率 / 设备分布（0.25d）
- ST-S8-E-11.2 时序图（echarts）（0.25d）
- ST-S8-E-11.3 调 `GET /api/share-link/{code}/stats`（0.25d）
- ST-S8-E-11.4 写 e2e（0.25d）

### T-E-12 · Poster 管理 `/admin/posters`（1.0d · 4 子任务）
- ST-S8-E-12.1 复用 T-B-43 usePoster（0.25d）
- ST-S8-E-12.2 复用 T-D-20 PosterPreview（0.25d）
- ST-S8-E-12.3 模板选择（0.25d）
- ST-S8-E-12.4 写 e2e（0.25d）

---

## E.4 Data Query 内部页（4 任务 · 15 子任务 · 4d）

### T-E-13 · 分数线查询 `/admin/data-query/score-line`（1.0d · 4 子任务）
- ST-S8-E-13.1 复用 T-D-16 ScoreLineQueryForm（0.25d）
- ST-S8-E-13.2 复用 T-D-17 ScoreLineResult（0.25d）
- ST-S8-E-13.3 导出 CSV（0.25d）
- ST-S8-E-13.4 写 e2e（0.25d）

### T-E-14 · 位次估算 `/admin/data-query/rank-estimator`（0.75d · 3 子任务）
- ST-S8-E-14.1 复用 T-D-16 RankEstimatorForm（0.25d）
- ST-S8-E-14.2 复用 T-D-17 RankEstimatorResult（0.25d）
- ST-S8-E-14.3 写 e2e（0.25d）

### T-E-15 · 专业库 `/admin/data-query/majors`（1.0d · 4 子任务）
- ST-S8-E-15.1 复用 T-D-16 MajorsQueryForm（0.25d）
- ST-S8-E-15.2 复用 T-D-17 MajorsResult（0.25d）
- ST-S8-E-15.3 分类树（0.25d）
- ST-S8-E-15.4 写 e2e（0.25d）

### T-E-16 · 院校库 `/admin/data-query/schools`（1.25d · 4 子任务）
- ST-S8-E-16.1 复用 T-D-16 SchoolsQueryForm（0.25d）
- ST-S8-E-16.2 复用 T-D-17 SchoolsResult（0.25d）
- ST-S8-E-16.3 985/211 筛选（0.5d）
- ST-S8-E-16.4 写 e2e（0.25d）

---

## E.5 Review 内部页（2 任务 · 8 子任务 · 2d）

### T-E-17 · 复核 Dashboard `/admin/review`（1.25d · 5 子任务）
- ST-S8-E-17.1 待复核列表（0.25d）
- ST-S8-E-17.2 LLM 增强结果（0.25d）
- ST-S8-E-17.3 action 按钮（approve / reject / revise）（0.25d）
- ST-S8-E-17.4 复用 T-D-18 ReviewFlow（0.25d）
- ST-S8-E-17.5 写 e2e（0.25d）

### T-E-18 · LLM 审计日志 `/admin/review/llm-logs`（0.75d · 3 子任务）
- ST-S8-E-18.1 模型使用统计（0.25d）
- ST-S8-E-18.2 token 消耗 + fallback 触发次数（0.25d）
- ST-S8-E-18.3 写 e2e（0.25d）

---

## E.6 Policy 内部页（1 任务 · 4 子任务 · 1d）

### T-E-19 · Policy 中心 `/admin/policies`（1.0d · 4 子任务）
- ST-S8-E-19.1 5 个政策页 editor（privacy / service-terms / policy-center / same-score / deletion-policy）（0.25d）
- ST-S8-E-19.2 草稿/发布两态（0.25d）
- ST-S8-E-19.3 Markdown 编辑器（0.25d）
- ST-S8-E-19.4 写 e2e（0.25d）
- **依据**：commit `c5b0c3d` `818bfa4` 5 个政策页面已实现后端

---

## E.7 通知 + 设置（4 任务 · 15 子任务 · 4d）

### T-E-20 · 通知列表 `/admin/notifications`（1.0d · 3 子任务）
- ST-S8-E-20.1 列表 + 筛选（0.25d）
- ST-S8-E-20.2 调 `GET /api/admin/notifications`（0.25d）
- ST-S8-E-20.3 写 e2e（0.5d）

### T-E-21 · 通知模板编辑（1.5d · 4 子任务）
- ST-S8-E-21.1 列表（0.25d）
- ST-S8-E-21.2 编辑器 + 变量插值（0.5d）
- ST-S8-E-21.3 预览（0.5d）
- ST-S8-E-21.4 写 e2e（0.25d）

### T-E-22 · 系统设置 `/admin/settings`（1.5d · 4 子任务）
- ST-S8-E-22.1 分组（基础/支付/AI/通知）（0.5d）
- ST-S8-E-22.2 表单 + 校验（0.5d）
- ST-S8-E-22.3 调 `PATCH /api/admin/settings`（0.25d）
- ST-S8-E-22.4 写 e2e（0.25d）

### T-E-23 · 用户管理 `/admin/users`（1.0d · 4 子任务）
- ST-S8-E-23.1 列表 + 角色筛选（0.25d）
- ST-S8-E-23.2 创建 / 编辑 / 禁用（0.5d）
- ST-S8-E-23.3 调 `GET/POST/PATCH /api/admin/users`（0.125d）
- ST-S8-E-23.4 写 e2e（0.125d）

---

## E.8 公共门户 React 化（1 任务 · 5 子任务 · 1d）

### T-E-24 · 公共门户 React 化（10 页 / 1d · 5 子任务）
- ST-S8-E-24.1 `/pricing` 定价页（0.125d）
- ST-S8-E-24.2 `/portal/{token}/info` 资料向导（0.125d）
- ST-S8-E-24.3 `/portal/{token}/status` 状态页（0.125d）
- ST-S8-E-24.4 `/portal/{token}/report` 报告查看（0.125d）
- ST-S8-E-24.5 `/portal/{token}/cwb` 冲稳保 + `/full-plan` 完整规划 + `/notifications` + `/deletion-request` + `/payment-return` + `/s/{code}` 短链接（0.5d）
- **复用**：所有 portal 页用 `packages/ui/` + `packages/api-client/` + `packages/hooks/`
- **验收**：
  - [ ] 与 `admin/static/portal-ui.css` 视觉一致
  - [ ] 全 10 个 portal 流程跑通

---

## Sprint 8 收口验收（**G7 生产可发版**）

- [ ] 15 主任务 / 48 子任务全部完成
- [ ] **G7 通过**：生产可发版
  - 21/21 功能模块
  - 17/17 后端集成点
  - 0 critical a11y 违规
  - Lighthouse 12 页 P75 ≥ 90
  - Bundle < 150KB
  - 50+ Chromatic stories
  - 15+ e2e spec 全绿
- [ ] 发版前 commit：`<release: v1.0.0 — frontend react migration complete>`

---

## 全 8 Sprint 收口

| 维度 | 目标 | 实际 |
|---|---|---|
| **任务数** | 136 | 136 |
| **子任务数** | ~400 | 497 |
| **人天** | 92 | 92 |
| **周数** | 16 | 16 |
| **闸门** | 6 | 7（含 G7 生产可发版） |
| **风险** | 10 | 10（全部 R-NEW-1..10 应对） |
| **Sprint 缓冲** | - | 14d 散落 8 Sprint |

---

**任务拆解完成。所有 Sprint 子表文件已生成，可按 Sprint 1 → Sprint 8 顺序执行。**
