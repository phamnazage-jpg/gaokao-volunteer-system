# V2 任务清单执行路线图 — 92 人天 / 8 Sprint 拆分

> 配套文档：`FRONTEND_TASK_LIST_2026-07-02_V2.md`（136 任务 / 92 人天）
> 编制日期：2026-07-02 22:55
> 编制人：Senior Developer（执行规划）
> 批准状态：PM 已批准追加 14 人天预算

## 1. 路线图设计原则

| 原则 | 落地方式 |
|---|---|
| **垂直切片** | 每 sprint 都有可演示产物，不做"建库 2 周后再做页面" |
| **风险前置** | B 阶段（最大风险 38 人天）放第 2-3 sprint，D 阶段视觉与 B 阶段并跑 |
| **依赖显式化** | 跨 sprint 任务标 ❗，并行任务标 ⚡ |
| **可中断性** | 每 sprint 末交付"Demoable Build"，PM 可中止而不丢已投入工作 |
| **能力对齐** | 每 sprint 必跑 Lighthouse / axe / Playwright 三件套 |

## 2. 8-Sprint 路线图（4 周一档，共 16 周 ≈ 4 个月）

> 假设：1 个前端主程 + 1 个后端联调支持 + 0.5 个设计 review
> 单 sprint 容量：~12 人天（按 5 天 × 0.85 效率 × 2.5 人 = 10.6 人天取整）

| Sprint | 周次 | 阶段 | 任务数 | 人天 | 关键交付 | Demoable 产物 |
|---|---|---|---|---|---|---|
| **S1** | W1 | A 前半 | 8 | 11 | monorepo + 5 组件 + CI | 5 页面原貌复刻 + CI 绿灯 |
| **S2** | W2-3 | A 后半 + B 启动 | 17 | 18 | OpenAPI codegen + 8 核心 hook | 30+ 端点 TypeScript 类型 + chat 流式 e2e |
| **S3** | W4-5 | B 主体 | 22 | 22 | 真实对接 + LLM fallback + Share | 完整 chat/plan 真实流，含 4 模 fallback |
| **S4** | W6-7 | B 收口 + C 启动 | 17 | 14 | Lighthouse ≥90 + Poster CLI 接入 | 性能报告 + Sentry + CSP 通过 |
| **S5** | W8-9 | C 收口 + D 启动 | 18 | 12 | 独立部署 + SharePanel | 灰度环境可访问 + Share 弹窗 3 状态 |
| **S6** | W10-11 | D 主体 | 22 | 11 | 18 组件 + DataQuery + Review UI | 全部页面视觉与 a11y 验收 |
| **S7** | W12-13 | D 收口 + E 启动 | 16 | 10 | axe 0 critical + Review 页 4 按钮 | 3 个 portal 页面 React 化 |
| **S8** | W14-16 | E 主体 | 14 | 8 | 6 个内部页 + Policy + Poster 渲染 | 全量运营后台可访问 |
| **合计** | 16 周 | — | **136** | **92 + 14 缓冲** | — | 生产可发版 |

> 8 sprint 总容量 92 人天 + 14 缓冲 = 106 人天。按 4 人/16 周实际可投 = 64 人天 → **结论：单兵执行需 22 周，多人 16 周可完成。**

## 3. Sprint 详图

### S1（W1）— 11 人天 · 阶段 A 前半

**入口条件**：PM 批准 14 人天预算完成
**目标**：让原型在 monorepo 里能跑起来，CI 灯绿

| 任务 | 人天 | 并行 | 备注 |
|---|---|---|---|
| T-A-01 monorepo 创建 | 0.5 | — | pnpm + Turborepo |
| T-A-02 收编前端原型 | 0.5 | — | 软链接 + tsconfig |
| T-A-03 共享包骨架 | 0.5 | — | @app/ui / @app/lib / @app/api |
| T-A-06 设计 token 提取 | 0.5 | ⚡ |
| T-A-07 组件库首批 5 组件 | 1.0 | — |
| T-A-21 OpenAPI Codegen 接入 | 1.0 | — | V2 跑出 30+ 端点类型 |
| T-A-23 CI 工作流 | 1.5 | — | lint + test + build |
| T-A-04 tsconfig 共享 | 0.5 | ⚡ |
| T-A-14 Vitest 骨架 | 0.5 | ⚡ |
| T-A-18 Playwright 骨架 | 0.5 | ⚡ |

**退出条件**：
- [ ] `pnpm dev` 可启动 `apps/web` 5 个页面
- [ ] `pnpm test` 跑通
- [ ] `pnpm build` 通过
- [ ] GitHub Actions 绿
- [ ] **无 mock 数据残留**（原型中的 `chat-fixtures.ts` 移走）

---

### S2（W2-3）— 18 人天 · A 后半 + B 启动

**入口条件**：S1 退出
**目标**：8 个核心 hook 真实化，OpenAPI 类型贯通

