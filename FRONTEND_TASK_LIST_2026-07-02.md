# 前端重构 · 任务清单（可验收粒度 + Self-Review 通过证明）

> 评审者：**Frontend Developer (资深前端开发工程师)**
> 日期：2026-07-02 22:30
> 输入：上轮 `FRONTEND_REFACTOR_PLAN_2026-07-02.md`（5 阶段方案）
> 本轮目标：把方案拆成 **可被 CI / 人工 1:1 验收** 的任务，**自检** UI/交互完全遵循新设计 + 功能完整 + 后端集成正常

---

## 0. 本轮自检总结（前置）

> 本节是 self-review 的"诚实账"——本轮**额外发现的 5 个新风险** 和 **8 个被验证的硬约束**。

### 0.1 新发现的 5 个风险（方案中未提及，必须补）

| # | 风险 | 触发点 | 应对任务 |
|---|---|---|---|
| **R-NEW-1** | `useChat.ts:543` 是 7 个子 hook 的**编排层**，且 mock 数据直接耦合在文件内 | 真实化时不能直接 `replaceAll`，需要**先解耦**再替换 | T-B-12 加显式子任务 |
| **R-NEW-2** | `consultations/page.tsx:8-9` 用了 `localStorage.consultationRecords` + `activeConsultationId` 两 key；plans 同理 | 真实化时需要**保留 key 名作为兼容层**，老用户不丢数据 | T-B-16 + T-D-04 |
| **R-NEW-3** | `CareerCard.tsx:22` `stars(n) = '⭐'.repeat(n)` — match 是 1-5 整数 | API 校验需加 Zod 约束，否则非法值前端会爆 | T-A-22 |
| **R-NEW-4** | `plans/[id]/page.tsx:165` 用 `alert()` 弹导出（图片/PDF） | 真实环境 alert 是阻塞的；需替换为 Toast + 异步下载 | T-D-12 |
| **R-NEW-5** | `page.tsx:192` `quickPrompts` 三态文案在 `app/page.tsx` 内**硬编码** | i18n 阶段需要把数组抽到 `packages/i18n/zh-CN/chat.json` | T-D-08 |

### 0.2 已验证的 8 个硬约束（方案正确）

| 约束 | 验证证据 | 任务化位置 |
|---|---|---|
| ✅ PlanCard 概率条颜色映射 4 档（80/50/30） | `PlanCard.tsx:34-39` | T-A-14 单测 |
| ✅ Tabs 移动端单字 / 桌面端全名 | `PlanCard.tsx:84-85` | T-A-14 视觉回归 |
| ✅ ModeIndicator 4 模式决策树顺序 | `ModeIndicator.tsx:67-74`（audit > plan > profile > explore） | T-A-15 单测 |
| ✅ FormCard 不允许跳步 | `FormCard.tsx:74-79` | T-A-17 单测 |
| ✅ 移动端 Tab min-h-[48px] | `MobileNav.tsx:60` | T-A-16 axe |
| ✅ 主题 init 防闪白 | `lib/theme.ts:19-32` + `layout.tsx` | T-A-18 单测 |
| ✅ SafeMarkdown XSS 防护 | `SafeMarkdown.tsx:97` rehype-sanitize | T-A-19 注入测试 |
| ✅ useChat typing 动画 | `page.tsx:173-186` | T-B-13 e2e |

---

## 1. 任务总览（5 阶段，91 个任务，66-89 人天）

| 阶段 | 任务数 | 人天 | 关键里程碑 |
|---|---|---|---|
| A. 基础设施 | 23 | 11 | monorepo + 5 组件 + e2e 骨架 + CI |
| B. 真实后端对接 | 21 | 30 | 11 端点对接 + 8 hook 真实化 + Lighthouse ≥ 90 |
| C. 架构整合 | 13 | 9 | 独立部署 + Sentry + CSP |
| D. 设计 / a11y 加固 | 18 | 11 | 15 组件 + axe 0 critical + i18n |
| E. 内部页面 React 化 | 16 | 17 | 运营后台全 React 化 |
| **总计** | **91** | **78** | **（已与 V2 报告对齐 66-89 中位）** |

每个任务含 **ID / 标题 / 验收标准 / 估时 / 依赖 / 关联约束** 六字段。

---

## 阶段 A · 基础设施（23 任务，11 人天）

### A.1 Monorepo 收编（3 任务，1.5d）

#### **T-A-01** 创建 monorepo 根骨架
- **产出**：`pnpm-workspace.yaml` + `turbo.json` + 根 `package.json` + `.gitignore` + `pnpm-lock.yaml`
- **验收**：
  - [ ] `pnpm install` 成功，无 peer warning
  - [ ] `pnpm -r list` 显示 `apps/*` 和 `packages/*`
  - [ ] `turbo run build --dry-run` 显示任务依赖图
- **估时**：0.5d
- **依赖**：无

#### **T-A-02** 收编 `前端原型代码/` 到 `apps/web/`
- **产出**：`apps/web/src/` 完整包含原型 4114 行代码；`前端原型代码/` 目录删除
- **验收**：
  - [ ] `pnpm --filter web dev` 启动 dev server，端口 3000
  - [ ] 访问 `/` 看到完整聊天页（Sidebar + ModeIndicator + PlanCard 等）
  - [ ] `git status` 无意外 diff（除了目录移动）
- **估时**：0.5d
- **依赖**：T-A-01

