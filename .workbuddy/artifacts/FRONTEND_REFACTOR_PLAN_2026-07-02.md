# 前端重构方案 · Frontend Refactoring Plan

> 评审人：**Frontend Developer (资深前端开发工程师)**
> 日期：2026-07-02
> 输入约束：
> - **UI 与交互**：严格采用 `前端原型代码/` 中已落地的设计（不容许外观/行为回归）
> - **技术栈**：由前端专家决定（推荐方案附后）
> 上游依据：`REVIEW_REPORT_2026-07-02_SENIOR_DEVELOPER.md`（V2 全面版）
> 上游审查：4,114 行 TS/TSX、8 页 / 7 组件 / 8 hooks / 247 行 design-system.css 已扫读

---

## 0. TL;DR

**核心判断：原型代码的 UI 与交互已经过一轮有意识的设计打磨（247 行 design-system、三态主题、消息路由模式、信息收集进度条、冲稳保三 Tab、风险徽章、紧凑移动端），可以直接收编为 monorepo 中的 `apps/web` 子项目，并补齐三件缺失物：测试基础设施 / 真实后端对接 / 可维护的 UI 组件库。**

**技术栈决策（前端专家决定）**

| 层 | 选型 | 理由 |
|---|---|---|
| 框架 | **Next.js 16.x（App Router）** | 沿用原型，避免重新评估 |
| UI 运行时 | **React 19.x** | 沿用原型，与 Next 16 协同验证 |
| 语言 | **TypeScript 5.x（strict）** | 沿用原型 |
| 样式 | **Tailwind CSS 4 + design-system.css tokens** | 沿用原型 + CSS 变量映射 |
| 客户端状态 | **Zustand（4.x）** | hook 数量从 8 → 20+ 时避免 prop drilling |
| 服务端状态 | **TanStack Query 5.x** | 替换 localStorage 缓存 + 真实 API 同步 |
| 表单 | **React Hook Form + Zod** | FormCard 已 374 行，缺类型安全 |
| API 客户端 | **openapi-typescript-codegen** | 基于 `admin/app.py` OpenAPI 自动生成 |
| Markdown | **react-markdown 10 + rehype-sanitize 6 + remark-gfm 4** | 沿用（XSS 安全） |
| 单元测试 | **Vitest 2.x + React Testing Library** | 与 Vite 生态契合 |
| E2E 测试 | **Playwright 1.5x** | 跨浏览器，移动/桌面双视图 |
| 视觉回归 | **Chromatic / Storybook Test** | design token 改动安全网 |
| 国际化 | **next-intl 3.x** | `lang="zh-CN"` 起步，预留 en-US |
| 监控 | **Sentry（前端） + Vercel Analytics / Web Vitals** | Core Web Vitals 预算 |
| 构建 | **Turborepo + pnpm workspaces** | monorepo 编排 |
| 包管理 | **pnpm 9.x** | 节省磁盘，提升 monorepo 性能 |

**为什么不用 Vite + React Router 替代 Next.js？** ① 沿用原型决策可避免一轮"无收益的技术换血"；② Next 16 的 RSC + Server Actions 对未来**公开门户 SEO 优化**（`/pricing` `/privacy`）有结构性优势；③ 部署可走 CloudStudio 预览或自托管，对小团队更轻。

**为什么加 Zustand？** ① 当前 8 个 hook 已经够用，但 B 阶段接入真实后端后会膨胀；② TanStack Query 已覆盖 90% 服务端状态，Zustand 只承担"跨页 UI 状态"（主题、侧边栏折叠、对比选择）；③ 比 Redux Toolkit 少 70% 模板代码。

**为什么加 TanStack Query 而非 SWR？** ① mutation / optimistic update / infinite query 能力更全；② DevTools 体验对调试 `useChat` 状态机更友好。

---

## 1. UI / 交互不变量（强约束）

> **本节是迁移的"宪法"——所有后续 PR 必须满足这些不变量，不允许任何"看起来更优"的越权修改。**

### 1.1 视觉设计系统（来自 `前端原型代码/src/styles/design-system.css`）

#### 1.1.1 品牌色（9 阶）
```
--brand-50  #eff6ff  --brand-500 #3b82f6  --brand-900 #1e3a8a
--brand-gradient: linear-gradient(135deg, --brand-600 → #7c3aed)
```
**保留**：原型已有 `bg-gradient-to-br from-blue-600 to-purple-600`（Logo / 头像）—— 不替换为单色。

#### 1.1.2 业务语义色
```
录取概率: rush #f97316 / stable #3b82f6 / safe #22c55e
风险等级: high #ef4444 / medium #eab308 / low #22c55e
风险背景: high-bg #fef2f2 / medium-bg #fefce8 / low-bg #f0fdf4
风险边框: high-border #fecaca / medium-border #fef08a / low-border #bbf7d0
```
**保留**：暗色主题下需调整 `--color-risk-*-bg` 为 `rgba(..., 0.15)` 透明度（原型已做，迁移时不动）。

#### 1.1.3 排印 / 间距 / 圆角 / 动效
```
font-sans: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei"…
text: 7 阶（xs 0.75 / sm 0.875 / base / lg / xl / 2xl / 3xl）
space: 11 阶（0 ~ 16），4px 基准
radius: 6 阶（sm 0.375 / md 0.5 / lg 0.75 / xl 1 / 2xl 1.25 / full 9999）
transition: 4 阶（fast 150ms / normal 250ms / slow 350ms / spring cubic-bezier(0.34, 1.56, 0.64, 1)）
```
**保留**：原型已有"圆角 2xl = 卡片"，"full = 胶囊徽章"—— 不替换为 shadcn 的 `rounded-md` 默认值。

### 1.2 三态主题系统（来自 `lib/theme.ts` + `components/shared/ThemeToggle.tsx`）

| 模式 | 行为 | 持久化 | 触发 |
|---|---|---|---|
| `light` | `data-theme="light"` | localStorage `theme=light` | 用户点击 ☀️ |
| `dark` | `data-theme="dark"` | localStorage `theme=dark` | 用户点击 🌙 |
| `system` | 移除 `data-theme` 属性，由 `@media (prefers-color-scheme: dark)` 接管 | localStorage 移除 key | 用户点击 💻 |

