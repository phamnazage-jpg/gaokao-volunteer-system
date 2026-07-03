# V10 执行路线图 — 82 人天 / 8 Sprint（V10 选项 B 重写）

> **配套文档**：`V10_REFACTOR_STRATEGY_UI_VS_TECH.md`（V10 决策）/ 8 个 `SPRINT_X_SX_*.md`
> **编制日期**：2026-07-03（V10 重写版）
> **技术栈**：Vite 5 + React 19 + Zustand 4 + TanStack Query 5 + RHF 7 + Zod + Vitest 2 + Playwright 1.55 + Chromatic
> **PM 决策（2026-07-03）**：
>   - Q1（技术栈）：前端工程师选型 → 选项 B（Vite+React+Zustand+TanStack Query+RHF）
>   - Q2（UI 验收）：Playwright 视觉回归 + Chromatic
>   - Q3（代码处置）：整体重写为新实现
>   - Q5（文档更新）：是，更新 SPRINT_2-8 全部文档

---

## ⚠️ V10 vs V2 关键差异

| 维度 | V2 | V10 | 变化 |
|---|---|---|---|
| 框架 | Next.js 16 | **Vite 5 + React 19** | 重写 |
| 状态管理 | 7 个手写 hook | **Zustand 4** | 简化 |
| 数据获取 | 自写 useChat | **TanStack Query 5** | 升级 |
| 表单 | 受控状态机 | **RHF 7 + Zod** | 升级 |
| 视觉回归 | 无 | **+ Chromatic** | 新增 |
| 验收 | axe / Lighthouse | **+ Chromatic 像素 diff** | 加强 |
| 总估时 | 92 人天 | **82 人天** | **节省 10d** |
| 总子任务 | 470 | **415** | 节省 55 |

---

## 1. 路线图设计原则（V10 不变）

| 原则 | 落地方式 |
|---|---|
| **垂直切片** | 每 sprint 都有可演示产物 |
| **风险前置** | B 阶段（最大风险）放第 2-3 sprint |
| **依赖显式化** | 跨 sprint 任务标 ❗，并行任务标 ⚡ |
| **可中断性** | 每 sprint 末交付"Demoable Build" |
| **能力对齐** | 每 sprint 必跑 Lighthouse / axe / Playwright / **Chromatic** |
| **UI/交互 1:1** | V10 核心约束：12 项 UI 不变量必须复现 |

---

## 2. 8-Sprint 路线图（V10 重写版 · 16 周）

> **假设**：1 个前端主程 + 1 个后端联调支持 + 0.5 个设计 review
> **单 sprint 容量**：~10 人天（V10 平均；Sprint 8 10d / Sprint 2 9.5d / Sprint 3 12d）

| Sprint | 周次 | 阶段 | 任务数 | 人天 | 关键交付 | Demoable 产物 | 闸门 |
|---|---|---|---|---|---|---|---|
| **S1** | W1 | A 前半 | 14 | 11 | monorepo + 5 组件 + CI | 5 页面 + CI 绿 | G0 ✅ |
| **S2** | W2-3 | A 后半 + B 启动 | 16 | **9.5** | Vite + Zustand + TanStack Query + Chromatic | 8 端点真实化 + 视觉基线 8 页 | G1 |
| **S3** | W4-5 | B 主体 | 15 | **12** | 5 大 V2 新模块 + LLM 4 模 | 端到端 5 模块 + 视觉基线 13 页 | G2 |
| **S4** | W6-7 | B 收口 + C 启动 | 16 | **10** | Lighthouse ≥90 + Poster CLI | 性能报告 + Poster Docker | G3 + G4 |
| **S5** | W8-9 | C 收口 + D 启动 | 16 | **9** | 18 高级组件 + Storybook | Storybook 19 组件 + axe 0 critical | G5 |
| **S6** | W10-11 | D 主体 | 13 | **12** | 7 业务组件 + 暗色审计 | 7 业务组件 + 视觉基线 7×3×3×6 | G6 |
| **S7** | W12-13 | D 收口 + E 启动 | 14 | **9** | i18n + 5 admin 页面 | i18n 中/英 + admin 入口 | G6.1 |
| **S8** | W14-16 | E 主体 | 18 | **10** | 12 后台 + 10 公共门户页 | 全量后台 + 门户 + 视觉收口 | **G7 最终** |
| **合计** | **16 周** | — | **122** | **82 + 11 缓冲 = 93** | — | 生产可发版 | — |

