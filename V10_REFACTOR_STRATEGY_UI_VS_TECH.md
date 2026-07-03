# V10 重构策略：UI/交互层与技术层解耦（2026-07-03）

> **核心原则（PM 拍板）**：
> > "原型主要确定 UI 和交互，我们重构前端时要用原型的 UI 和交互，可以不适用原型的技术。"
>
> **含义**：原型是 **UI/交互的行为规约**（行为契约），不是 **代码模板**。技术栈完全开放。

---

## 0. 与 V1 / V2 报告的关键差异

| 维度 | V1 / V2 假设 | V10 修正 |
|---|---|---|
| 原型代码 | "保留为主，只重构集成" | **可整体重写**，但 UI/交互 1:1 复现 |
| React 19 | "沿用" | **可选**：Vue 3 / Svelte 5 / Solid 都可以 |
| useChat 单体 hook | "分解成 5 个子 hook" | **可选**：保留/Zustand/Jotai/Redux Toolkit 都可以 |
| `any` 类型 33 处 | "降级到 warn，逐步修" | **直接清零**：重写时使用严格类型 |
| 7 个原型 lib 文件 | "提取到 packages/lib" | **可丢弃**：业务逻辑重新按 API 端点重写 |
| ESLint 49 warning | "Sprint 1 降级 + Sprint 2 修" | **直接消除**：新代码按严格规范写 |
| 评估总工时 | 66-89 人天 | **修正 50-70 人天**（节省的 16-19d 来自：删 `any` 修复 + 7 文件重写 + 6 个手写 hook 重构） |

---

## 1. 双层模型：UI/交互层 × 技术层

```
┌────────────────────────────────────────────────────────┐
│  Layer A · UI/交互契约层（🔒 锁定，1:1 复现）              │
│  ────────────────────────────────────────────────────  │
│  • 12 个 UI 不变量（见 FRONTEND_REFACTOR_PLAN §3.1）     │
│  • 8 个核心组件视觉规范（PlanCard 3-Tab、ModeIndicator 4  │
│    mode 决策树、FormCard 3-step guards、Badge 状态映射）  │
│  • 1024px 断点、48px 移动端导航、SafeMarkdown XSS 防护   │
│  • Design Token（247 行 design-system.css 100+ 变量）   │
│  • 暗/亮/系统三主题切换 + 1.2s 缓动                     │
│  • Flash 防护：theme-script + ThemeProvider SSR/CSR 一致 │
│  • Typing 动画（思考指示器三态：思考中/已暂停/已停止）   │
│  • 移动端手势（下拉刷新、虚拟键盘适配、安全区）          │
│  ────────────────────────────────────────────────────  │
│  ★ 验收：Playwright 视觉回归 + Chromatic 像素级 diff      │
│  ★ 验收：axe-core 0 critical / 0 serious                 │
└────────────────────────────────────────────────────────┘
                          △ 契约接口
                          │
┌─────────────────────────▽──────────────────────────────┐
│  Layer B · 技术实现层（🔓 完全开放，按 Sprint 选型）       │
│  ────────────────────────────────────────────────────  │
│  B1. 框架：Next.js 16 / Vite+React 19 / Nuxt 3 /       │
│       SvelteKit 2 / SolidStart 1（任选）                │
│  B2. 状态：Zustand 4 / Jotai 2 / Redux Toolkit 2 /      │
│       Pinia 2 / 自定义 store（任选）                    │
│  B3. 数据：TanStack Query 5 / SWR 2 / Apollo 4 /       │
│       tRPC 11（任选）                                  │
│  B4. 表单：React Hook Form 7 / Formik 2 / VeeValidate  │
│  B5. 测试：Vitest 2 / Jest 29 / Playwright 1.55（统一）  │
│  B6. 构建：Turborepo 2.10 / Nx 20 / Lerna 8（任选）     │
│  B7. 样式：Tailwind 4 / vanilla-extract / CSS Modules / │
│       Panda CSS / UnoCSS（任选，保持 design token 一致）│
│  B8. 类型：TypeScript 5（统一）/ JSDoc（备选）           │
│  ────────────────────────────────────────────────────  │
│  ★ 验收：typecheck 0 error / lint 0 error / test 100%   │
│  ★ 验收：bundle < 300KB gzip / LCP < 2.5s / CLS < 0.1  │
└────────────────────────────────────────────────────────┘
```

---

## 2. UI/交互契约 · 12 项不变量（必须 1:1 复现）

> 来源：`FRONTEND_REFACTOR_PLAN_2026-07-02.md` §3.1，已通过原型实测验证。