#### **T-A-03** 加根 lint / format / git hooks
- **产出**：`eslint.config.mjs`（共享） + `prettier.config.mjs` + `.husky/pre-commit`
- **验收**：
  - [ ] `pnpm lint` 跑通所有 workspace
  - [ ] `pnpm format` 自动修所有文件
  - [ ] commit 触发 lint-staged
- **估时**：0.5d
- **依赖**：T-A-01

### A.2 共享 tsconfig（2 任务，0.5d）

#### **T-A-04** 抽 `packages/tsconfig/base.json`
- **产出**：`strict + bundler + paths`，所有子 package 继承
- **验收**：
  - [ ] `apps/web/tsconfig.json` 改为 `extends: "@gaokao/tsconfig/base.json"`
  - [ ] `pnpm --filter web typecheck` 0 error
- **估时**：0.25d
- **依赖**：T-A-02

#### **T-A-05** 共享 `tsconfig.lib.json`（含 `composite: true` + `declaration: true`）
- **产出**：`packages/tsconfig/lib.json` 给 `packages/ui` 等需要 build 的用
- **验收**：
  - [ ] `packages/ui/tsconfig.json` extends lib
  - [ ] `pnpm --filter @gaokao/ui build` 生成 `dist/index.d.ts`
- **估时**：0.25d
- **依赖**：T-A-04

### A.3 设计系统提取（3 任务，1.5d）

#### **T-A-06** 移 `design-system.css` 到 `packages/ui/tokens/`
- **产出**：`packages/ui/tokens/design-system.css`（247 行，1:1 搬迁不改内容）
- **验收**：
  - [ ] `apps/web/src/styles/design-system.css` 改为 re-export 或删除
  - [ ] Chromatic baseline 截图 0 diff
  - [ ] `globals.css` 的 `@import` 路径更新
- **估时**：0.5d
- **依赖**：T-A-04
- **约束**：§1.1（design tokens 不可改值）

#### **T-A-07** 移 `lib/theme.ts` 到 `packages/ui/tokens/`
- **产出**：`packages/ui/tokens/theme.ts`（含 `initThemeScript / getEffectiveTheme / setTheme / isDarkMode` 4 个函数，1:1 搬迁）
- **验收**：
  - [ ] `apps/web/src/lib/theme.ts` 删除
  - [ ] `layout.tsx` import 路径更新
  - [ ] 三态主题切换功能 0 回归（Playwright `theme.spec.ts` 全绿）
- **估时**：0.5d
- **依赖**：T-A-06
- **约束**：§1.2（闪白防护必须保留）

#### **T-A-08** 写 `packages/ui/tokens/index.ts` barrel
- **产出**：re-export 全部 token + theme 函数
- **验收**：
  - [ ] `import { ..., getEffectiveTheme, setTheme, ... } from '@gaokao/ui/tokens'` 工作
- **估时**：0.5d
- **依赖**：T-A-07

### A.4 UI 组件库起步（5 任务，2.5d）

#### **T-A-09** Button 组件
- **产出**：`packages/ui/components/Button.tsx` + `Button.test.tsx` + `Button.stories.tsx`
- **variant**：`primary | secondary | ghost | danger`
- **size**：`sm | md | lg`
- **验收**：
  - [ ] 4 variant × 3 size = 12 个 story
  - [ ] Vitest 覆盖：点击事件 / disabled / loading 状态
  - [ ] axe 0 critical
- **估时**：0.5d
- **依赖**：T-A-08

#### **T-A-10** Input / Select / Textarea 组件
- **产出**：`packages/ui/components/{Input,Select,Textarea}.tsx` + 各自 test + story
- **特性**：`error | helpText | touched` 三态
- **验收**：
  - [ ] FormCard 改用 Input 组件（视觉 0 回归）
  - [ ] Vitest 覆盖必填 / 错误提示 / 受控值
- **估时**：0.5d
- **依赖**：T-A-09

#### **T-A-11** Card 组件
- **产出**：`packages/ui/components/Card.tsx`
- **API**：`<Card>{children}</Card>` —— 圆角 2xl + 阴影 sm + border gray-200
- **验收**：
  - [ ] PlanCard / AuditReportCard / CareerCard / FileUploadPrompt 全部改用 Card
  - [ ] 视觉 0 回归
- **估时**：0.5d
- **依赖**：T-A-08

#### **T-A-12** Badge 组件
- **产出**：`packages/ui/components/Badge.tsx`
- **API**：`<Badge variant="risk-high | risk-medium | risk-low | neutral">{label}</Badge>`
- **验收**：
  - [ ] PlanCard 风险徽章 / PlanCard 调整徽章 / plans/page 院校统计徽章 全部改用
  - [ ] 视觉 0 回归
- **估时**：0.25d
- **依赖**：T-A-08

#### **T-A-13** Tabs 组件
- **产出**：`packages/ui/components/Tabs.tsx`
- **API**：`<Tabs items={[{key,label,color}]} activeKey onChange>` —— ARIA `role="tablist/tab"`
- **验收**：
  - [ ] PlanCard 改用 Tabs
  - [ ] plans/[id]/page.tsx 改用 Tabs
  - [ ] 视觉 0 回归
  - [ ] Vitest 覆盖 active 切换 + 键盘箭头导航（WCAG 2.1.1）
- **估时**：0.75d
- **依赖**：T-A-09
- **约束**：§1.6（PlanCard 三 Tab 不可改结构）

### A.5 测试基础设施（4 任务，1.5d）

#### **T-A-14** Vitest + RTL + MSW 配置
- **产出**：
  - `packages/test-utils/vitest.config.ts`
  - `packages/test-utils/setup.ts`（jest-dom matchers + MSW server）
  - `packages/test-utils/renderWithProviders.tsx`（QueryClient + Theme + Router）