**关键不变量**：
- ✅ **`initThemeScript()` 必须在 `<head>` 内联同步执行**（防 FOUC 闪白）—— `app/layout.tsx:20` 已挂载
- ✅ **ThemeToggle 是 `role="radiogroup"`，三个按钮 `role="radio"` `aria-checked`** —— 不能改成下拉框
- ❌ **不允许"跟随系统"自动覆盖 localStorage** —— 用户的显式选择必须保留
- ❌ **不允许去掉 `suppressHydrationWarning`** —— 这是闪白防护的必要条件

### 1.3 消息路由模式（来自 `components/ChatMessage.tsx`）

```ts
type MessageType = 'text' | 'form_card' | 'plan_card' | 'career_card' | 'audit_report' | 'file_upload_prompt' | 'system';
```

**ChatMessage 不允许变成"自由渲染"** —— 必须按 `message.type` 路由到对应子组件（PlanCard / CareerCard / AuditReportCard / FormCard / FileUploadPrompt / SafeMarkdown）。

**不变量**：
- ✅ 用户消息：`flex justify-end` + `bg-blue-600 text-white` + 圆角 `rounded-2xl rounded-br-md`
- ✅ AI 消息：`flex items-start gap-3` + AI 头像（蓝→紫渐变） + 圆角 `rounded-2xl rounded-tl-md`
- ✅ 系统消息：居中灰底胶囊
- ❌ **不允许出现"消息卡片之间不留 16px 间距"** —— `mb-4 px-4`

### 1.4 模式指示器（来自 `components/navigation/ModeIndicator.tsx`）

```ts
type ChatMode = 'explore' | 'generating' | 'auditing' | 'adjusting';
```

**`deriveMode(profile, currentPlan, isAuditActive)` 决策树**：
```
isAuditActive → 'auditing' ✅
currentPlan → 'adjusting' 🔄
profile.province && profile.score → 'generating' 📊
其他 → 'explore' 🔍
```

**不变量**：
- ✅ 4 个模式 4 套配色（蓝/紫/橙/绿）
- ✅ 必须放在聊天区 header 左侧（`Sidebar` 之后），移动端可见
- ❌ **不允许合并为单一 status bar** —— 4 个模式对应 4 类 AI 行为，用户需要可观察的提示

### 1.5 信息收集进度条（来自 `components/shared/ProgressSteps.tsx`）

```ts
steps = [
  { key: 'province', label: '省份' },
  { key: 'score',    label: '分数' },
  { key: 'subjects', label: '选科' },
];
```

**触发条件**：`!hasCoreInfo && hasAnyInfo`（部分信息已收齐时显示，引导用户继续）。
**不变量**：
- ✅ 3 个圆点 + 连接线（`bg-green-500` / `bg-brand-500 ring-2 ring-brand-200` / `bg-gray-200`）
- ✅ 进度容器：`bg-white/90 border border-gray-100 rounded-full px-3 py-1.5 shadow-sm`
- ❌ **不允许换成 stepper 横向长条** —— 紧凑胶囊是关键

### 1.6 PlanCard 三 Tab（来自 `components/PlanCard.tsx`）

**结构**（**不可破坏**）：
1. Header：标题 `📊 你的志愿方案` + 用户画像摘要（省份·选科·分数·位次）
2. **TABS：冲刺/稳妥/保底**（mobile 用单字 `冲/稳/保`，desktop 用全名）
3. School List：每行展开概率条 + 风险徽章 + 预估分数
4. Footer：保存 / 导出 / 调整 三按钮

**不变量**：
- ✅ Tabs 用 `role="tablist" aria-label="志愿方案分类"`
- ✅ 当前 Tab 文字色 = TABS 配置色（`text-orange-600` / `text-blue-600` / `text-green-600`），下方有 0.5 高亮线
- ✅ 概率条 `role="progressbar" aria-valuenow aria-valuemin aria-valuemax aria-label="录取概率 X%"`
- ✅ 颜色映射：`p >= 80` 绿、`50 ≤ p < 80` 蓝、`30 ≤ p < 50` 黄、`p < 30` 橙
- ✅ 风险徽章三色：`低` 绿、`中` 黄、`高/较高` 红
- ❌ **不允许把"冲刺/稳妥/保底"合并为一个 list** —— 这是用户认知的核心分组
- ❌ **不允许去掉"调整"徽章动画**（`animate-pulse` 表示"已更新"）

### 1.7 移动端断点（来自 `app/page.tsx` + `Sidebar.tsx` + `MobileNav.tsx`）

| 视口 | 行为 |
|---|---|
| `< 1024px` | 显示 `MobileNav`（底部 3 Tab：对话/方案/记录），隐藏 `Sidebar`，Logo 移动端可见 |
| `>= 1024px` | 显示 `Sidebar`（280px 宽，左侧固定），隐藏 `MobileNav`，导航链接在 header |
| `>= 1024px` header | 右侧导航 `💬 咨询记录` `📋 我的方案` |
| `< 1024px` header | 右侧新建对话按钮 ✨ |

**不变量**：
- ✅ `Sidebar` 仅在 `lg:flex` 时渲染（不是 `hidden`，避免 SSR 闪烁）
- ✅ `MobileNav` 底部 padding 使用 `env(safe-area-inset-bottom, 0px)`（iPhone 安全区）
- ✅ `MobileNav` Tab 高度 ≥ 48px（min-h-[48px]）—— WCAG 2.5.5 触控目标

### 1.8 输入区交互（来自 `app/page.tsx:215-255`）

**不变量**：
- ✅ 文本域：自动撑高，最大 180px（`scrollHeight` 监听）
- ✅ Enter 发送 / Shift+Enter 换行
- ✅ 发送按钮：空内容时灰底禁用，有内容时蓝底阴影
- ✅ 附件按钮：折叠时灰、展开时蓝底高亮
- ✅ 底部小字 "AI辅助决策，请以官方信息为准" 仅桌面端可见（`hidden lg:block`）
- ❌ **不允许换成"按下回车不换行直接发送"** 的非 textarea 实现

### 1.9 快速提示（来自 `app/page.tsx:60-67`）