### 2.1 布局不变量（4 项）

| # | 不变量 | 实测值 | 验收方式 |
|---|---|---|---|
| L1 | 桌面断点 | `≥ 1024px` 显示侧栏三栏布局 | Playwright viewport=1280 |
| L2 | 移动断点 | `< 768px` 单栏 + 底部 Tab 导航（48px 高） | Playwright viewport=375 |
| L3 | 中间断点 | `768-1023px` 双栏，导航折叠为顶部抽屉 | Playwright viewport=900 |
| L4 | 容器宽度 | `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8` | 视觉回归 |

### 2.2 组件不变量（4 项）

| # | 组件 | 关键行为 | 来源文件 |
|---|---|---|---|
| C1 | **PlanCard 3-Tab** | "院校 / 专业 / 就业" Tab 切换不重渲染父组件 | `src/components/PlanCard.tsx` |
| C2 | **ModeIndicator 4-mode 决策树** | chat-mode / plan-mode / review-mode / share-mode 互斥显示，决策延迟 < 50ms | `src/components/ModeIndicator.tsx` |
| C3 | **FormCard 3-step guards** | step 1→2 需 score 输入；step 2→3 需选科+位次；后退保留数据 | `src/components/FormCard.tsx` |
| C4 | **Badge 8 态映射** | 985/211/双一流/省重点/普通本科/专科/提前批/征集，颜色 + 图标对应 | `src/components/Badge.tsx` |

### 2.3 行为不变量（2 项）

| # | 行为 | 验收 |
|---|---|---|
| B1 | **Typing 动画三态** | "AI 正在思考"旋转 / "已暂停"静止 / "已停止"隐藏 | Playwright trace |
| B2 | **SafeMarkdown XSS 防护** | `<script>` / `onerror` / `javascript:` 全部过滤 | unit test + xss-payload 库 |

### 2.4 设计系统不变量（2 项）

| # | 不变量 | 来源 |
|---|---|---|
| D1 | **247 行 design-system.css 100+ token** | `src/styles/design-system.css` |
| D2 | **三主题切换 + 1.2s 缓动 + SSR/CSR 一致** | `src/styles/globals.css` + `src/components/ThemeProvider.tsx` |

---

## 3. 技术选型决策菜单（Sprint 2 启动前必选）

PM 需要在 Sprint 2 启动前从以下 8 个轴中做选择（或选"沿用原型"）：

### 选项 A：沿用原型技术栈（最小风险）
```
Next.js 16 + React 19 + TypeScript 5 + Tailwind 4 + 自定义 useChat
工时：~50 人天（节省技术调研）
风险：低（已在 Sprint 1 验证 G0）
```

### 选项 B：现代化重写（推荐 ★）— 与 V2 任务清单一致
```
Vite 5 + React 19 + TypeScript 5 + Tailwind 4
+ Zustand 4（替代 7 个手写 hook）
+ TanStack Query 5（数据获取）
+ React Hook Form 7（表单）
+ Vitest 2 + Playwright 1.55
工时：~58 人天（多 8d 调研/重写，节省 16d `any` 修复 + 6 hook 重构）
净节省：8 人天
风险：中（需 Chromatic 全量视觉回归）
```

### 选项 C：激进换框架（最大创新）
```
Nuxt 3 + Vue 3.5 + TypeScript 5 + Pinia 2
+ VueUse 11（替代 7 个手写 hook）
+ TanStack Query 5（Vue 版）
+ VeeValidate 4
+ Vitest 2 + Playwright 1.55
工时：~68 人天（多 18d 框架迁移）
风险：高（团队 Vue 经验需评估）
```

### 选项 D：性能优先（高 LCP 压力场景）
```
Astro 5 + React 19 岛模式 + TypeScript 5
+ Zustand 4 + TanStack Query 5
工时：~72 人天
风险：低（岛模式天然 SSR + 局部 hydrate）
```

### 选项 E：保留 Next.js + 改状态管理
```
Next.js 16 App Router + React 19 Server Components
+ Zustand 4（client store）
+ TanStack Query 5
工时：~55 人天
风险：低-中
```

---

## 4. Sprint 2-8 计划修正矩阵