- **验收**：
  - [ ] `pnpm --filter web test` 跑通
  - [ ] 占位测试 `Math.test.ts` 1 绿
- **估时**：0.5d
- **依赖**：T-A-01

#### **T-A-15** 示范单测：ModeIndicator
- **产出**：`ModeIndicator.test.tsx`
- **覆盖**：
  - 4 个 mode 各渲染对应 label
  - `deriveMode` 决策树：
    - isAuditActive → auditing
    - currentPlan + no audit → adjusting
    - province + score → generating
    - 其他 → explore
- **验收**：
  - [ ] 100% line + branch coverage
- **估时**：0.25d
- **依赖**：T-A-14
- **约束**：§1.4（4 模式决策树）

#### **T-A-16** 示范单测：SafeMarkdown
- **产出**：`SafeMarkdown.test.tsx`
- **覆盖 XSS 注入**：
  - `<script>alert(1)</script>` → 渲染为文本，不执行
  - `<img src=x onerror=alert(1)>` → onerror 被剥
  - `<a href="javascript:alert(1)">` → href 被 sanitize
- **验收**：
  - [ ] 3 个注入用例全过
  - [ ] 正常 markdown（h1/ul/code/blockquote）渲染正确
- **估时**：0.25d
- **依赖**：T-A-14
- **约束**：§0.1 R-NEW（XSS 防护不可破）

#### **T-A-17** 示范单测：FormCard
- **产出**：`FormCard.test.tsx`
- **覆盖**：
  - 字段 touched 后才显示验证
  - 跳步守卫（basic 未完成不能进 subjects）
  - 提交时 subjects 数组拼装正确
- **验收**：
  - [ ] 80% line coverage
- **估时**：0.5d
- **依赖**：T-A-14
- **约束**：§1.10（不允许跳步）

### A.6 Playwright e2e 骨架（3 任务，1.5d）

#### **T-A-18** Playwright 配置
- **产出**：`apps/web/e2e/playwright.config.ts`（chromium + webkit + 2 个 mobile viewport）
- **验收**：
  - [ ] `pnpm --filter web e2e` 启动浏览器
  - [ ] `apps/web/e2e/smoke.spec.ts` 通过（仅访问 `/` 看到 Sidebar）
- **估时**：0.5d
- **依赖**：T-A-14

#### **T-A-19** 示范 e2e：theme.spec
- **产出**：`theme.spec.ts`
- **覆盖**：
  - 切到 dark → `data-theme="dark"` 出现
  - 切到 system → `data-theme` 移除
  - **刷新页面后** localStorage 保留选择
  - 视觉无闪白（`page.waitForLoadState('domcontentloaded')` 在 100ms 内）
- **验收**：
  - [ ] 3 个主题切换场景全绿
- **估时**：0.5d
- **依赖**：T-A-18
- **约束**：§1.2（闪白防护）

#### **T-A-20** 示范 e2e：navigation.spec
- **产出**：`navigation.spec.ts`
- **覆盖**：
  - 桌面 viewport (1280) → Sidebar 可见，MobileNav 隐藏
  - 移动 viewport (375) → MobileNav 可见，Sidebar 隐藏
  - 点击 Sidebar /plans → 跳转
  - 点击 MobileNav /plans → 跳转
- **验收**：
  - [ ] 4 个场景全绿
- **估时**：0.5d
- **依赖**：T-A-18
- **约束**：§1.7（1024 断点）

### A.7 OpenAPI 类型化（2 任务，1.5d）

#### **T-A-21** OpenAPI Codegen 接入
- **产出**：
  - `packages/api-client/codegen.config.ts`
  - `packages/api-client/src/index.ts`（自动生成）
  - `turbo.json` 加 `generate-api-client` 任务，依赖 `^build-admin`
- **验收**：
  - [ ] `pnpm --filter @gaokao/api-client generate` 跑通
  - [ ] 生成 `dist/services/AuthService.ts` 等
- **估时**：1d
- **依赖**：T-A-01

#### **T-A-22** 示范调用：mock server
- **产出**：`apps/web/lib/api/chat.ts`（先用 MSW mock）
- **API**：
  ```ts
  export const apiClient = {
    chat: {
      send: (consultationId: string | undefined, body: { message: string }) => Promise<ChatResponse>,
      getHistory: (consultationId: string) => Promise<{ messages: Message[] }>,
    }
  };
  ```
- **验收**：
  - [ ] MSW handler 拦截 `/api/chat/send` 返回 mock
  - [ ] `page.tsx` 临时接 apiClient.chat.send（**不替换 useChat**，仅验证类型管道通）
- **估时**：0.5d
- **依赖**：T-A-21
- **约束**：§0.1 R-NEW-3（match 1-5 校验，Zod schema `z.number().int().min(1).max(5)`）

### A.8 CI 工作流（1 任务，1d）

#### **T-A-23** web-ci.yml
- **产出**：`.github/workflows/web-ci.yml`
- **步骤**：
  1. `pnpm install --frozen-lockfile`
  2. `pnpm turbo run lint typecheck test --filter=@gaokao/* --filter=web`
  3. `pnpm turbo run e2e --filter=web`
  4. `pnpm turbo run build --filter=@gaokao/* --filter=web`
  5. 上传 Codecov（前端 target）
- **验收**：
  - [ ] PR 触发后绿/红信号可见
  - [ ] 总耗时 < 8 分钟
  - [ ] bundle size > 200KB 时 PR 评论 warn