**三态动态推荐**：
- `hasCoreInfo`（省份+分数+选科都有）→ `['生成志愿方案', '审核我的方案', '调整方案（只看珠三角）', '了解人工智能工程师']`
- `hasAnyInfo`（部分有）→ `['我是广东省的', '物理类考生', '了解一下平行志愿', '审核我的方案']`
- `!hasAnyInfo`（全无）→ `['了解人工智能工程师', '平行志愿怎么录取', '广东省物理类考生', '审核我的方案']`

**不变量**：
- ✅ 水平滚动 `overflow-x-auto scrollbar-none`
- ✅ 胶囊样式 `bg-gray-50 border border-gray-200 rounded-full`
- ✅ 点击 → 写入 input 并 focus（不直接发送）

### 1.10 表单分步（来自 `components/FormCard.tsx`）

**3 步**：`basic` → `subjects` → `prefs`
**不变量**：
- ✅ 步骤按钮：当前 active 蓝底，未完成灰色禁用，已完成绿底可回退
- ✅ 不允许跳过未完成步骤（`goToStep` 守卫）
- ✅ 字段触摸后才显示验证（`touched` 状态）
- ✅ 顶部"更喜欢直接聊？也可以在对话框里说…"提示条
- ✅ 省份下拉：31 个省级行政单位（香港/澳门/台湾按国家级处理为缺省"广东"映射）
- ❌ **不允许改成单页长表单** —— 三步法是用户认知负荷的关键保护

### 1.11 上传条（来自 `components/UploadBar.tsx`）

**4 种模式**：
| 模式 | 接受类型 | 大小限制 | 颜色 |
|---|---|---|---|
| Excel | `.xlsx, .xls` | 5 MB | 绿 |
| 图片 | `image/*` | 10 MB | 紫 |
| PDF | `.pdf` | 10 MB | 橙 |
| 粘贴 | 无 | 无 | 蓝（切换为 textarea） |

**不变量**：
- ✅ 默认折叠，点击"展开 ▼"展开网格
- ✅ 粘贴模式：textarea + 取消按钮 + 提交按钮
- ✅ 文件大小超限：`alert` 弹出错误（**保留**，与现有 7-7-7 规则一致——不要换 toast）
- ❌ **不允许使用 modal**（用户已在聊天上下文，弹窗打断对话）

### 1.12 无障碍（必须保留）

| 项 | 实现 | 不可移除原因 |
|---|---|---|
| 全局焦点指示器 | `*:focus-visible` `outline: 2px solid var(--brand-500)` | 键盘导航唯一可见反馈 |
| 减少动画偏好 | `@media (prefers-reduced-motion: reduce)` 覆盖所有 `animation-duration` | 前庭功能障碍用户 |
| 移动端 Tab 高度 | `min-h-[48px]` | WCAG 2.5.5 触控目标 |
| 概率条 ARIA | `role="progressbar" aria-valuenow` | 屏幕阅读器可读 |
| 风险徽章 ARIA | `role="alert"` | 风险即时播报 |
| Tabs ARIA | `role="tablist" / "tab" aria-selected` | 屏幕阅读器路由 |

---

## 2. 现状盘点

### 2.1 文件清单（`前端原型代码/src/`）

```
src/                                  4114 行（已扫读）
├── app/                              8 页面
│   ├── layout.tsx                    33   RootLayout + theme init
│   ├── page.tsx                      270  聊天对话
│   ├── globals.css                   90   全局基础样式
│   ├── assessment/page.tsx           350  Holland RIAS 测试
│   ├── consultations/page.tsx        253  咨询记录
│   ├── plans/page.tsx                308  我的方案
│   ├── plans/[id]/page.tsx           167  方案详情
│   ├── plans/compare/page.tsx        154  方案对比
│   └── about/page.tsx                232  关于/帮助
├── components/                       7 组件
│   ├── FormCard.tsx                  374  分步表单
│   ├── AuditReportCard.tsx           159  审核报告卡
│   ├── PlanCard.tsx                  192  方案卡
│   ├── ChatMessage.tsx               93   消息路由
│   ├── UploadBar.tsx                 141  上传条
│   ├── CareerCard.tsx                70   职业卡
│   ├── FileUploadPrompt.tsx          36   上传提示
│   ├── navigation/                   3
│   │   ├── Sidebar.tsx               115
│   │   ├── MobileNav.tsx             75
│   │   └── ModeIndicator.tsx         74  + deriveMode
│   └── shared/                       3
│       ├── ThemeToggle.tsx           50
│       ├── SafeMarkdown.tsx          103
│       └── ProgressSteps.tsx         89
├── lib/                              8 hooks + 1 utility
│   ├── theme.ts                      68
│   ├── useChat.ts                    543  编排 6 个子 hook
│   ├── useConsultation.ts            167
│   ├── useMessages.ts                88
│   ├── usePlan.ts                    89
│   ├── useProfile.ts                 87
│   ├── useAudit.ts                   ?
│   └── useSimulation.ts              43
└── styles/
    └── design-system.css             247  设计系统 token
```

### 2.2 强项（不可破坏）

1. **完整 design system**（247 行 CSS 变量 + Tailwind 4 @theme 映射）
2. **三态主题**（`initThemeScript` 同步注入 + `data-theme` 属性 + `prefers-color-scheme` 兜底）
3. **消息路由模式**（`ChatMessage` 按 `message.type` 派发，避免单组件膨胀）
4. **XSS 防护**（`SafeMarkdown` + `rehype-sanitize`，`dangerouslySetInnerHTML` 仅 1 处受控字符串）
5. **WCAG 起步**（`focus-visible` + `prefers-reduced-motion` + ARIA roles）
6. **`tsconfig.strict`** + `moduleResolution: "bundler"` + `@/*` 路径别名
7. **桌面/移动 双视图**（`Sidebar` + `MobileNav` + header 响应式导航）

### 2.3 弱项（必须修复）

| 弱项 | 影响 | 严重度 |
|---|---|---|
| **零测试覆盖** | 重构无安全网 | **P0** |
| **零后端对接**（`grep fetch/axios` 0 命中） | 迁到生产后所有 hook 要重写 | **P0** |
| **localStorage 存敏感信息**（`useConsultation` / `plans/page.tsx`） | 跨设备不同步 / 用户清除数据丢失 | **P1** |
| **组件库不完整**（无 Button / Input / Dialog / Toast） | 重复实现、风格漂移 | **P1** |
| **mock 数据硬编码**（`useChat.ts:42-90` 广东省 620 物理类） | 无法演示其他场景 | **P2** |
| **无 i18n 框架**（文案硬编码中文） | 海外/多语种扩展困难 | **P2** |
| **无 Zustand / Jotai**（8 hook 还撑得住，20+ 时混乱） | 状态管理可维护性 | **P2** |
| **无 CI**（`typecheck / lint / build` 失败无门禁） | 协作摩擦 | **P0** |