> 8 sprint 总容量 82 人天 + 11 缓冲 = 93 人天。按 4 人/16 周实际可投 = 64 人天 → **结论：单兵执行需 23 周，多人 16 周可完成**（与 V2 一致）。

---

## 3. Sprint 详图（V10 关键差异）

### S1（W1）— 11 人天 · 阶段 A 前半 ✅ 已完成

**入口条件**：PM 批准 14 人天预算
**目标**：让原型在 monorepo 里能跑起来，CI 灯绿

**已完成**（SPRINT_1_CLOSEOUT_2026-07-03.md）：
- pnpm + Turborepo + root package.json
- cp -r `前端原型代码/` → `apps/web/`（⚠️ 勘误：原型未在 git 中）
- 5 基础组件：Button / Input / Card / Badge / Tabs
- web-ci.yml：typecheck / lint / build / bundle
- G0 闸门：pnpm install 1m55s / typecheck 0 errors / lint 0 errors 49 warnings / build 8 routes

**V10 收益**：S1 是 V2 → V10 共同基础，工时不变（11d）

---

### S2（W2-3）— 9.5 人天 · A 后半 + B 启动 ⚠️ V10 简化

**入口条件**：S1 G0 通过
**目标**：Vite + Zustand + TanStack Query + Chromatic + 8 端点真实化

| 任务 | 人天 | V10 变化 |
|---|---|---|
| Vitest + RTL + MSW + **Chromatic** 配置 | 0.5 | + Chromatic |
| OpenAPI Codegen + Zod schema | 1.0 | 类型 + Zod 联合生成 |
| **Zustand store + 5 query hooks** | 1.0 | **替代 7 手写 hook** |
| RHF 重写 FormCard | 1.0 | **替代 3-step 状态机** |
| **Chromatic 视觉基线 8 页** | 0.5 | **V10 新增** |
| Vite build + bundle 验证 | 0.5 | V10 新增 |
| 其他 7 任务（Playwright e2e 等） | 5.0 | 不变 |

**V10 vs V2**：18d → 9.5d（节省 8.5d）

**退出条件**：
- [ ] OpenAPI 30+ 端点类型生成 0 `any`
- [ ] Zustand store 4 slice 完成
- [ ] Chromatic 视觉基线 8 页全提交
- [ ] Vite build bundle < 300KB gzip
- [ ] **G1 闸门**：lint 0 warning（V10 重写后归零）

---

### S3（W4-5）— 12 人天 · B 主体 ⚠️ V10 简化

**入口条件**：S2 G1 通过
**目标**：5 大 V2 新模块 + LLM 4 模 fallback

| 任务 | 人天 | V10 变化 |
|---|---|---|
| useChatOrchestrator（V10 重写） | 0.5 | 从 1.5d 简化 |
| 真实 sendMessage + typing | 0.5 | TanStack Query mutation |
| 真实 getHistory + 滚动恢复 | 0.5 | TanStack Query |
| usePlan/useConsultation 真实化 | 0.75 | 不变 |
| useProfile Zustand 版 | 0.5 | 从 1.0d 简化 |
| useAudit + LLM 增强（4 模 fallback） | 0.75 | 4 模实测 |
| Share Link API（4 端点） | 0.75 | 不变 |
| Data Query API（3 端点） | 0.75 | 不变 |
| Review Flow API（3 端点） | 0.75 | 不变 |
| Portal API（2 端点） | 0.5 | 不变 |
| LLM Audit Enhance API | 0.75 | SSE + Zustand 增量 |
| Poster Generate API | 0.5 | 不变 |
| Share Link 统计 + UI | 1.0 | V10 加强 |
| Chromatic 视觉回归（S3 增量） | 0.5 | V10 新增 |
| ESLint 0 warning 守门 | 0.5 | V10 关键 |