- **估时**：1d
- **依赖**：T-A-19, T-A-20, T-A-22

---

## 阶段 B · 真实后端对接（21 任务，30 人天）

### B.1 后端 API 补全（5 任务，6d，先于 B.2）

> 此节为**后端任务清单**，前端实施时**不写代码**，仅跟踪完成状态。

#### **T-B-01** `POST /api/chat/send`
- **入参**：`{message: string, consultation_id?: string, profile_snapshot?: object}`
- **出参**：`{user_message: Message, assistant_message: Message, consultation_id: string}`
- **验收**：
  - [ ] OpenAPI schema 完整
  - [ ] 与后端 `Consultation` / `Message` 模型对齐
  - [ ] 错误码 E03001/03002/03003 覆盖
- **估时**：1.5d

#### **T-B-02** `GET /api/chat/history?consultation_id=...`
- **出参**：`{messages: Message[]}`
- **验收**：
  - [ ] 分页参数（cursor）支持
  - [ ] auth：必须登录或持有 consultation_id 的访问令牌
- **估时**：0.5d

#### **T-B-03** `GET /api/consultations` / `GET /api/consultations/{id}` / `DELETE /api/consultations/{id}`
- **验收**：
  - [ ] 列表返回 `{consultations: [{id, title, updated_at, profile, has_plan, has_audit}]}`
  - [ ] 详情返回完整 messages + profile + plan + audit
  - [ ] DELETE 软删除 + 数据保留 30 天
- **估时**：1d

#### **T-B-04** `GET /api/plans` / `GET /api/plans/{id}` / `PATCH /api/plans/{id}` / `DELETE /api/plans/{id}`
- **验收**：
  - [ ] 列表返回 `{plans: [{id, name, created_at, profile, distribution: {rush,stable,safe}}]}`
  - [ ] PATCH 仅支持 name 修改
  - [ ] DELETE 软删除
- **估时**：1d

#### **T-B-05** `POST /api/assessment` / `POST /api/audit/upload`
- **audit/upload**：multipart/form-data，Excel/Image/PDF/Paste
- **出参**：`{report_id, overall_score, summary, risk_items, distribution, good_points}`
- **验收**：
  - [ ] 文件大小限制：Excel 5MB / Image 10MB / PDF 10MB
  - [ ] MIME 校验
  - [ ] 解析后存 DB + 触发 AI 审核
- **估时**：2d

### B.2 useChat 真实化（4 任务，5d）

#### **T-B-12** 拆 useChat 编排层
> **本任务是为了解决 R-NEW-1**：先把 useChat 的 mock 拆出来
- **产出**：
  - `useChat.ts` 改为纯编排（无 mock 数据）
  - mock 数据移到 `apps/web/__mocks__/chat-fixtures.ts`（仅 B 阶段测试用）
- **验收**：
  - [ ] useChat.ts < 300 行
  - [ ] `__mocks__/chat-fixtures.ts` 包含：广东省物理 620、广东省历史 580、河北省物理 600 共 3 套 mock
- **估时**：1.5d
- **依赖**：T-B-01 ~ T-B-05（API 已就位）
- **约束**：§0.1 R-NEW-1

#### **T-B-13** 真实 sendMessage + typing 动画
- **产出**：mutation + optimistic update
- **验收**：
  - [ ] e2e `chat-send.spec.ts`：输入消息 → 1s 内出现用户气泡 → 3s 内出现 AI 回复
  - [ ] 失败时乐观更新回滚 + Toast 提示
  - [ ] typing 动画 (`page.tsx:173-186`) 保留
- **估时**：1d
- **依赖**：T-B-12
- **约束**：§1.3（消息路由模式）

#### **T-B-14** 真实 getHistory + 滚动恢复
- **产出**：consultation 切换时 fetch 历史
- **验收**：
  - [ ] 切换 consultation_id → 加载历史消息
  - [ ] 自动滚动到底部（`messagesEndRef`）
  - [ ] 加载中显示 Skeleton（用 T-D-09 阶段组件）
- **估时**：1d
- **依赖**：T-B-13

#### **T-B-15** usePlan / useConsultation 真实化 + localStorage 兼容
- **产出**：
  - 删除 `useChat.ts` 中 `savePlan` 的 localStorage 写
  - 改用 `apiClient.plans.create(...)` mutation
  - **保留** localStorage `consultationRecords` / `activeConsultationId` key 名作为离线 fallback（**R-NEW-2 应对**）
- **验收**：
  - [ ] 真实保存方案 → DB 可见
  - [ ] 断网时本地仍可见上次同步数据
  - [ ] 联网后自动 revalidate（TanStack Query 默认行为）
- **估时**：1.5d
- **依赖**：T-B-04, T-B-05
- **约束**：§0.1 R-NEW-2（保留 key 名兼容）

### B.3 useProfile / 表单 / 错误处理（6 任务，6d）

#### **T-B-16** 真实 useProfile
- **产出**：`GET /api/profile` 拉取，表单提交用 `PATCH /api/profile`
- **验收**：
  - [ ] FormCard 提交后立即看到进度条（InfoCollectionProgress）填充
  - [ ] 失败时回滚 + 错误提示
- **估时**：1d
- **依赖**：T-B-15

#### **T-B-17** 真实 useAudit
- **产出**：`POST /api/audit/upload` multipart
- **验收**：
  - [ ] 4 种文件类型（Excel/Image/PDF/Paste）全部走真实 API
  - [ ] 进度条（上传 + AI 处理）显示
  - [ ] 错误码 E04001（上游 AI 失败）→ Toast 重试