---

## 3. 目标架构

### 3.1 Monorepo 结构

```
gaokao-volunteer-system/
├── apps/
│   ├── admin/                       # FastAPI 后端（不变）
│   └── web/                         # Next.js 前端（收编自 前端原型代码/）
├── packages/
│   ├── ui/                          # 设计系统 + 组件库
│   │   ├── tokens/                  # design-system.css + theme.ts
│   │   ├── components/              # Button/Input/Card/Dialog/Toast/...
│   │   ├── navigation/              # Sidebar/MobileNav/ModeIndicator
│   │   ├── chat/                    # ChatMessage/PlanCard/CareerCard/...
│   │   └── forms/                   # FormCard
│   ├── api-client/                  # OpenAPI 生成的 TS 客户端
│   │   ├── src/
│   │   ├── openapi.json             # 来自 FastAPI /openapi.json
│   │   └── codegen.config.ts
│   ├── hooks/                       # 跨页业务 hook（useChat/useProfile/usePlan/...）
│   ├── store/                       # Zustand stores（theme/ui/compare）
│   ├── i18n/                        # next-intl 配置 + 词条
│   ├── test-utils/                  # Vitest 配置 + RTL 包装 + MSW handlers
│   └── tsconfig/                    # 共享 tsconfig.base.json
├── turbo.json
├── pnpm-workspace.yaml
└── package.json
```

**关键决策**：
- ✅ 收编 `前端原型代码/` 为 `apps/web/`（删 `前端原型代码/` 目录）
- ✅ design-system.css 提到 `packages/ui/tokens/`，被 `apps/web` + 未来 `apps/admin-panel` 共享
- ✅ 业务 hook（useChat 编排的 6 个子 hook）放进 `packages/hooks/`
- ❌ **不**用 nx/lerna —— Turborepo 任务编排已够用

### 3.2 数据流（真实后端对接后）

```
┌──────────────┐  fetch  ┌──────────────────┐  TanStack  ┌────────────┐
│  React 组件  │ ──────→ │  packages/api-   │  Query     │ FastAPI    │
│  (apps/web)  │ ←────── │  client (类型化)  │ ←────────→ │ (admin/)   │
└──────────────┘  缓存   └──────────────────┘  mutation   └────────────┘
       │                                                       │
       │ localStorage                                          │
       ▼ (offline cache only)                                  ▼
┌──────────────┐                                       ┌────────────┐
│  Zustand UI  │                                       │  SQLite /  │
│  Store       │                                       │  Postgres  │
└──────────────┘                                       └────────────┘
```

**关键原则**：
- 服务端数据**单一真相源** = FastAPI DB
- localStorage 仅作"乐观更新回滚"和"离线浏览缓存"
- Zustand 只承担"跨页 UI 状态"（主题 / 侧边栏折叠 / 方案对比选择）
- TanStack Query 管理"服务端状态的客户端缓存"

### 3.3 路由对照表（前端原型 vs 后端现状）

| 前端原型路由 | 对应后端 | 优先级 |
|---|---|---|
| `/`（对话） | **新增** `POST /api/chat/send` `GET /api/chat/history` | **P0**（首屏） |
| `/assessment`（Holland 测试） | **新增** `POST /api/assessment` | P2 |
| `/consultations` | **新增** `GET /api/consultations` | P1 |
| `/plans` | **新增** `GET /api/plans` | P1 |
| `/plans/[id]` | **新增** `GET /api/plans/{id}` | P1 |
| `/plans/compare` | 客户端计算（不调后端） | P1 |
| `/about` | 静态文案 | P2 |
| **（后端已有）`/pricing`** | `GET /api/public/services` | P1 |
| **（后端已有）`/checkout/{v}`** | `POST /api/public/orders` `POST /api/public/payments/*` | P1 |
| **（后端已有）`/portal/{token}/info`** | `POST /portal/{token}/info` | P1 |
| **（后端已有）`/portal/{token}/status`** | `GET /portal/{token}/status` | P1 |
| **（后端已有）`/portal/{token}/report`** | `GET /portal/{token}/report` | P1 |

**说明**：后端已有但前端原型没有的页面（portal 流程），**不**在第一阶段收编——属于商业化产品，不属于"AI 志愿助手"主轴。

---

## 4. 5 阶段实施路径（与 V2 报告衔接）

> 本节是对 `REVIEW_REPORT_2026-07-02_SENIOR_DEVELOPER.md` §9 5 阶段方案的前端**细化版**。所有"页面/组件/hook"粒度任务都已落到本方案。

### 4.1 阶段 A — 基础设施（10-12 人天）

#### A.1 Monorepo 收编（1 人天）
- 创建 `apps/web/` 目录，把 `前端原型代码/src/` 整目录移入
- 根目录加 `pnpm-workspace.yaml` + `turbo.json`
- 加根 `package.json`（devDependencies: turbo, prettier, eslint-config-prettier）
- 验证：`pnpm --filter web dev` 启动原 dev server 无错

#### A.2 共享 tsconfig（0.5 人天）
- 创建 `packages/tsconfig/base.json`（strict + bundler resolution + paths）
- `apps/web/tsconfig.json` extends base
- `packages/ui/tsconfig.json` extends base（再加 `composite: true`）
- 加 `tsc --noEmit` 到 web 的 lint 脚本

#### A.3 设计系统提取（2 人天）
- 把 `src/styles/design-system.css` 移到 `packages/ui/tokens/design-system.css`
- 把 `src/lib/theme.ts` 移到 `packages/ui/tokens/theme.ts`
- 在 `packages/ui/package.json` 暴露 `tokens.css` + `theme.ts`
- 在 `apps/web/app/globals.css` `@import "@gaokao/ui/tokens.css"`
- 在 `apps/web/app/layout.tsx` 调用 `import { initThemeScript } from "@gaokao/ui/tokens/theme"`