| 任务 | 人天 | 并行 | 备注 |
|---|---|---|---|
| T-A-22 OpenAPI 类型生成完成 | 1.0 | — | 30+ 端点全部生成 |
| T-A-08-T-A-13 6 组件扩展 | 3.0 | ⚡ | 12 组件总量 |
| T-A-15 单元测试 50% | 1.0 | ⚡ |
| T-A-19 Playwright 首批 3 e2e | 1.0 | ⚡ |
| T-A-16 集成测试 30% | 1.0 | ⚡ |
| T-A-20 Storybook | 1.0 | ⚡ |
| **T-B-01~08** chat 流式对接 | 4.0 | — | SSE + 重连 + 取消 |
| **T-B-09~14** plan/audit 真实化 | 3.0 | — |
| T-A-05 ESLint/Prettier 收口 | 0.5 | ⚡ |
| T-A-17 性能预算 CI | 0.5 | ⚡ |

**退出条件**：
- [ ] Chat 流式 e2e 真实后端可跑通
- [ ] Plan/Audit 8 hook 全部对接真实 API
- [ ] OpenAPI 30+ 端点无 `any` 残留
- [ ] 单元测试覆盖率 ≥50%

---

### S3（W4-5）— 22 人天 · B 主体

**入口条件**：S2 退出
**目标**：全部 35 端点对接完成，含 5 大 V2 新模块

| 任务 | 人天 | 并行 | 备注 |
|---|---|---|---|
| **T-B-15~18** Share Link API 对接 | 3.0 | — | 4 端点 + QR 渲染 ❗ |
| **T-B-19~22** Data Query 4 端点 | 3.0 | — |
| **T-B-23~26** Review Flow 4 端点 | 3.0 | — | step1 + 冲稳保按钮 |
| **T-B-27~30** LLM 增强 + 多模型 fallback | 4.0 | — | 4 模 + SSE 重连 ❗ |
| **T-B-31~35** Poster 渲染 + 政策页 | 3.0 | — |
| T-B-11 错误边界全局化 | 1.0 | ⚡ |
| T-B-12 Loading/Toast 统一 | 1.0 | ⚡ |
| T-B-13 离线兜底策略 | 1.0 | ⚡ |
| T-B-14 表单 RHF+Zod 接入 | 2.0 | ⚡ |
| T-B-07 mock 数据清理 | 0.5 | ⚡ |
| T-B-08 端到端联调 | 0.5 | ⚡ |

**退出条件**：
- [ ] 35 端点 e2e 全绿
- [ ] LLM fallback 4 模模拟可切换
- [ ] Share link 生成/打开可闭环
- [ ] 全部 mock 移除
- [ ] **风险闸门**：R-NEW-7（LLM 超时）实测 < 30s

---

### S4（W6-7）— 14 人天 · B 收口 + C 启动

**入口条件**：S3 退出
**目标**：性能达标，监控接入

| 任务 | 人天 | 并行 | 备注 |
|---|---|---|---|
| T-B 收尾 + Lighthouse 调优 | 3.0 | — | ≥90 性能分 |
| **T-C-01~04** 独立部署 + Sentry | 2.0 | — |
| **T-C-05~07** CSP + 安全头 | 1.5 | ⚡ |
| **T-C-08~10** Poster CLI 接入 | 2.0 | — | 风险 R-NEW-8 ❗ |
| **T-C-11~12** 灰度发布 + 灰度路由 | 1.5 | ⚡ |
| T-C-13 性能监控 RUM | 1.0 | ⚡ |
| T-C-14 错误追踪 | 1.0 | ⚡ |
| T-C-15 部署文档 | 1.0 | ⚡ |
| D 阶段预研：design pass (R-NEW-9) | 1.0 | — | 风险闸门 |

**退出条件**：
- [ ] Lighthouse Performance ≥90 / A11y ≥95
- [ ] Sentry 接收到测试事件
- [ ] CSP 报告 0 violation
- [ ] 灰度发布可路由
- [ ] **风险闸门**：R-NEW-8（Poster CLI 镜像验证）通过

---

### S5（W8-9）— 12 人天 · C 收口 + D 启动

**入口条件**：S4 退出 + Design pass 完成
**目标**：18 组件 + SharePanel 基础

| 任务 | 人天 | 并行 | 备注 |
|---|---|---|---|
| T-C 收尾 2 任务 | 1.0 | — |
| **T-D-01~05** 5 组件 design system | 2.5 | ⚡ |
| **T-D-06~10** 5 业务组件 | 2.5 | ⚡ |
| **T-D-11~14** 4 反馈组件 | 2.0 | ⚡ |
| **T-D-15~18** 4 容器组件 | 2.0 | ⚡ |
| T-D-19 SharePanel 弹窗 | 2.0 | — | 3 状态 (生成/复制/失效) |

**退出条件**：
- [ ] 18 组件 Storybook 全部可查
- [ ] SharePanel 弹窗 3 状态 e2e 通过
- [ ] **风险闸门**：R-NEW-9（Portal 视觉一致性）已对齐

---

### S6（W10-11）— 11 人天 · D 主体