**V10 vs V2**：22d → 12d（节省 10d）

**退出条件**：
- [ ] 5 大新模块端到端跑通
- [ ] LLM 4 模实测可切换 + 自动降级
- [ ] **G2 闸门**：lint 0 warning + Chromatic 13 页基线

---

### S4（W6-7）— 10 人天 · B 收口 + C 启动 ⚠️ V10 简化

**入口条件**：S3 G2 通过
**目标**：性能达标（Lighthouse ≥ 90）+ Poster CLI 镜像

| 任务 | 人天 | V10 变化 |
|---|---|---|
| 错误码 → 用户文案映射 | 0.5 | 不变 |
| ErrorBoundary + 离线 + 防重 | 1.5 | RHF 简化 |
| TanStack Query 持久化 | 0.5 | persister 内置 |
| e2e 真实化（8 路径） | 2.0 | Playwright 加速 |
| Lighthouse CI | 1.5 | Vite 产物天然高分 |
| Bundle 优化 | 0.5 | V10 简化（已分块） |
| 真实后端回归 | 0.5 | docker compose |
| Poster CLI Docker | 1.0 | 不变 |
| 其他 4 任务 | 2.0 | 不变 |

**V10 vs V2**：14d → 10d（节省 4d）

**退出条件**：
- [ ] **G3 闸门**：Lighthouse P/A/B/S ≥ 90
- [ ] **G4 闸门**：Poster CLI Docker 镜像跑通
- [ ] 8 e2e spec 全绿 + 真实后端 5 模块 200

---

### S5（W8-9）— 9 人天 · C 收口 + D 启动 ⚠️ V10 升级

**入口条件**：S4 G3 + G4 通过
**目标**：18 高级组件 + Storybook + axe-core CI

| 任务 | 人天 | V10 变化 |
|---|---|---|
| DataTable（TanStack Table + Virtual） | 1.0 | **V10 升级** |
| Tree（react-arborist） | 0.5 | **V10 升级** |
| Chart（recharts + 主题） | 1.0 | V10 主题适配 |
| 11 基础组件（Modal/Toast/Tooltip 等） | 3.75 | Radix 头less |
| Storybook 配置 + 19 组件 story | 1.5 | Vite builder |
| **axe-core CI 集成** | 0.5 | **V10 新增** |

**V10 vs V2**：12d → 9d（节省 3d）

**退出条件**：
- [ ] **G5 闸门**：18 组件 dark story 全覆盖 + axe-core 0 critical

---

### S6（W10-11）— 12 人天 · D 主体 ⚠️ V10 加强

**入口条件**：S5 G5 通过
**目标**：7 业务组件 + 暗色审计

| 任务 | 人天 | V10 变化 |
|---|---|---|
| SharePanel + ShareStatusPanel | 1.25 | 不变 |
| DataQueryForm 4 变体 | 1.0 | 不变 |
| DataQueryResult 4 变体 | 1.0 | 不变 |
| ReviewFlow + LLMEnhancement + PosterPreview | 2.0 | 不变 |
| 暗色变体审计 | 1.0 | V10 关键 |
| **Chromatic 视觉回归（S6 增量）** | 1.0 | **V10 新增** |
| axe-core 集成（复用 S5） | 0 | V10 收益 |
| 屏幕阅读器 + 键盘测试 | 0.5 | 不变 |
| 替换 alert() 为 Toast | 0.25 | 不变 |
| ESLint 0 warning 守门 | 0.5 | V10 关键 |

**V10 vs V2**：11d → 12d（+1d Chromatic 验证）

**退出条件**：
- [ ] **G6 闸门**：7 业务组件 + 暗色审计 0 像素 diff
- [ ] WCAG AA 对比度全通过