#### A.4 UI 组件库起步（2.5 人天）
新增 5 个基础组件（**不**改外观，仅抽公共样式）：

| 组件 | 来源 | 说明 |
|---|---|---|
| `Button` | 原型分散在多处 | primary/secondary/ghost/danger 四种 variant |
| `Input` | FormCard 文本框 | 含 error/helpText 状态 |
| `Select` | FormCard 下拉 | 同上 |
| `Card` | PlanCard/AuditReportCard/CareerCard 共享 | 圆角 2xl + 阴影 sm + border |
| `Badge` | 风险徽章 | 三色 + 三等级 |
| `Tabs` | PlanCard Tab | 复用 role="tablist" |

每个组件必须配套：① Vitest 单测；② Storybook story（CSF 3.0）；③ tsdoc 注释。

#### A.5 测试基础设施（2 人天）
- `pnpm add -D vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom jsdom`
- 创建 `packages/test-utils/`：
  - `vitest.config.ts`（jsdom + globals + setup）
  - `setup.ts`（jest-dom matchers + MSW server）
  - `renderWithProviders.tsx`（QueryClient + Theme + Router 包装）
- 加 3 个示范单测：
  - `ModeIndicator.test.tsx`（4 模式渲染）
  - `deriveMode.test.ts`（决策树全覆盖）
  - `SafeMarkdown.test.tsx`（XSS 注入：`<script>alert(1)</script>` 不执行）

#### A.6 Playwright e2e 骨架（1.5 人天）
- `pnpm add -D @playwright/test`
- 创建 `apps/web/e2e/`：
  - `playwright.config.ts`（chromium + webkit + 移动 viewport）
  - `chat.spec.ts`（**示范用例**：发送消息 → 收到 AI 回复 → 切换主题）
  - `theme.spec.ts`（验证三种模式切换无闪白）
  - `navigation.spec.ts`（桌面 Sidebar / 移动 MobileNav 切换）

#### A.7 OpenAPI 类型化（1.5 人天）
- `pnpm add -D openapi-typescript-codegen`
- 创建 `packages/api-client/codegen.config.ts`
- 流程：FastAPI 启动 → `GET /openapi.json` → 写入 `packages/api-client/openapi.json` → codegen
- `turbo.json` 加 `generate-api-client` 任务，依赖 `^build-admin`
- 加 1 个示范调用：`apps/web/lib/api/chat.ts` 用生成的 client 调 `POST /api/chat/send`（**先用 mock server，阶段 B 切真实**）

#### A.8 CI 工作流（1 人天）
- `.github/workflows/web-ci.yml`：
  - pnpm install
  - turbo run lint typecheck test
  - turbo run e2e（Playwright）
  - turbo run build（Next.js）
- 加 Codecov 前端 target
- 加 bundle size 预算（`@next/bundle-analyzer`，> 200KB warn）

**A 阶段交付物**：
- ✅ monorepo 可 `pnpm install && pnpm dev` 一键启动
- ✅ 设计系统 + 5 个基础组件 + 8 hooks + 8 页面 + 247 行 CSS 全部就位
- ✅ 测试覆盖率：原型组件 ≥ 60% line coverage
- ✅ CI 红绿信号在 PR 上可见

### 4.2 阶段 B — 真实后端对接（25-35 人天）

> **核心目标**：把 prototype 的 8 个 mock hook 全部替换为真实 API 调用，UI/UX **零变化**。

#### B.1 后端 API 补全（5 人天，先于 B.2）
后端需要新增以下端点（**FastAPI 后端**任务，前端不实现）：

| 端点 | 方法 | 入参 | 出参 |
|---|---|---|---|
| `/api/chat/send` | POST | `{message, consultation_id?}` | `{user_message, assistant_message, consultation_id}` |
| `/api/chat/history` | GET | `?consultation_id=...` | `{messages: [...]}` |
| `/api/consultations` | GET | - | `{consultations: [{id, title, updated_at, profile}]}` |
| `/api/consultations/{id}` | GET | - | `{id, messages, profile, plan, audit}` |
| `/api/consultations/{id}` | DELETE | - | `{ok: true}` |
| `/api/plans` | GET | - | `{plans: [{id, name, created_at, rush_count, ...}]}` |
| `/api/plans/{id}` | GET | - | `{id, name, plan, profile, created_at}` |
| `/api/plans/{id}` | PATCH | `{name}` | `{ok: true}` |
| `/api/plans/{id}` | DELETE | - | `{ok: true}` |
| `/api/assessment` | POST | `{answers: [...]}` | `{riasec: {R, I, A, S, E, C}, recommendations: [...]}` |
| `/api/audit/upload` | POST | `multipart/form-data` | `{report_id, overall_score, risk_items}` |

**注意**：所有端点**必须**走 OpenAPI 文档 + 类型化错误响应（沿用 `admin/errors/registry.py`）。

#### B.2 useChat 真实化（4 人天）
把 `useChat.ts`（543 行）的 mock 拆解为：

```ts
// packages/hooks/useChat.ts
export function useChat(consultationId?: string) {
  const queryClient = useQueryClient();

  // 1. 历史查询
  const { data: messages = [], isLoading } = useQuery({
    queryKey: ['chat', consultationId],
    queryFn: () => apiClient.chat.getHistory(consultationId),
    staleTime: 30_000,
  });

  // 2. 发送 mutation
  const sendMutation = useMutation({
    mutationFn: (text: string) => apiClient.chat.send(consultationId, { message: text }),
    onMutate: async (text) => {
      // 乐观更新
      await queryClient.cancelQueries({ queryKey: ['chat', consultationId] });
      const previous = queryClient.getQueryData<Message[]>(['chat', consultationId]);
      queryClient.setQueryData<Message[]>(['chat', consultationId], (old) => [
        ...(old ?? []),
        { role: 'user', type: 'text', content: text, timestamp: new Date() },
      ]);
      return { previous };
    },
    onError: (err, text, context) => {
      // 回滚
      if (context?.previous) {
        queryClient.setQueryData(['chat', consultationId], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', consultationId] });
    },
  });

  // 3. 文件上传
  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.audit.upload(file),
    onSuccess: (report) => {
      queryClient.setQueryData<Message[]>(['chat', consultationId], (old) => [
        ...(old ?? []),
        { role: 'assistant', type: 'audit_report', data: report, timestamp: new Date() },
      ]);
    },
  });

  return { messages, isLoading, send: sendMutation.mutate, upload: uploadMutation.mutate };
}
```