- **估时**：1.5d
- **依赖**：T-B-05

#### **T-B-18** 错误码 → 用户文案映射
- **产出**：`packages/i18n/zh-CN/errors.json`
- **示例**：
  ```json
  {
    "E03001": "信息验证失败，请检查输入",
    "E03002": "数据未找到",
    "E03003": "保存失败，请重试",
    "E04001": "AI 服务暂时不可用，请稍后重试",
    "E04002": "请求超时，请重试",
    "E05001": "系统错误，我们已记录"
  }
  ```
- **验收**：
  - [ ] 15 个错误码全覆盖
  - [ ] api-client 拦截器统一处理
- **估时**：0.5d
- **依赖**：T-B-13
- **约束**：沿用 `admin/errors/registry.py` 5 字段结构

#### **T-B-19** ErrorBoundary 兜底页
- **产出**：`apps/web/app/error.tsx`（Next 16 error boundary）
- **验收**：
  - [ ] 5xx 错误时显示兜底页（"出错了，刷新重试"）
  - [ ] Sentry 上报
- **估时**：0.5d
- **依赖**：T-B-18

#### **T-B-20** 离线检测 + 提示
- **产出**：`useOnlineStatus` hook + 顶部黄条提示
- **验收**：
  - [ ] offline → 顶部条 + 写操作禁用
  - [ ] online 恢复 → 自动重试 pending mutations
- **估时**：1d

#### **T-B-21** 表单提交防重复
- **产出**：所有 mutation 加 `isPending` 状态
- **验收**：
  - [ ] FormCard 提交按钮在 isPending 时禁用 + 旋转图标
  - [ ] ChatMessage 的修复按钮单次点击后禁用
- **估时**：0.5d

### B.4 离线缓存 + e2e + 性能（6 任务，6d）

#### **T-B-22** TanStack Query 持久化
- **产出**：`@tanstack/query-persist-client-core` + localStorage
- **验收**：
  - [ ] 关闭浏览器再打开 → 历史消息立即可见
  - [ ] 后台 revalidate 后更新
- **估时**：1d
- **依赖**：T-B-13

#### **T-B-23** e2e 真实化（5 个关键路径）
- **产出**：
  - `chat-send.spec.ts` 真实发消息
  - `chat-history.spec.ts` 切换 consultation
  - `plan-save.spec.ts` 保存方案
  - `audit-upload.spec.ts` 上传文件
  - `theme-persist.spec.ts` 主题持久化
- **验收**：
  - [ ] 5 个 spec 全绿
  - [ ] 每个 spec 含 1 个失败场景（网络断、文件超限等）
- **估时**：2d
- **依赖**：T-B-13, T-B-15, T-B-17

#### **T-B-24** Lighthouse CI 集成
- **产出**：`lighthouserc.json` + GitHub Action
- **预算**：
  - LCP < 2.5s
  - INP < 200ms
  - CLS < 0.1
  - Performance ≥ 90
  - Accessibility ≥ 95
  - Best Practices ≥ 95
  - SEO ≥ 90
- **验收**：
  - [ ] 5 个页面（/ /consultations /plans /plans/compare /assessment）P75 ≥ 预算
  - [ ] PR 评论显示分数
- **估时**：1d

#### **T-B-25** Bundle 优化
- **产出**：
  - `next/dynamic` 异步加载 PlanCard / AuditReportCard / CareerCard
  - `react-markdown` 异步 chunk
  - 拆 vendor chunk
- **验收**：
  - [ ] First load JS < 200KB
  - [ ] PlanCard 异步 chunk < 50KB
- **估时**：1d

#### **T-B-26** 路由级 prefetch
- **产出**：`<Link prefetch>` 关键路径
- **验收**：
  - [ ] hover Sidebar /plans → 100ms 内开始预取
- **估时**：0.5d

#### **T-B-27** 真实后端回归
- **产出**：完整 e2e 套件在真实后端跑通
- **验收**：
  - [ ] 15+ e2e spec 全绿
  - [ ] 跨 3 浏览器（chromium / webkit / firefox）通过
- **估时**：0.5d
- **依赖**：T-B-23 ~ T-B-26

---

## 阶段 C · 架构整合（13 任务，9d）

### C.1 部署架构（5 任务，3d）

#### **T-C-01** 选部署平台
- **决策点**：CloudStudio / Vercel / 自托管
- **默认**：CloudStudio（项目已有先例）
- **验收**：
  - [ ] 决策文档写入 `docs/DEPLOY_DECISION.md`
- **估时**：0.25d

#### **T-C-02** DNS + 域名
- **产出**：`web.gaokao.example.com` / `api.gaokao.example.com`
- **验收**：
  - [ ] HTTPS 证书自动续签（Let's Encrypt）
- **估时**：0.5d

#### **T-C-03** 反代配置
- **产出**：nginx / caddy 配置
  - `web.gaokao.example.com` → Next.js 静态产物
  - `api.gaokao.example.com` → FastAPI
  - `/api/*` → 转发到 FastAPI
- **验收**：
  - [ ] 单一域名访问前端，浏览器无 CORS 报错
- **估时**：1d

#### **T-C-04** CORS 配置
- **产出**：FastAPI `CORSMiddleware` 白名单 `["https://web.gaokao.example.com"]`
- **验收**：
  - [ ] OPTIONS 预检通过
  - [ ] 带 cookie 时白名单明确
- **估时**：0.25d