---

### S7（W12-13）— 9 人天 · D 收口 + E 启动 ⚠️ V10 替换

**入口条件**：S6 G6 通过
**目标**：i18n 中/英 + 5 admin 页面

| 任务 | 人天 | V10 变化 |
|---|---|---|
| **react-intl 接入**（替换 next-intl） | 1.0 | V10 替换 |
| 文案审计（中/英） | 0.5 | V10 关键 |
| Chromatic + Lighthouse 收口 | 1.0 | V10 关键 |
| 5 admin 页面（Login/Dashboard/Layout/Error/Auth） | 2.75 | Vite 友好 |
| 4 订单/案例页面 | 2.0 | 不变 |
| **a11y 全量审计** | 0.75 | **V10 关键** |
| Chromatic 收口（S7 增量） | 0.5 | V10 新增 |

**V10 vs V2**：10d → 9d（节省 1d）

**退出条件**：
- [ ] **G6.1 闸门**：i18n 中/英全覆盖 + Lighthouse ≥ 95 + a11y 0 critical

---

### S8（W14-16）— 10 人天 · E 主体 ⚠️ V10 合理化

**入口条件**：S7 G6.1 通过
**目标**：12 后台 + 10 公共门户页

| 任务 | 人天 | V10 变化 |
|---|---|---|
| 8 后台管理页面 | 5.0 | V10 合理化（每页 0.5-1.0d） |
| 4 通知/Policy/设置/用户页面 | 2.75 | V10 合理化 |
| **公共门户 React 化（10 页）** | 1.0 | V10 关键 |
| **Chromatic 收口（S8 最终）** | 0.5 | V10 新增 |
| ESLint 0 warning 守门 | 0.25 | V10 关键 |
| **G7 最终验收** | 0.25 | V10 关键 |

**V10 vs V2**：8d → 10d（+2d 合理化）

**退出条件**：
- [ ] **G7 闸门（最终）**：生产可发版
  - 12 后台 + 10 公共门户页全部完成
  - pnpm typecheck/lint/test/e2e/storybook/chromatic 全绿
  - Lighthouse P/A/B/S ≥ 95
  - axe-core 0 critical 0 serious
  - bundle < 350KB gzip
  - 真实后端 5 模块 + admin 端到端跑通

---

## 4. V10 关键风险闸门（不能跳过）

| 闸门 | 位置 | 失败动作 | V10 关键变化 |
|---|---|---|---|
| **G0** | S1 末 | 暂停 S2，修基础 | ✅ 已通过 |
| **G1** | S2 末 | 暂停 S3，补 codegen + Zustand | **新增**：lint 0 warning |
| **G2** | S3 末 | 暂停 S4，与后端对齐 LLM 超时 | **新增**：Chromatic 13 页基线 |
| **G3** | S4 末 | 暂停 S5，先做性能调优 | 不变 |
| **G4** | S4 末 | 暂停 S5，修正 Dockerfile | 不变 |
| **G5** | S5 末 | 暂停 S6，先做 axe-core | **加强**：axe 0 critical 强制 |
| **G6** | S6 末 | 暂停 S7，先做 design pass | **加强**：暗色审计 |
| **G6.1** | S7 末 | 暂停 S8，先做 i18n / a11y | **新增**：Lighthouse ≥ 95 |
| **G7** | S8 末 | 不发版 | **最终**：生产可发版 |

---