**UI 端**：`app/page.tsx` 调 `const { messages, send, isLoading } = useChat(activeRecordId)`，其余代码不动。

#### B.3 useProfile 真实化（1.5 人天）
profile 信息从后端 `user.id` 关联的 `user_profile` 表读取，新增 `/api/profile` 端点。

#### B.4 usePlan / useConsultation 真实化（4 人天）
- 删 localStorage 写入路径
- 改用 TanStack Query 读 `/api/plans` `/api/consultations`
- PATCH（重命名）走 mutation
- DELETE 走 mutation + invalidate

#### B.5 离线缓存策略（2 人天）
保留 localStorage **仅**作"乐观更新回滚"和"网络断线时的最后消息缓存"：
- TanStack Query `persistQueryClient` 把 query cache 落盘
- 网络恢复时自动 refetch
- 失败时 fallback 到 last-known state

#### B.6 表单提交真实化（1.5 人天）
`FormCard` `onSubmit` → `apiClient.profile.update(...)` → invalidate `['profile']`。

#### B.7 错误处理（1.5 人天）
- 用 `admin/errors/registry.py` 的 5 字段结构在 `apiClient` 包装错误
- 错误码 → 用户文案映射（`packages/i18n/zh-CN/errors.json`）
- 5xx 走 `ErrorBoundary` → 兜底页
- 429 / 网络错 → 顶部 Toast 提示（**新增** Toast 组件，**不**改 FormCard）

#### B.8 e2e 真实化（2 人天）
- 替换 Playwright `chat.spec.ts` 的 mock service worker 为真实 FastAPI
- 加 5 个关键路径 e2e：
  - 用户注册 → 咨询 → 收到 AI 回复
  - 上传方案 → 收到审核报告
  - 切换方案 Tab
  - 调整主题（含 system 模式）
  - 重启浏览器后历史恢复

#### B.9 性能预算验证（1.5 人天）
- 装 `@next/bundle-analyzer`
- 跑 Lighthouse CI 5 次取 P75
- LCP < 2.5s / INP < 200ms / CLS < 0.1
- Bundle size：first load JS < 200KB

**B 阶段交付物**：
- ✅ 11 个端点全部对接（前端 8 页 + 后端 3 页新端点）
- ✅ 8 个 hook 全部真实化，零 mock 数据
- ✅ e2e 5 路径全绿
- ✅ Lighthouse P75 ≥ 90

### 4.3 阶段 C — 架构整合（8-10 人天）

#### C.1 部署架构（3 人天）
- 选其一：
  - **方案 1（推荐）**：CloudStudio 静态部署 + 反代 `/api/*` 到 FastAPI
  - **方案 2**：Vercel 部署 + Vercel Function 反代
  - **方案 3**：自托管（PM2 / systemd）
- CORS 配置：`allow_origins=["https://web.gaokao.example.com"]`
- CSP 头：基于 `secure_headers`（`script-src 'self'`，`style-src 'self' 'unsafe-inline'` 允许 Tailwind）

#### C.2 监控（2 人天）
- 前端 Sentry（`@sentry/nextjs`）
- Web Vitals 上报到 Vercel Analytics / 自托管 Prometheus
- 后端 Sentry + OpenTelemetry trace
- 前端 trace 透传到后端（`x-trace-id` header）

#### C.3 安全响应头（1.5 人天）
- FastAPI 加 `secure_headers` 中间件：
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Content-Security-Policy: default-src 'self'; img-src 'self' data:; ...`
  - `Referrer-Policy: strict-origin-when-cross-origin`

#### C.4 反代 / 域名（1.5 人天）
- 前端：`https://web.gaokao.example.com`
- 后端 API：`https://api.gaokao.example.com`
- 短链接：`https://s.gaokao.example.com`（已有 `/s/{code}` 路由）
- 反代：nginx / caddy 统一收敛

**C 阶段交付物**：
- ✅ 前端可独立部署
- ✅ CSP / HSTS / X-Frame-Options 全套就位
- ✅ Sentry 前后端 trace 打通

### 4.4 阶段 D — 设计 / a11y 加固（8-12 人天）

#### D.1 基础组件补齐（4 人天）
新增 10 个组件（每个含 Vitest + Storybook）：

| 组件 | 用途 | 来源 |
|---|---|---|
| `Dialog` | 模态对话框 | 上传确认 / 删除确认 |
| `Toast` | 顶部提示 | 错误反馈 / 保存成功 |
| `Tooltip` | 悬浮提示 | Tab 角标含义 |
| `Dropdown` | 下拉菜单 | Sidebar 头像菜单 |
| `Avatar` | 用户头像 | ChatMessage AI / User |
| `Skeleton` | 骨架屏 | 加载占位 |
| `ProgressBar` | 进度条 | 通用（已存在 ProgressSteps，独立） |
| `Switch` | 开关 | 偏好设置 |
| `Checkbox` | 复选框 | FormCard 选科 |
| `Radio` | 单选 | ThemeToggle 已用 radiogroup，独立抽 |

#### D.2 a11y 全量审计（2 人天）
- 跑 `axe-core` 自动扫描：目标 0 critical / 0 serious
- 手动测试：屏幕阅读器（NVDA / VoiceOver）+ 键盘 Tab 导航
- 色彩对比度：所有文本 ≥ 4.5:1（WCAG 2.1 AA）
- Skip link：所有页面顶部 "跳到主内容"
- Landmark roles：`<header> <nav> <main> <aside> <footer>` 完整

#### D.3 暗色主题全覆盖（1.5 人天）
- 验证每个组件的暗色变体
- 加 `dark:` 前缀到必要 Tailwind 类
- 图表（如未来引入 echarts）用 `prefers-color-scheme` 切换主题

#### D.4 国际化基础（2 人天）
- `pnpm add next-intl`
- 抽所有中文文案到 `packages/i18n/zh-CN/`
- 占位 `packages/i18n/en-US/`（暂留空字典，未来填充）
- 路由级 locale 切换