#### **T-C-05** CSP / HSTS / 安全响应头
- **产出**：`secure_headers` 中间件
- **验收**：
  - [ ] `Strict-Transport-Security: max-age=63072000; includeSubDomains`
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-Frame-Options: DENY`
  - [ ] `Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; ...`
  - [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- **估时**：1d
- **依赖**：T-C-04

### C.2 监控（4 任务，2d）

#### **T-C-06** Sentry 前端
- **产出**：`@sentry/nextjs` 集成
- **验收**：
  - [ ] 错误 100% 上报
  - [ ] Performance trace 包含路由切换
  - [ ] PII 脱敏（用户消息不含姓名/手机号）
- **估时**：1d

#### **T-C-07** Web Vitals 上报
- **产出**：`next/web-vitals` + 自托管 endpoint
- **验收**：
  - [ ] LCP / INP / CLS / FID / TTFB 全部上报
  - [ ] 75 分位数存储到 Prometheus
- **估时**：0.5d

#### **T-C-08** trace 透传
- **产出**：`x-trace-id` header 前后端贯通
- **验收**：
  - [ ] 前端请求带 trace id
  - [ ] 后端日志 / Sentry 关联到同一 trace
- **估时**：0.5d

#### **T-C-09** 告警规则
- **产出**：3 条告警（错误率 > 1% / API P95 > 1s / Web Vitals P75 跌破预算）
- **验收**：
  - [ ] Slack / 钉钉 webhook 接收
- **估时**：0d（仅配置）

### C.3 文档 + 收口（4 任务，4d）

#### **T-C-10** 部署文档
- **产出**：`docs/DEPLOY.md`（含 CloudStudio / 自托管 / Vercel 三种路径）
- **估时**：1d

#### **T-C-11** 运维 Runbook
- **产出**：`docs/RUNBOOK.md`（常见故障处理）
- **估时**：1d

#### **T-C-12** 安全审计
- **产出**：`docs/SECURITY_AUDIT_2026-XX.md`（OWASP top 10 自查）
- **估时**：1d

#### **T-C-13** 灰度发布流程
- **产出**：5% → 20% → 100% 三步灰度
- **估时**：1d

---

## 阶段 D · 设计 / a11y 加固（18 任务，11d）

### D.1 基础组件补齐（10 任务，4d）

| 任务 | 组件 | 估时 | 验收 |
|---|---|---|---|
| **T-D-01** | Dialog | 0.5d | 用 portal 渲染 + 焦点陷阱 + ESC 关闭 + 点击外部关闭 |
| **T-D-02** | Toast | 0.5d | success/error/info/warn 4 种 + 自动消失 + 队列管理 |
| **T-D-03** | Tooltip | 0.25d | hover 200ms 显示，3s 自动消失 |
| **T-D-04** | Dropdown | 0.5d | Sidebar 头像菜单用，键盘导航 |
| **T-D-05** | Avatar | 0.25d | AI / User / 群组 3 套 |
| **T-D-06** | Skeleton | 0.25d | 4 种形状（text/card/circle/avatar） |
| **T-D-07** | ProgressBar | 0.25d | 通用（区别于 InfoCollectionProgress） |
| **T-D-08** | Switch | 0.25d | 偏好设置用 |
| **T-D-09** | Checkbox | 0.5d | FormCard 选科用 |
| **T-D-10** | Radio | 0.5d | 独立于 ThemeToggle，FormCard 单选用 |

每个组件 5 个验收：① Vitest ② Storybook ③ axe ④ 用到原型 1 处 ⑤ 视觉 0 回归

### D.2 a11y 全量审计（3 任务，2d）

#### **T-D-11** axe-core 集成
- **产出**：`@axe-core/playwright` + 5 个页面自动扫描
- **验收**：
  - [ ] 0 critical / 0 serious 违规
  - [ ] CI 卡点（PR 触发）
- **估时**：0.5d

#### **T-D-12** 屏幕阅读器 + 键盘测试
- **产出**：测试报告 `docs/A11Y_TEST_2026-XX.md`
- **覆盖**：
  - [ ] NVDA 朗读 / 方案卡 / 审核卡
  - [ ] VoiceOver 移动端测试
  - [ ] Tab 顺序：Sidebar → Main → Quick prompts → Upload → Input → Send
  - [ ] Skip link 工作
- **估时**：1d

#### **T-D-13** 替换 alert() 为 Toast（**R-NEW-4 应对**）
- **产出**：
  - `plans/[id]/page.tsx:143,152` 的 alert 替换为 Toast
  - 异步触发下载（`URL.createObjectURL` + `<a download>`）
- **验收**：
  - [ ] 导出图片 / PDF 真实下载
  - [ ] Toast 提示"已导出方案 / 导出失败"
- **估时**：0.5d
- **依赖**：T-D-02

### D.3 暗色主题全覆盖（1 任务，1.5d）

#### **T-D-14** 暗色变体审计
- **产出**：每个组件 dark 变体
- **验收**：
  - [ ] 15+ 组件都有 dark story
  - [ ] 视觉切换无白边/无对比度 < 4.5:1
  - [ ] 风险徽章 / 概率条 / 模式指示器 暗色下语义色保持
- **估时**：1.5d
- **依赖**：T-D-01 ~ T-D-10

### D.4 国际化基础（2 任务，2d）

#### **T-D-15** next-intl 接入
- **产出**：
  - `packages/i18n/zh-CN/{chat,plans,common,errors}.json`
  - `packages/i18n/en-US/{...}.json`（占位空字典）
  - 路由级 locale 切换
- **验收**：
  - [ ] 所有硬编码中文移到词条
  - [ ] 切到 en-US 显示 key 而非中文（占位）
- **估时**：1.5d
- **依赖**：T-B-18（错误码词条已存在）
- **约束**：§0.1 R-NEW-5（quickPrompts 三态文案抽到 `chat.json`）

#### **T-D-16** 文案审计
- **产出**：i18n key 命名规范文档
- **验收**：
  - [ ] `git grep "[\u4e00-\u9fff]"` 在 `apps/web/src/` 仅命中 `i18n/` 目录
- **估时**：0.5d
- **依赖**：T-D-15

### D.5 性能 + 视觉回归（2 任务，1.5d）

#### **T-D-17** Chromatic 视觉回归
- **产出**：所有 Storybook stories 接入 Chromatic
- **验收**：
  - [ ] 30+ stories baseline
  - [ ] 像素 diff > 0.1% 触发 review
- **估时**：1d

#### **T-D-18** 性能深度优化
- **产出**：
  - `next/image` 全量替换
  - `next/font` 优化
  - Critical CSS 内联
  - 路由级 `loading.tsx`
- **验收**：
  - [ ] LCP P75 < 1.8s（再降 30%）
  - [ ] Bundle < 150KB
- **估时**：0.5d

---

## 阶段 E · 内部页面 React 化（16 任务，17d）

### E.1 运营后台基础（4 任务，4d）

| 任务 | 页面 | 估时 | 验收 |
|---|---|---|---|
| **T-E-01** | 登录页 `/admin/login` | 0.5d | 复用 T-A-09 Button + T-A-10 Input；调 `POST /api/admin/auth/login` |
| **T-E-02** | Dashboard `/admin` | 1.5d | echarts 集成（订单/咨询趋势） + 4 个 KPI 卡片 |
| **T-E-03** | Layout `/admin` shared | 1d | 顶部 nav + 侧边栏 + 暗色支持 |
| **T-E-04** | 错误兜底 `/admin/error.tsx` | 0.5d | 同 T-B-19 |
| **T-E-05** | 权限守卫 | 0.5d | 未登录跳 /admin/login |

### E.2 订单 + 案例（4 任务，4d）

| 任务 | 页面 | 估时 |
|---|---|---|
| **T-E-06** | 订单列表 `/admin/orders` | 1d |
| **T-E-07** | 订单详情 `/admin/orders/{id}` | 1.5d |
| **T-E-08** | 案例列表 `/admin/cases` | 0.75d |
| **T-E-09** | 案例详情 `/admin/cases/{id}` | 0.75d |

### E.3 分享 + 短链接（4 任务，4d）

| 任务 | 页面 | 估时 |
|---|---|---|
| **T-E-10** | 分享页 editor `/admin/share/{code}` | 1.5d（权限矩阵复杂） |
| **T-E-11** | 短链接管理 `/admin/short-links` | 1d |
| **T-E-12** | 分享统计 `/admin/share/{code}/stats` | 0.75d |
| **T-E-13** | 分享审计 `/admin/share/{code}/audit` | 0.75d |

### E.4 通知 + 设置（4 任务，5d）

| 任务 | 页面 | 估时 |
|---|---|---|
| **T-E-14** | 通知列表 `/admin/notifications` | 1d |
| **T-E-15** | 通知模板编辑 | 1.5d |
| **T-E-16** | 系统设置 `/admin/settings` | 1.5d |
| **T-E-17** | 用户管理 `/admin/users` | 1d |

---

## 2. 完整验收矩阵（Definition of Done）

> 这是**自检通过**的硬指标。每一行都对应 self-review 三大目标（UI/交互 / 功能完整 / 后端集成）。

### 2.1 UI/交互完全遵循新设计（**Self-Review #1**）

| 检查项 | 工具 | 通过标准 |
|---|---|---|
| **Chromatic 视觉回归** | Chromatic | 0 story 像素 diff > 0.1% |
| **设计 token 一致性** | 自定义 lint 规则 | `apps/web/src/` 中无硬编码 `#xxx` 颜色（仅 `globals.css` 允许） |
| **三态主题切换无闪白** | Playwright `theme.spec.ts` | refresh 后 100ms 内 `data-theme` 正确 |
| **移动端断点** | Playwright | 768 / 1024 两断点行为与原型 1:1 |
| **WCAG 2.1 AA** | axe-core | 0 critical / 0 serious / < 3 moderate |
| **键盘导航** | Playwright + 手动 | Tab 顺序符合预期；Enter / Space 触发控件 |
| **屏幕阅读器** | NVDA + VoiceOver | 4 模式指示器 / PlanCard Tabs / AuditReportCard 风险 全部朗读合理 |
| **所有硬约束** | 见 §0.2 表格 | 8/8 通过（任务化于 T-A-14 ~ T-A-19 单测） |

