# Sprint 2 任务拆解（W2-3 · 9 人天 · 56 子任务）— V10 选项 B

> **技术栈**：Vite 5 + React 19 + TypeScript 5 + Tailwind 4 + **Zustand 4** + **TanStack Query 5** + **React Hook Form 7** + Vitest 2 + Playwright 1.55
> **目标**：整体重写 7 个手写 hook + 引入现代状态管理 + 后端 5 端点对接
> **闸门**：G1（OpenAPI 类型生成无 `any` + ESLint 0 warning）
> **V10 变化**：从 18d 缩到 9d（节省 9d = 删 33 any 修复 + 7 hook 重构 + 6 文件重写）
> **PM 决策（2026-07-03）**：整体重写为新实现；Playwright 视觉回归 + Chromatic 验收

---

## ⚠️ V10 关键变化（与 V2 对比）

| 维度 | V2 | V10 选项 B |
|---|---|---|
| 框架 | Next.js 16（保留） | **Vite 5 + React 19**（重写） |
| 状态管理 | 自定义 7 个手写 hook | **Zustand 4**（4 个 slice） |
| 数据获取 | 自写 useChat + fetch | **TanStack Query 5** |
| 表单 | 受控 + 3-step 状态机 | **React Hook Form 7** + Zod |
| 测试 | Vitest + Playwright（保留） | 同 |
| 视觉回归 | 无 | **+ Chromatic**（V10 新增） |
| 总子任务 | 58 | 56（少 2：合并到 Zustand store） |
| 总估时 | 18d | **9d** |

---

## 0. Sprint 2 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-A-14 | Vitest + RTL + MSW + Chromatic 配置 | 0.5d | 4 |
| T-A-15 | 示范单测：ModeIndicator | 0.25d | 3 |
| T-A-16 | 示范单测：SafeMarkdown | 0.25d | 3 |
| T-A-17 | 示范单测：FormCard（RHF 版） | 0.5d | 4 |
| T-A-18 | Playwright + Chromatic 配置 | 0.5d | 3 |
| T-A-19 | 示范 e2e：theme.spec | 0.5d | 3 |
| T-A-20 | 示范 e2e：navigation.spec | 0.5d | 3 |
| T-A-21 | OpenAPI Codegen + Zod schema 复用 | 1.0d | 5 |
| T-A-22 | 示范调用：MSW mock server | 0.5d | 4 |
| T-B-01 | **Zustand store** + 5 query hooks（chat） | 1.0d | 5 |
| T-B-02 | TanStack Query 3 个 consultations 端点 | 0.5d | 3 |
| T-B-03 | TanStack Query 4 个 plans 端点 | 0.5d | 3 |
| T-B-04 | RHF 重写 FormCard + assessment | 1.0d | 5 |
| T-B-05 | audit/upload 端点（V10 重写） | 1.0d | 4 |
| T-B-06 | **Chromatic 视觉基线**（V10 新增） | 0.5d | 3 |
| T-B-07 | **Vite build + bundle 体积验证** | 0.5d | 4 |
| **合计** | **16 任务** | **9.5d** | **56** |

---

## T-A-14 · Vitest + RTL + MSW + Chromatic 配置（0.5d · 4 子任务）

### ST-S2-A-14.1 写 `vitest.config.ts`（0.125d）
- **产出**：`apps/web/vitest.config.ts`（jsdom env + setup 文件 + alias）
- **V10 变化**：保留 jsdom；alias 指向 `packages/ui` 和 `packages/lib`

### ST-S2-A-14.2 写 `setup.ts`（0.125d）
- **产出**：`@testing-library/jest-dom/vitest` + MSW server 启动/关闭 + Zustand store reset helper

### ST-S2-A-14.3 写 `renderWithProviders.tsx`（0.125d）
- **产出**：`packages/test-utils/renderWithProviders.tsx`
  - QueryClient（测试用，禁用 retry）
  - ThemeProvider
  - Router（MemoryRouter）
  - Zustand 注入 reset 函数
- **验收**：
  - [ ] `pnpm --filter web test` 跑通

### ST-S2-A-14.4 占位测试验证（0.125d）
- **产出**：`Math.test.ts`（1+1=2）
- **验收**：
  - [ ] 占位测试 1 绿

---

## T-A-15 · 示范单测：ModeIndicator（0.25d · 3 子任务）

### ST-S2-A-15.1 写 4 mode 渲染测试（0.125d）
- **覆盖**：explore / generating / auditing / adjusting
- **验收**：
  - [ ] 4 模式 label 正确