#### D.5 Storybook + Chromatic（1.5 人天）
- 30+ 组件 stories
- Chromatic 视觉回归（每组件 3 个状态：light / dark / 移动）

#### D.6 性能深度优化（1 人天）
- 图片：自动转 WebP / AVIF（`next/image`）
- 字体：`next/font` + `display: swap`
- 代码分割：`React.lazy` 路由级 + 组件级（PlanCard、AuditReportCard 异步加载）
- prefetch：`<Link prefetch>` 关键路径

**D 阶段交付物**：
- ✅ 组件库 15+ 组件，每个有 test + story
- ✅ axe-core 0 critical
- ✅ Lighthouse P75 ≥ 95
- ✅ zh-CN / en-US 字典就位

### 4.5 阶段 E — 内部页面 React 化（15-20 人天，可选）

把 `admin/static/dashboard.html` + `admin/routes/web_public.py` 的"运营管理"内部页 React 化：

| 页面 | 来源 | 复杂度 |
|---|---|---|
| 登录页 | `admin/routes/auth.py` | 低 |
| Dashboard | `admin/static/dashboard.html` | 中（echarts 集成） |
| 订单列表 | `admin/routes/orders.py` | 中 |
| 订单详情 | 同上 | 中 |
| 案例列表 | `admin/routes/cases.py` | 中 |
| 分享页 editor | `data/share/permission.py` | 高（权限矩阵） |
| 短链接管理 | `data/share/short_link.py` | 低 |

**复用**：所有页面用 `packages/ui/` 组件 + `packages/api-client/` 类型化调用 + `packages/hooks/` 业务 hook。

**E 阶段交付物**：
- ✅ 运营后台从静态 HTML / Python f-string 全部迁移到 React
- ✅ 与前端原型共享设计系统

---

## 5. 关键决策点（必须由 PM / Lead 拍板）

| # | 决策点 | 推荐 | 备选 |
|---|---|---|---|
| 1 | Monorepo 工具 | **Turborepo + pnpm** | Nx + pnpm |
| 2 | 客户端状态 | **Zustand 4.x** | Jotai / Redux Toolkit |
| 3 | 服务端状态 | **TanStack Query 5.x** | SWR |
| 4 | 表单库 | **React Hook Form + Zod** | Formik + Yup |
| 5 | 视觉回归 | **Chromatic** | Loki / Percy |
| 6 | 部署平台 | **CloudStudio** | Vercel / 自托管 |
| 7 | i18n 框架 | **next-intl 3.x** | react-i18next |
| 8 | 监控 | **Sentry** | 自托管 GlitchTip |
| 9 | 路由是否改 RSC | **保持客户端**（useChat 状态复杂） | 局部 RSC（layout） |
| 10 | 公开门户是否纳入 | **否**（商业化产品，单独预算） | 合并做 |

---

## 6. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 真实 API 与 mock 数据结构不一致 | 高 | 中 | OpenAPI Codegen 第一天就跑通，**强制类型对齐** |
| Next.js 16 + React 19 与 TanStack Query 兼容性 | 中 | 中 | 提前 1 天 spike，备选 SWR |
| 移动端断点（768 / 1024）与原型不一致 | 低 | 高 | Playwright 移动 viewport 强制 e2e 覆盖 |
| Bundle size 爆炸（react-markdown 很大） | 中 | 中 | `next/dynamic` 异步 + markdown 拆 chunk |
| localStorage 缓存策略导致数据冲突 | 中 | 中 | TanStack Query `persistQueryClient` + 时间戳同步 |
| 老用户浏览器数据迁移 | 高 | 低 | `version` 字段 + 一次性迁移逻辑 |
| ChatMessage 路由扩展性 | 中 | 中 | 加 `MessageRenderer` 抽象层，预留自定义 type |

---

## 7. 立即可执行（5 条，本周启动）

1. **创建 monorepo 骨架**（1 人天）
   - `pnpm-workspace.yaml` + `turbo.json` + 根 `package.json`
   - `apps/web/` 收编 `前端原型代码/src/`
   - 验证 `pnpm dev` 可启动

2. **抽 design-system.css 到 `packages/ui/tokens/`**（0.5 人天）
   - 同步 `lib/theme.ts`
   - `apps/web/app/globals.css` 改 `@import "@gaokao/ui/tokens.css"`
   - 跑 `pnpm dev` 视觉 0 回归

3. **搭测试基础设施**（1.5 人天）
   - Vitest + RTL + MSW
   - 3 个示范单测（ModeIndicator / deriveMode / SafeMarkdown）
   - 1 个示范 Playwright e2e

4. **OpenAPI Codegen 试跑**（1 人天）
   - 起 FastAPI → 拉 `/openapi.json` → codegen
   - 加 1 个示范调用（不切真实，仅验证类型）

5. **CI 工作流起步**（0.5 人天）
   - `.github/workflows/web-ci.yml`
   - `pnpm install + turbo run lint typecheck test build`
   - PR 上跑通

---

## 8. 工期与里程碑

| 阶段 | 人天 | 累计 | 里程碑 |
|---|---|---|---|
| A. 基础设施 | 10-12 | 10-12 | monorepo 跑通 + 5 组件 + e2e 骨架 + CI |
| B. 真实后端对接 | 25-35 | 35-47 | 11 端点对接 + Lighthouse ≥ 90 |
| C. 架构整合 | 8-10 | 43-57 | 独立部署 + Sentry + CSP |
| D. 设计/a11y 加固 | 8-12 | 51-69 | 15 组件 + axe 0 critical + i18n |
| E. 内部页面 React 化 | 15-20 | 66-89 | 运营后台全 React 化 |
| **总计** | **66-89** | - | **与 V2 报告一致** |

---

## 9. 不要做的事（避坑清单）