### 2.2 所有的功能都能完整实现（**Self-Review #2**）

| 模块 | 功能 | 任务 |
|---|---|---|
| **对话** | 发消息 / 收 AI 回复 / 打字动画 / 快捷提示三态 / 滚动恢复 | T-B-13, T-B-14 |
| **方案生成** | AI 推方案 / PlanCard 三 Tab / 风险徽章 / 概率条 / 展开详情 | T-A-13, T-B-12 |
| **方案保存** | 保存 / 重命名 / 删除 / 列表 / 详情 | T-B-15 |
| **方案对比** | 选 2 个 / 维度表 / 差异高亮 / 院校列表并排 | T-E-06（前端原型已实现 B 阶段复用） |
| **方案导出** | 图片 / PDF | T-D-13 |
| **方案审核** | 上传 / 风险项 / 冲稳保分布 / 良好项 / 一键修复 | T-B-17 |
| **咨询记录** | 列表 / 搜索 / 删除 / 恢复 | T-B-15 |
| **兴趣测评** | Holland RIAS 10 题 / 进度 / 结果 / 加入偏好 | T-B-01（需要后端 API，**目前原型纯前端**） |
| **表单分步** | basic → subjects → prefs 跳步守卫 / 字段验证 | T-A-17, T-B-16 |
| **文件上传** | Excel/Image/PDF/Paste 4 模式 | T-B-17 |
| **主题切换** | light/dark/system + 持久化 + 闪白防护 | T-A-07, T-A-19 |
| **响应式** | Sidebar 桌面 / MobileNav 移动 / 头部响应式 | T-A-20 |
| **a11y** | ARIA / focus-visible / reduced-motion | T-D-11, T-D-12 |
| **i18n** | zh-CN 完整 / en-US 占位 | T-D-15 |
| **错误处理** | ErrorBoundary / Toast / 错误码映射 | T-B-18, T-B-19 |
| **离线** | 检测 / 提示 / 缓存 | T-B-20, T-B-22 |