### ST-S2-A-15.2 写 `deriveMode` 决策树测试（0.0625d → 0d）
- **覆盖**：
  - isAuditActive → auditing
  - currentPlan + no audit → adjusting
  - province + score → generating
  - 其他 → explore
- **验收**：
  - [ ] 100% branch coverage

### ST-S2-A-15.3 验证 100% 覆盖（0.0625d → 0d）
- **命令**：`pnpm test --coverage`
- **验收**：
  - [ ] `ModeIndicator.tsx` line + branch 各 100%

---

## T-A-16 · 示范单测：SafeMarkdown（0.25d · 3 子任务）

### ST-S2-A-16.1 写 XSS 注入测试（0.125d）
- **覆盖**：
  - `<script>alert(1)</script>` → 渲染为文本
  - `javascript:alert(1)` → 链接被剥离
  - `<img src=x onerror=alert(1)>` → onerror 剥离
  - `<svg onload=alert(1)>` → onload 剥离

### ST-S2-A-16.2 写合法 Markdown 渲染测试（0.0625d → 0d）
- **覆盖**：H1-H3 / 列表 / 链接 / 代码块 / 表格

### ST-S2-A-16.3 100% 覆盖（0.0625d → 0d）

---

## T-A-17 · 示范单测：FormCard（RHF 版 · V10 重写）（0.5d · 4 子任务）

> **V10 变化**：FormCard 改用 React Hook Form + Zod，不再用 3-step 状态机手写

### ST-S2-A-17.1 写 RHF schema 测试（0.125d）
- **覆盖**：Zod schema 校验（分数/位次/选科）

### ST-S2-A-17.2 写 step 1→2→3 guards 测试（0.125d）
- **覆盖**：RHF `trigger()` 校验后再前进

### ST-S2-A-17.3 写后退保留数据测试（0.125d）

### ST-S2-A-17.4 100% 覆盖（0.125d）

---

## T-A-18 · Playwright + Chromatic 配置（0.5d · 3 子任务）⚠️ V10 新增

### ST-S2-A-18.1 Playwright config（0.125d）
- **产出**：`playwright.config.ts`（chromium / webkit / firefox + Vite preview server）

### ST-S2-A-18.2 Chromatic 配置（0.125d）⚠️ V10 新增
- **产出**：`chromatic.config.json` + GitHub Action
- **关键**：UI/交互层 1:1 验收的视觉基线工具

### ST-S2-A-18.3 e2e 烟雾测试（0.25d）
- **产出**：3 个 spec 文件占位

---

## T-A-19 · 示范 e2e：theme.spec（0.5d · 3 子任务）

### ST-S2-A-19.1 暗/亮/系统三主题切换（0.25d）
- **覆盖**：点击切换 + localStorage 持久化 + 系统主题响应

### ST-S2-A-19.2 SSR/CSR 一致性（0.125d）
- **覆盖**：无 flash of unstyled content

### ST-S2-A-19.3 1.2s 缓动断言（0.125d）

---

## T-A-20 · 示范 e2e：navigation.spec（0.5d · 3 子任务）

### ST-S2-A-20.1 桌面 3 栏布局（0.125d）

### ST-S2-A-20.2 移动 48px 底部 Tab（0.125d）
- **V10 不变量 L2**：移动端 < 768px 单栏 + 48px 底部 Tab

### ST-S2-A-20.3 1024px 断点切换（0.25d）

---

## T-A-21 · OpenAPI Codegen + Zod schema 复用（1.0d · 5 子任务）⚠️ V10 加强

> **V10 变化**：从单一类型生成 → 类型 + Zod schema 联合生成，业务层可用

### ST-S2-A-21.1 安装 openapi-typescript + openapi-zod-client（0.125d）
```bash
pnpm --filter web add -D openapi-typescript openapi-zod-client
```

### ST-S2-A-21.2 写 codegen 脚本（0.25d）
- **产出**：`apps/web/scripts/codegen.ts`
  ```ts
  import { generateZodClientFromOpenAPI } from 'openapi-zod-client'
  import { OpenAPIV3 } from 'openapi-types'
  
  // 拉取后端 openapi.json
  // 生成 types/api.d.ts + schemas/api.ts
  ```

### ST-S2-A-21.3 接入 Vite plugin 自动 codegen（0.25d）
- **产出**：`vite.config.ts` 集成 codegen