## 5. V10 新增风险登记

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| V10-R1 | UI 1:1 复现遗漏 | 中 | Chromatic 视觉基线 + Playwright 像素比对 |
| V10-R2 | Vite 切框架后 Next.js 能力失效 | 中 | Sprint 4 处理（i18n 用 react-intl） |
| V10-R3 | Zustand persist 与 SSR 冲突 | 低 | 客户端守卫 |
| V10-R4 | TanStack Query 5 与 React 19 兼容 | 低 | 锁定 5.59.x 稳定版 |
| V10-R5 | RHF + Zod 类型推导慢 | 低 | `z.infer<typeof Schema>` |
| V10-R6 | LLM 4 模 provider 适配 | 中 | 抽象统一接口；Sprint 3 末 4 模实测 |
| V10-R7 | SSE 流式与 TanStack Query 兼容 | 中 | Zustand 增量更新 + onMutate |
| V10-R8 | Chromatic 商业配额 | 低 | 8 sprint × 1 次 = 8 次（S2-S8 各 1 次） |
| V10-R9 | 整体重写工期超 V2 | 低 | 保留 11d 缓冲；S2 中期 gate 评估 |
| V10-R10 | 后台页面工期紧张 | 中 | S8 合理化到 10d |

---

## 6. 团队配置（V10 不变）

| 角色 | 数量 | 占比 | 主要 sprint |
|---|---|---|---|
| 前端主程（Vite + React 19） | 1 | 60% | 全程 |
| UI/交互设计师 | 0.3 | 15% | S1 / S4-S6 |
| 后端联调 | 0.3 | 15% | S2-S4 |
| QA / a11y | 0.2 | 10% | S4-S7 |
| DevOps | 0.1 | 5% | S4 |

---

## 7. 监控与汇报机制

- **每日**：sprint board 更新（按任务 ID 标 in_progress / done）
- **每 sprint 末**：Demoable Build + 风险闸门报告（30 分钟会议）
- **S2/S4/S6/S8 末**：里程碑汇报（含 Lighthouse / axe / e2e / **Chromatic** 截图）
- **S8 末**：上线发布 + 复盘文档

---

## 8. 与上游文档的对齐（V10 更新）

| 文档 | 状态 |
|---|---|
| 任务清单基线 | `FRONTEND_TASK_LIST_2026-07-02_V2.md`（V2）→ **V10 选项 B 已合并到 SPRINT_2-8** |
| **V10 决策文档** | `V10_REFACTOR_STRATEGY_UI_VS_TECH.md` ⭐ 新增 |
| 技术决策依据 | `FRONTEND_REFACTOR_PLAN_2026-07-02.md` |
| 质量基线 | `REVIEW_REPORT_2026-07-02_SENIOR_DEVELOPER.md` |
| Sprint 1 closeout | `SPRINT_1_CLOSEOUT_2026-07-03.md` ✅ |
| Sprint 2-8 文档 | **已重写为 V10 选项 B** ⭐ |

---

## 9. V10 工时对比汇总

```
Sprint | V2 估时 | V10 估时 | 节省 | 关键变化
S1     | 11d    | 11d      | 0    | 已完成
S2     | 18d    | 9.5d     | -8.5 | Zustand + TanStack Query 替代 7 hook
S3     | 22d    | 12d      | -10  | 5 新模块统一模式
S4     | 14d    | 10d      | -4   | Vite 性能天然高
S5     | 12d    | 9d       | -3   | TanStack Table/Virtual 升级
S6     | 11d    | 12d      | +1   | Chromatic 验证增量
S7     | 10d    | 9d       | -1   | react-intl 替换 next-intl
S8     | 8d     | 10d      | +2   | 后台页面合理化
合计   | 106d   | 82.5d    | -10  | 净节省 10 人天
缓冲   | 14d    | 11d      | -3   |
总计   | 92d + 14 = 106d | 82d + 11 = 93d |
```

---

## 10. 下一步

**V10 路线图编制完成**。请确认：
1. ✅ Sprint 2-8 文档已按 V10 选项 B 重写
2. ✅ V10 决策文档已归档
3. ✅ 路线图已更新

**等待 PM 确认**：
- 立即启动 Sprint 2（T-A-14 Vitest + Chromatic 配置）？
- 或先审阅 V10 文档后决策？

---

**V10 路线图版本**：v1.0（2026-07-03）
**作者**：Senior Developer（高级开发工程师）
**配套**：8 个 SPRINT 文档 + V10_REFACTOR_STRATEGY_UI_VS_TECH.md