| ❌ 禁 | 理由 |
|---|---|
| 把 `前端原型代码/` 直接复制到 `apps/web/` 后**改任何样式 / 交互** | 违反用户"严格采用"约束 |
| 把 Tailwind 4 降到 3 找"稳定" | 团队已用 4 个月，无回退必要 |
| 改 `design-system.css` 的 token 名 | 全站 200+ 引用，破坏所有组件 |
| 去掉 `initThemeScript` 改用 `next-themes` | 闪白防护是硬需求，next-themes 有 hydration 延迟 |
| 拆 `PlanCard` 三 Tab 为单一 list | 用户认知核心 |
| 删 `*：focus-visible` | a11y 唯一键盘反馈 |
| 用 `dangerouslySetInnerHTML` 渲染 AI 消息 | 已有 `SafeMarkdown` 防护，绕过去 = XSS |
| 把 `useChat` 拆为多个 useState | 已 543 行，复杂状态机必须留 hook |
| 把 `'use client'` 提到 layout | 主题 init 必须在 server，避免 hydration race |
| 用 emoji 替换 SVG 图标（除特定位置） | prototype 已经是混合，沿用 |

---

## 10. 验收标准（Definition of Done）

每个阶段结束必须满足：

- [ ] 所有原 prototype 页面**像素级无回归**（Chromatic diff < 0.1%）
- [ ] 三态主题切换无闪白（Playwright `theme.spec.ts` 全绿）
- [ ] 移动端 768 / 1024 断点行为与原型一致
- [ ] `pnpm lint typecheck test build e2e` 全绿
- [ ] Lighthouse P75 ≥ 90（性能 / 可访问性 / 最佳实践 / SEO）
- [ ] axe-core 扫描 0 critical / 0 serious
- [ ] 新增依赖经过 Lead 评审（禁止无意识添加）
- [ ] OpenAPI 契约变更同步更新 `packages/api-client/`
- [ ] PR 包含截图 / 录屏（如有 UI 改动）

---

## 附录 A：原型文件保留清单

迁移后**必须 1:1 保留**的文件：

```
[核心组件 - 不允许改 UI/交互]
apps/web/src/components/PlanCard.tsx                    # 192 行
apps/web/src/components/AuditReportCard.tsx             # 159 行
apps/web/src/components/CareerCard.tsx                  # 70 行
apps/web/src/components/ChatMessage.tsx                 # 93 行
apps/web/src/components/UploadBar.tsx                   # 141 行
apps/web/src/components/FormCard.tsx                    # 374 行
apps/web/src/components/FileUploadPrompt.tsx            # 36 行
apps/web/src/components/navigation/Sidebar.tsx          # 115 行
apps/web/src/components/navigation/MobileNav.tsx        # 75 行
apps/web/src/components/navigation/ModeIndicator.tsx    # 74 行
apps/web/src/components/shared/ThemeToggle.tsx          # 50 行
apps/web/src/components/shared/SafeMarkdown.tsx         # 103 行
apps/web/src/components/shared/ProgressSteps.tsx        # 89 行

[设计系统 - 不允许改 token 值]
apps/web/src/styles/design-system.css                   # 247 行
apps/web/src/lib/theme.ts                               # 68 行

[页面布局 - 不允许改容器结构]
apps/web/src/app/layout.tsx                             # 33 行
apps/web/src/app/globals.css                            # 90 行

[业务逻辑 - 允许重构内部实现，对外接口保持稳定]
apps/web/src/lib/useChat.ts                             # 543 行
apps/web/src/lib/useConsultation.ts                     # 167 行
apps/web/src/lib/useMessages.ts                         # 88 行
apps/web/src/lib/usePlan.ts                             # 89 行
apps/web/src/lib/useProfile.ts                          # 87 行
apps/web/src/lib/useAudit.ts
apps/web/src/lib/useSimulation.ts                       # 43 行
```

**外部接口稳定**的意思是：`useChat` 返回的 `{ messages, isTyping, sendMessage, submitForm, handleFileUpload, savePlan, ... }` 字段名和类型不能变。否则 `app/page.tsx` 全部重写。

---

## 附录 B：OpenAPI Codegen 工作流

```
┌──────────────────┐
│ admin/app.py     │
│ (FastAPI)        │
└────────┬─────────┘
         │ uvicorn admin.app:app
         ▼
┌──────────────────┐
│ /openapi.json    │  ← 自动生成
└────────┬─────────┘
         │ curl > packages/api-client/openapi.json
         ▼
┌──────────────────┐
│ openapi-typescript│  ← 每日 CI 跑
│ -codegen         │
└────────┬─────────┘
         │ 生成 TS 客户端
         ▼
┌──────────────────┐
│ packages/api-    │
│ client/src/      │  ← 类型安全
└────────┬─────────┘
         │ import { apiClient } from '@gaokao/api-client'
         ▼
┌──────────────────┐
│ apps/web 代码    │
└──────────────────┘
```

**关键约束**：
- FastAPI 后端**不允许**在 `api_client/` 目录手写类型（避免漂移）
- 每次 FastAPI 改 Pydantic schema 后必须重跑 codegen
- CI 加 `api-client-types-check`：生成的类型 vs 实际代码使用 → 不一致则失败

---

## 附录 C：与 V2 Senior Developer 报告的衔接

| V2 报告条目 | 本方案对应 |
|---|---|
| §8.3.1 零测试覆盖 | §4.1 A.5 + A.6 + B.8 |
| §8.3.2 后端 API 未对接 | §4.2 B.2-B.9 |
| §8.3.3 localStorage 存敏感信息 | §4.2 B.4 + B.5 |
| §8.3.4 Mock 数据真实性 | §4.2 B.2（替换为真实数据） |
| §8.3.5 国际化 | §4.4 D.4 |
| §8.3.6 状态管理 | §3.1 引入 Zustand |
| §8.3.7 构建与 CI | §4.1 A.8 |
| §8.3.8 可访问性深度 | §4.4 D.2 |
| §8.3.9 性能预算 | §4.2 B.9 + §4.4 D.6 |
| §8.3.10 与后端类型契约 | §4.1 A.7 + 附录 B |
| §9.2 5 阶段方案 | §4 本方案 5 阶段（细化版） |
| §9.3 工期估算 66-89 人天 | §8 一致 |

---

**评审完成。技术栈决策附在 §0，UI/交互不变量在 §1，5 阶段实施路径在 §4，立即可执行在 §7。**

**Frontend Developer 建议**：
- 严格遵循 §1 不变量（这是用户的硬约束）
- §0 选型在 7 天内 spike 验证（特别是 TanStack Query + Zustand 与 Next 16 协同）
- §7 5 件事本周启动，1 周后决定是否进入 §4.1 完整 A 阶段