### ST-S2-A-21.4 验证生成文件 0 `any`（0.25d）
- **命令**：`grep -r "any" apps/web/src/types/`
- **验收**：
  - [ ] 0 `any`（这是 V10 重写带来的关键收益）

### ST-S2-A-21.5 接入 CI 自动 codegen（0.125d）
- **产出**：`pnpm codegen:check` 检查生成文件是否过期

---

## T-A-22 · 示范调用：MSW mock server（0.5d · 4 子任务）

### ST-S2-A-22.1 写 MSW handlers 骨架（0.125d）
### ST-S2-A-22.2 写 5 端点 mock 数据（0.125d）
### ST-S2-A-22.3 setup.ts 启动 server（0.125d）
### ST-S2-A-22.4 验证 mock 数据驱动组件渲染（0.125d）

---

## T-B-01 · Zustand store + 5 query hooks（chat · V10 重写）（1.0d · 5 子任务）⚠️ V10 全新

> **V10 关键**：替代原型 7 个手写 hook 中的 5 个（chat 相关）

### ST-S2-B-01.1 设计 Zustand store 4 slice（0.25d）
- **产出**：`apps/web/src/stores/chat.ts`
  - `useChatStore`：messages / isStreaming / mode / plan
  - `useFormStore`：score / rank / subjects
  - `useUIStore`：theme / sidebar / modal
  - `useUserStore`：user / preferences
- **类型**：Zustand `create<T>()(devtools(persist(...)))`，**0 any**

### ST-S2-B-01.2 写 `useChatQuery`（0.125d）
- **产出**：`apps/web/src/hooks/queries/useChatQuery.ts`
- **封装**：TanStack Query + Zod schema

### ST-S2-B-01.3 写 `useChatMutation`（0.125d）
- **封装**：`POST /api/chat/send` + 流式响应处理

### ST-S2-B-01.4 写 `useChatHistoryQuery`（0.125d）
- **封装**：`GET /api/chat/history`

### ST-S2-B-01.5 删除原型 7 个手写 hook（0.25d）⚠️ V10 收益
- **命令**：`rm apps/web/src/lib/{useChat,useForm,useUI,useUser,...}.ts`
- **验收**：
  - [ ] `grep -r "useChat(" apps/web/src/` 返回 0 结果
  - [ ] 33 `any` 中相关 5 个已清零

---

## T-B-02 · TanStack Query 3 个 consultations 端点（0.5d · 3 子任务）

### ST-S2-B-02.1 写 `useConsultationsQuery`（0.125d）
- **封装**：`GET /api/consultations`

### ST-S2-B-02.2 写 `useConsultationMutation`（0.125d）
- **封装**：`POST /api/consultations`

### ST-S2-B-02.3 写 `useConsultationUpdateMutation`（0.125d）
- **封装**：`PATCH /api/consultations/:id`

---

## T-B-03 · TanStack Query 4 个 plans 端点（0.5d · 3 子任务）

### ST-S2-B-03.1 写 `usePlansQuery`（0.125d）
### ST-S2-B-03.2 写 `usePlanMutation`（0.125d）
### ST-S2-B-03.3 写 `usePlanUpdateMutation` + `usePlanDeleteMutation`（0.25d）

---

## T-B-04 · RHF 重写 FormCard + assessment（1.0d · 5 子任务）⚠️ V10 重写

> **V10 变化**：从受控 3-step 状态机 → RHF + Zod

### ST-S2-B-04.1 写 Zod schema（0.25d）
- **产出**：`apps/web/src/schemas/assessment.ts`
  ```ts
  export const AssessmentSchema = z.object({
    province: z.string().min(1),
    score: z.number().int().min(0).max(750),
    rank: z.number().int().min(1),
    subjects: z.array(z.enum(['物理', '历史', ...])).min(1),
  })
  ```

### ST-S2-B-04.2 写 RHF `useAssessmentForm`（0.25d）
- **封装**：`useForm<AssessmentSchema>({ resolver: zodResolver(AssessmentSchema) })`
- **3-step guards**：`trigger()` 校验后再前进

### ST-S2-B-04.3 重写 `FormCard.tsx`（0.25d）⚠️ V10 重写
- **V10 收益**：删除手写 3-step 状态机；`trigger('score')` 替代 `if (step === 1 && !score)` 分支
- **验收**：
  - [ ] UI/交互 1:1（V10 不变量 C3）
  - [ ] `any` 数量从 8 → 0

### ST-S2-B-04.4 重写 3 个 consultation 相关组件（0.125d）