**入口条件**：S5 退出
**目标**：DataQuery + Review UI 全部页面

| 任务 | 人天 | 并行 | 备注 |
|---|---|---|---|
| **T-D-20~23** DataQuery 4 页面 | 2.0 | — |
| **T-D-24~27** Review UI 4 状态 | 2.0 | — | step1 + 冲稳保 + token 加载 |
| T-D-28 主题切换持久化 | 0.5 | ⚡ |
| T-D-29 暗色模式适配 | 0.5 | ⚡ |
| T-D-30 焦点环统一 | 0.5 | ⚡ |
| T-D-31 prefers-reduced-motion | 0.5 | ⚡ |
| T-D-32 键盘导航 | 0.5 | ⚡ |
| T-D-33~35 视觉 QA 3 轮 | 1.5 | ⚡ |
| T-D-36 风险面板 | 1.0 | ⚡ |
| T-D-37 LLM 失败兜底 UI | 1.0 | ⚡ |
| T-D-38 错误页统一 | 1.0 | ⚡ |

**退出条件**：
- [ ] DataQuery 4 页面真实数据流通
- [ ] Review 4 状态全跑通
- [ ] axe-core 0 critical issue
- [ ] prefers-reduced-motion 全部组件支持

---

### S7（W12-13）— 10 人天 · D 收口 + E 启动

**入口条件**：S6 退出
**目标**：a11y 完整合规，3 个 portal 页面 React 化

| 任务 | 人天 | 并行 | 备注 |
|---|---|---|---|
| T-D 收尾 3 任务 (axe 0 critical / 屏幕阅读器测试 / WCAG 报告) | 1.5 | — |
| **T-E-01~04** 后台登录 + 导航 | 2.0 | — |
| **T-E-05~08** Share 管理 + Data Query 后台 | 2.0 | — |
| **T-E-09~12** Review 后台 + Poster 渲染 | 2.0 | — |

**退出条件**：
- [ ] axe-core 0 critical，0 serious
- [ ] 3 个 portal 页面（运营 / Share / Data Query）可访问
- [ ] 后台登录 + RBAC 工作

---

### S8（W14-16）— 8 人天 · E 主体

**入口条件**：S7 退出
**目标**：6 个内部页 + Policy + Poster 完整

| 任务 | 人天 | 并行 | 备注 |
|---|---|---|---|
| T-E-13~16 我的订单 + 我的报告 | 1.5 | — |
| T-E-17~20 Policy 5 页 (服务/隐私/退订/合规/关于) | 2.0 | — |
| T-E-21~23 Poster 渲染页 + 下载 | 1.5 | — |
| T-E-24 联调收口 + 灰度上线 | 3.0 | — |

**退出条件**：
- [ ] 6 个内部页全部可访问
- [ ] 5 个 Policy 页发布
- [ ] Poster 可生成可下载
- [ ] **生产可发版** ✅

## 4. 关键风险闸门（不能跳过）

| 闸门 | 位置 | 失败动作 |
|---|---|---|
| **G1**: OpenAPI 类型生成无 `any` | S2 末 | 暂停 S3，补 codegen 配置 |
| **G2**: LLM fallback 4 模实测 | S3 末 | 暂停 S4，与后端对齐超时策略 |
| **G3**: Lighthouse ≥90 | S4 末 | 暂停 S5，先做性能调优 |
| **G4**: R-NEW-8 Poster CLI 镜像验证 | S4 末 | 暂停 S5，修正 Dockerfile |
| **G5**: axe 0 critical | S7 末 | 暂停 S8，先做 a11y |
| **G6**: R-NEW-9 视觉一致 | S5 末 | 暂停 S6，先做 design pass |

## 5. 团队配置推荐

| 角色 | 数量 | 占比 | 主要 sprint |
|---|---|---|---|
| 前端主程（Next.js + TS） | 1 | 60% | 全程 |
| UI/交互设计师 | 0.3 | 15% | S1 / S4-S6 |
| 后端联调 | 0.3 | 15% | S2-S4 |
| QA / a11y | 0.2 | 10% | S4-S7 |
| DevOps | 0.1 | 5% | S4 |

## 6. 监控与汇报机制

- **每日**：sprint board 更新（按任务 ID 标 in_progress / done）
- **每 sprint 末**：Demoable Build + 风险闸门报告（30 分钟会议）
- **S2/S4/S6 末**：里程碑汇报（含 Lighthouse / axe / e2e 截图）
- **S8 末**：上线发布 + 复盘文档

## 7. 与上游文档的对齐

- 任务清单基线：`FRONTEND_TASK_LIST_2026-07-02_V2.md`
- 技术决策依据：`FRONTEND_REFACTOR_PLAN_2026-07-02.md`
- 质量基线：`REVIEW_REPORT_2026-07-02_SENIOR_DEVELOPER.md`
- 历史对照：`docs/REVIEW_REPORT_2026-06-19_SYSTEMATIC_PRODUCTION_READINESS_REVIEW.md`

---

**路线图编制完成。请确认是否进入 S1 启动。**