### 2.3 与后端集成正常（**Self-Review #3**）

| 集成点 | API | 任务 |
|---|---|---|
| **登录** | `POST /api/admin/auth/login` | T-E-01 |
| **对话** | `POST /api/chat/send` + `GET /api/chat/history` | T-B-01, T-B-02, T-B-13 |
| **profile** | `GET / PATCH /api/profile` | T-B-16 |
| **方案** | `CRUD /api/plans` | T-B-04, T-B-15 |
| **咨询** | `CRUD /api/consultations` | T-B-03, T-B-15 |
| **审核上传** | `POST /api/audit/upload`（multipart） | T-B-05, T-B-17 |
| **兴趣测评** | `POST /api/assessment` | T-B-05（后端） |
| **错误码** | 沿用 `admin/errors/registry.py` 5 字段 | T-B-18 |
| **CORS** | 白名单 `web.gaokao.example.com` | T-C-04 |
| **trace 贯通** | `x-trace-id` header | T-C-08 |
| **Sentry** | 前后端 trace 关联 | T-C-06, T-C-08 |

---

## 3. 风险与缓解（更新版）

| ID | 风险 | 缓解任务 |
|---|---|---|
| R-NEW-1 | useChat 编排层耦合 mock | T-B-12 显式解耦 |
| R-NEW-2 | localStorage key 兼容 | T-B-15 保留 key 名 |
| R-NEW-3 | CareerCard match 字段无校验 | T-A-22 Zod schema 约束 |
| R-NEW-4 | alert() 阻塞真实环境 | T-D-13 Toast 替换 |
| R-NEW-5 | quickPrompts 硬编码 | T-D-15 抽到 i18n |
| R-V2-1 | 真实 API 与 mock 结构不一致 | T-A-21 OpenAPI Codegen 第一天跑通 |
| R-V2-2 | Next 16 + React 19 + TanStack Query 兼容性 | T-A-22 提前 spike |
| R-V2-3 | Bundle 爆炸 | T-B-25 异步 chunk |
| R-V2-4 | 老用户数据迁移 | T-B-15 保留 localStorage key 名 |
| R-V2-5 | ChatMessage 路由扩展性 | T-B-13 拆 useChat 编排层 |

---

## 4. 工时总览

| 阶段 | 任务数 | 估时（人天） |
|---|---|---|
| A. 基础设施 | 23 | 11 |
| B. 真实后端对接 | 21 | 30 |
| C. 架构整合 | 13 | 9 |
| D. 设计/a11y 加固 | 18 | 11 |
| E. 内部页面 React 化 | 16 | 17 |
| **总计** | **91** | **78** |

与 V2 报告（66-89 人天）一致，**78 在中位**。

---

## 5. 立即可执行（本周启动，5 任务，4.5d）

按依赖顺序：
1. **T-A-01**（0.5d）→ 创建 monorepo
2. **T-A-02**（0.5d）→ 收编前端原型代码
3. **T-A-06 + T-A-07**（1d）→ 设计系统提取
4. **T-A-21**（1d）→ OpenAPI Codegen 接入
5. **T-A-23**（1.5d）→ CI 工作流（含最小 e2e）

**5 任务完成后**，进入 T-A-04（tsconfig 共享）+ T-A-14（Vitest）+ T-A-18（Playwright），构成 A 阶段前半段。

---

## 6. Self-Review 闭环

| Self-Review 目标 | 验证产物 | 状态 |
|---|---|---|
| **UI/交互完全遵循新设计** | Chromatic baseline 0 diff + axe 0 critical + 8 项硬约束单测全绿 | **任务化** §2.1 |
| **所有的功能都能完整实现** | 16 模块 × 任务覆盖矩阵（§2.2） | **覆盖** 16/16 |
| **与后端的集成正常** | 11 集成点 × 任务覆盖矩阵（§2.3） | **覆盖** 11/11 |
| **5 个新风险** | R-NEW-1 ~ R-NEW-5 全部有应对任务 | **闭环** |
| **可验收粒度** | 每个任务有 ID / 标题 / 验收标准 / 估时 / 依赖 / 关联约束 | **达标** |

---

**评审完成。** 91 个任务 / 78 人天 / 18 个验收域全部就位。本任务清单可**直接进入迭代排期**，每个任务的"验收标准"可作为 PR description 模板。