### ST-S2-B-04.5 删除原型 4 个手写 hook（0.125d）⚠️ V10 收益

---

## T-B-05 · audit/upload 端点（V10 重写）（1.0d · 4 子任务）

### ST-S2-B-05.1 写 `useAuditQuery`（0.125d）
### ST-S2-B-05.2 写 `useAuditSubmitMutation`（0.25d）
### ST-S2-B-05.3 写 `useUploadMutation`（0.5d）
- **封装**：`multipart/form-data` 上传 + 进度回调
- **V10 变化**：用 TanStack Query 替代手写 fetch + AbortController

### ST-S2-B-05.4 删除原型最后 2 个手写 hook（0.125d）⚠️ V10 收益

---

## T-B-06 · Chromatic 视觉基线（V10 新增 · 0.5d · 3 子任务）⚠️ V10 关键

> **PM 决策（2026-07-03）**：Playwright 视觉回归 + Chromatic

### ST-S2-B-06.1 接入 Chromatic CLI（0.125d）
```bash
pnpm --filter web add -D chromatic
```

### ST-S2-B-06.2 截图 8 个核心页面（0.25d）
- **页面**：Home / Plan Detail / Chat / Form / Share / Review / Settings / Admin

### ST-S2-B-06.3 提交基线 + 接入 CI（0.125d）
- **产出**：`pnpm chromatic` 提交基线
- **CI**：`.github/workflows/web-ci.yml` 添加 chromatic 步骤

---

## T-B-07 · Vite build + bundle 体积验证（0.5d · 4 子任务）⚠️ V10 新增

> **V10 关键**：从 Next.js 切到 Vite，必须验证 bundle 体积和构建时间

### ST-S2-B-07.1 写 `vite.config.ts`（0.125d）
- **配置**：手动 chunk split（vendor / ui / pages）+ 资源内联阈值

### ST-S2-B-07.2 bundle 分析（0.125d）
- **命令**：`pnpm build -- --analyze`
- **验收**：
  - [ ] vendor < 200KB gzip
  - [ ] 业务代码 < 100KB gzip
  - [ ] 总 bundle < 300KB gzip

### ST-S2-B-07.3 构建时间验证（0.125d）
- **验收**：
  - [ ] `pnpm build` < 30s

### ST-S2-B-07.4 接入 turbo build（0.125d）
- **验收**：
  - [ ] `turbo run build` 全 monorepo < 60s

---

## V10 验收清单（Sprint 2 G1 闸门）

```
G1 闸门（必须全部通过）：
  [ ] pnpm install 0 error
  [ ] pnpm typecheck 0 error 0 any
  [ ] pnpm lint 0 error 0 warning（V10 重写后归零）
  [ ] pnpm test 100% 覆盖 ModeIndicator / SafeMarkdown / FormCard
  [ ] pnpm test:e2e 3 spec 全绿
  [ ] pnpm build bundle < 300KB gzip
  [ ] pnpm chromatic 视觉基线 8 页全提交
  [ ] OpenAPI codegen 0 any
  [ ] 原型 7 个手写 hook 全部删除
  [ ] ESLint 33 any + 16 unused 全部归零
```

---

## V10 风险（Sprint 2 特有）

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| V10-S2-R1 | Vite 切框架导致 Next.js 特有能力（i18n routing）失效 | 中 | Sprint 4 处理（i18n 用自写 router） |
| V10-S2-R2 | Zustand persist 与 SSR 冲突 | 低 | 用 `createJSONStorage(() => localStorage)` + 客户端守卫 |
| V10-S2-R3 | TanStack Query 5 与 React 19 兼容性 | 低 | 锁定 5.59.x 稳定版 |
| V10-S2-R4 | RHF + Zod 类型推导慢 | 低 | 用 `z.infer<typeof Schema>` 而非泛型 |

---

## V10 与后续 Sprint 衔接

- **Sprint 3** 直接基于 Sprint 2 的 Zustand store + TanStack Query 开发 5 个新模块
- **Sprint 4** 性能优化基线：Vite build 产物 + Chromatic diff 阈值
- **Sprint 5-8** 全部使用 RHF + Zod + Zustand 模式

---

**Sprint 2 文档状态**：V10 选项 B 重写完成，待启动
**总工时**：9.5 人天（V2 是 18 人天，节省 8.5d）
**总子任务**：56 个（V2 是 58 个）
**下一步**：PM 确认后启动 T-A-14