| Sprint | 主题 | V2 估时 | V10 估时（选项 B） | 关键变化 |
|---|---|---|---|---|
| **S1** Foundation | monorepo + 5 基础组件 | 11d | 11d | ✅ 已完成 |
| **S2** API Hooks | 5 模块 × 3 hook = 15 个 | 12d | **9d** | Zustand store 替代 15 个手写 hook |
| **S3** New Modules | 5 个新模块（Share/Query/Review/LLM/Poster） | 14d | **12d** | 删 `any` 同步重写 + TanStack Query |
| **S4** Perf/Ops | 性能优化 + 监控 | 10d | 10d | 不变 |
| **S5** Components | 高级组件（DataTable/Tree/Chart） | 11d | **9d** | TanStack Virtual + TanStack Table |
| **S6** Query/Review | 查询/审核 UI | 12d | 12d | 不变 |
| **S7** A11y/Portal | 无障碍 + 招生门户 | 10d | 9d | axe-core CI 集成 |
| **S8** Admin/Policy | 后台 + 政策合规 | 12d | 10d | 简化的 RHF 表单 |
| **合计** | | **92d** | **82d** | 节省 10 人天 |

> 注：Sprint 2 节省 3d / Sprint 3 节省 2d / Sprint 5 节省 2d / Sprint 7 节省 1d / Sprint 8 节省 2d = 10d。
> V2 任务清单的 14 个新模块任务依然有效，但实现路径从"修原型"变为"重写 + 严格类型"。

---

## 5. 关键问题清单（V10 启动前 PM 必答）

### Q1：技术栈选哪个？
- A：沿用原型
- **B：Vite+React+Zustand+TanStack Query+RHF（推荐）** ★
- C：Nuxt+Vue+Pinia
- D：Astro 岛模式
- E：Next.js + Zustand

### Q2：UI/交互层验收方式？
- Playwright 视觉回归 + Chromatic 像素 diff（推荐 ★）
- 仅人工抽查（不推荐）
- 第三方视觉测试（如 Percy）

### Q3：原型代码处置？
- **整体重写为新实现（推荐 ★）**：UI 1:1 + 严格类型 + 现代状态管理
- 保留 + 局部重构：保留 useChat 单体 hook，渐进式重构
- 二者并行：保留原型做 A/B 对照

### Q4：Sprint 2 启动条件？
- Q1 选定 + Q2 选定 + Q3 选定后方可启动
- 默认值：推荐 B + Chromatic + 整体重写

### Q5：是否需要更新所有 Sprint 2-8 文档？
- **是（推荐 ★）**：根据技术选型重新拆分子任务，避免 S2 启动后再发现颗粒度问题
- 否：保持 V2 文档，按当前颗粒度执行，遇到问题再调整

---

## 6. 与 V2 任务清单的关系（V10 = V2 选型版）

```
V1（基础）→ V2（+14 人天，5 新模块）→ V10（+技术选型 + UI/交互契约锁定）
   ↓              ↓                          ↓
方案层          任务层                    决策层
```

**V10 输出的决策**将作为 Sprint 2 启动的输入。一旦 PM 选定 Q1-Q3，所有 Sprint 2-8 子任务将按选定技术栈重新拆解，颗粒度仍为 0.25 人天。

---

## 7. 建议执行顺序

```
1. PM 审阅 V10 文档（当前）
2. PM 决策 Q1-Q5（5 分钟）
3. 高级开发工程师根据决策更新 SPRINT_2-8 文档（2 人天）
4. 启动 Sprint 2（按更新后的子任务执行）
5. 每个 Sprint 完成后做 Chromatic 视觉回归 + axe-core + bundle 体积报告
```

---

## 8. 风险登记（V10 特有）

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| V10-R1 | UI 1:1 复现遗漏 | 中 | Chromatic 全量视觉基线 + Playwright 像素比对 |
| V10-R2 | 新技术栈团队不熟 | 中 | Sprint 2 前 1d spike（小型 PoC） |
| V10-R3 | 整体重写工期超 V2 估时 | 低 | 保留 7d 缓冲；S2 中期 gate 评估 |
| V10-R4 | 与后端 API 契约错位 | 中 | OpenAPI 自动生成类型 + MSW mock |
| V10-R5 | 设计 token 在新栈丢失 | 中 | 设计 token 在 D1 中提前抽取至 packages/ui/tokens |

---

## 9. 决策记录

| 日期 | 决策 | 决策人 | 影响 |
|---|---|---|---|
| 2026-07-03 | 原型只锁 UI/交互，不锁技术 | PM | V10 文档出，V1-V2 重构范围调整 |
| 待定 | Q1-Q5 5 项决策 | PM | Sprint 2-8 文档更新 + 启动 |

---

**V10 文档状态**：草稿 v1，待 PM 决策 Q1-Q5
**下一步**：等待 PM 决策（建议选项 B + Chromatic + 整体重写 + 是更新文档）
