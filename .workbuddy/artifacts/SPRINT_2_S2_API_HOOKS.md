# Sprint 2 任务拆解（W2-3 · 18 人天 · 58 子任务）

> **主任务**：T-A-14 ~ T-A-22, T-B-01 ~ T-B-05
> **目标**：Vitest/Playwright 骨架 + OpenAPI Codegen + 后端 5 端点对接
> **闸门**：G1（OpenAPI 类型生成无 `any`）

## 0. Sprint 2 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-A-14 | Vitest + RTL + MSW 配置 | 0.5d | 4 |
| T-A-15 | 示范单测：ModeIndicator | 0.25d | 3 |
| T-A-16 | 示范单测：SafeMarkdown | 0.25d | 3 |
| T-A-17 | 示范单测：FormCard | 0.5d | 4 |
| T-A-18 | Playwright 配置 | 0.5d | 3 |
| T-A-19 | 示范 e2e：theme.spec | 0.5d | 3 |
| T-A-20 | 示范 e2e：navigation.spec | 0.5d | 3 |
| T-A-21 | OpenAPI Codegen 接入 | 1.0d | 5 |
| T-A-22 | 示范调用：mock server | 0.5d | 4 |
| T-B-01 | `POST /api/chat/send` | 1.5d | 6 |
| T-B-02 | `GET /api/chat/history` | 0.5d | 4 |
| T-B-03 | 3 个 consultations 端点 | 1.0d | 5 |
| T-B-04 | 4 个 plans 端点 | 1.0d | 5 |
| T-B-05 | assessment + audit/upload | 2.0d | 6 |
| **合计** | **15 任务** | **10.5d + 缓冲 7.5d = 18d** | **58** |

---

## T-A-14 · Vitest + RTL + MSW 配置（0.5d · 4 子任务）

### ST-S2-A-14.1 写 `vitest.config.ts`（0.125d）
- **产出**：`apps/web/vitest.config.ts`（jsdom env + setup 文件 + alias）

### ST-S2-A-14.2 写 `setup.ts`（0.125d）
- **产出**：`@testing-library/jest-dom/vitest` + MSW server 启动/关闭

### ST-S2-A-14.3 写 `renderWithProviders.tsx`（0.125d）
- **产出**：`packages/test-utils/renderWithProviders.tsx`（QueryClient + Theme + Router + Intl）
- **验收**：
  - [ ] `pnpm --filter web test` 跑通

### ST-S2-A-14.4 占位测试验证（0.125d）
- **产出**：`Math.test.ts`（1+1=2）
- **验收**：
  - [ ] 占位测试 1 绿

---

## T-A-15 · 示范单测：ModeIndicator（0.25d · 3 子任务）

### ST-S2-A-15.1 写 4 mode 渲染测试（0.125d）
- **覆盖**：
  - explore: "探索模式"
  - generating: "生成中"
  - auditing: "审核中"
  - adjusting: "调整中"
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
  - `<img src=x onerror=alert(1)>` → onerror 剥
  - `<a href="javascript:alert(1)">` → href sanitize
- **验收**：
  - [ ] 3 注入用例全过

### ST-S2-A-16.2 写正常 markdown 渲染（0.0625d → 0d）
- **覆盖**：h1/ul/code/blockquote 渲染正确

### ST-S2-A-16.3 验证（0.0625d → 0d）

---

## T-A-17 · 示范单测：FormCard（0.5d · 4 子任务）

### ST-S2-A-17.1 字段 touched 显示验证（0.125d）
- **验收**：
  - [ ] 字段未 touch 时不显示错误
  - [ ] touch 后显示错误

### ST-S2-A-17.2 跳步守卫测试（0.125d）
- **验收**：
  - [ ] basic 未完成时点击 subjects 步骤 → 阻止 + 提示

### ST-S2-A-17.3 subjects 数组拼装测试（0.125d）
- **验收**：
  - [ ] 选物理/化学/生物 → 提交时 `subjects: ["physics", "chemistry", "biology"]`

### ST-S2-A-17.4 验证 80% 覆盖（0.125d）
- **命令**：`pnpm test --coverage --testPathPattern=FormCard`

---

## T-A-18 · Playwright 配置（0.5d · 3 子任务）

### ST-S2-A-18.1 写 `playwright.config.ts`（0.25d）
- **产出**：`apps/web/e2e/playwright.config.ts`
  - chromium + webkit
  - viewports: 375 (mobile) / 768 (tablet) / 1280 (desktop)
  - baseURL: http://localhost:3000
- **验收**：
  - [ ] `pnpm --filter web e2e` 启动浏览器

### ST-S2-A-18.2 写 `smoke.spec.ts`（0.125d）
- **验收**：
  - [ ] 访问 `/` 看到 Sidebar

### ST-S2-A-18.3 写 webServer 配置（0.125d）
- **产出**：自动启 `pnpm dev`

---

## T-A-19 · 示范 e2e：theme.spec（0.5d · 3 子任务）

### ST-S2-A-19.1 写 light/dark/system 切换（0.25d）
- **覆盖**：
  - 切到 dark → `data-theme="dark"` 出现
  - 切到 system → `data-theme` 移除
- **验收**：
  - [ ] 3 场景全绿

### ST-S2-A-19.2 写持久化测试（0.125d）
- **覆盖**：
  - 刷新页面后 localStorage 保留选择
- **验收**：
  - [ ] `expect(localStorage.getItem('theme')).toBe('dark')`

### ST-S2-A-19.3 写闪白防护测试（0.125d）
- **覆盖**：
  - `page.waitForLoadState('domcontentloaded')` 在 100ms 内
- **验收**：
  - [ ] DOMContentLoaded → theme 已应用

---

## T-A-20 · 示范 e2e：navigation.spec（0.5d · 3 子任务）

### ST-S2-A-20.1 写桌面导航（0.125d）
- **覆盖**：viewport 1280 → Sidebar 可见，MobileNav 隐藏

### ST-S2-A-20.2 写移动导航（0.125d）
- **覆盖**：viewport 375 → MobileNav 可见，Sidebar 隐藏

### ST-S2-A-20.3 写跳转测试（0.25d）
- **覆盖**：
  - Sidebar /plans → 跳转
  - MobileNav /plans → 跳转
- **验收**：
  - [ ] 4 场景全绿

---

## T-A-21 · OpenAPI Codegen 接入（1.0d · 5 子任务）

### ST-S2-A-21.1 启动后端 OpenAPI（0.125d）
- **命令**：`curl http://localhost:8000/openapi.json > openapi.json`
- **验收**：
  - [ ] 看到 ~30+ 端点（V2 增至 30+）

### ST-S2-A-21.2 写 `codegen.config.ts`（0.25d）
- **产出**：`packages/api-client/codegen.config.ts`
  - schema: openapi.json
  - generator: typescript-fetch
  - output: src/gen

### ST-S2-A-21.3 写 `turbo.json` generate 任务（0.125d）
- **产出**：`generate-api-client` 任务依赖 `^build-admin`
- **验收**：
  - [ ] `pnpm turbo run generate-api-client` 跑通

### ST-S2-A-21.4 跑 codegen 看产物（0.25d）
- **验收**：
  - [ ] `packages/api-client/src/gen/services/` 30+ 服务类
  - [ ] 0 个 `any`（**G1 闸门**）

### ST-S2-A-21.5 写 `packages/api-client/src/index.ts` barrel（0.25d）
- **验收**：
  - [ ] `import { AuthService } from '@gaokao/api-client'` 可用

---

## T-A-22 · 示范调用：mock server（0.5d · 4 子任务）

### ST-S2-A-22.1 写 `apps/web/lib/api/chat.ts`（0.125d）
- **API**：
  ```ts
  export const apiClient = {
    chat: {
      send: (consultationId: string | undefined, body: { message: string }) => Promise<ChatResponse>,
      getHistory: (consultationId: string) => Promise<{ messages: Message[] }>,
    }
  };
  ```

### ST-S2-A-22.2 写 MSW handler（0.125d）
- **产出**：`apps/web/mocks/handlers/chat.ts` 拦截 `/api/chat/send`

### ST-S2-A-22.3 在 `page.tsx` 临时接 apiClient（0.125d）
- **验收**：
  - [ ] 类型管道通（**不替换 useChat**，仅验证）

### ST-S2-A-22.4 写 Zod 校验 match 字段（0.125d）
- **约束**：§0.1 R-NEW-3（`z.number().int().min(1).max(5)`）
- **验收**：
  - [ ] match=6 → Zod 抛错

---

## T-B-01 · `POST /api/chat/send`（1.5d · 6 子任务）

### ST-S2-B-01.1 对接 OpenAPI 类型（0.25d）
- **产出**：`import type { ChatSendRequest, ChatResponse } from '@gaokao/api-client/gen'`

### ST-S2-B-01.2 写 `useChatStore.sendMessage`（0.5d）
- **产出**：`apps/web/stores/chatStore.ts`
- **API**：`sendMessage(consultationId, body)` → 调用 `apiClient.chat.send`
- **验收**：
  - [ ] 401/403 错误码正确捕获

### ST-S2-B-01.3 写错误码 E03001/03002/03003 处理（0.25d）
- **验收**：
  - [ ] 3 错误码 → 对应 Toast 提示

### ST-S2-B-01.4 写单测（0.25d）
- **覆盖**：成功 / 401 / 403 / 500

### ST-S2-B-01.5 写 e2e 草稿（0.125d）
- **产出**：`chat-send.spec.ts`（Sprint 3 完成）

### ST-S2-B-01.6 写 Storybook 故事（0.125d）
- **产出**：`ChatSendButton.stories.ts`

---

## T-B-02 · `GET /api/chat/history`（0.5d · 4 子任务）

### ST-S2-B-02.1 对接 OpenAPI（0.125d）

### ST-S2-B-02.2 写 useQuery（0.125d）
- **验收**：
  - [ ] cursor 分页支持

### ST-S2-B-02.3 写 auth 校验（0.125d）
- **验收**：
  - [ ] consultation_id 无访问令牌 → 401

### ST-S2-B-02.4 写单测（0.125d）

---

## T-B-03 · 3 个 consultations 端点（1.0d · 5 子任务）

### ST-S2-B-03.1 列表（0.25d）
- **出参**：`{consultations: [{id, title, updated_at, profile, has_plan, has_audit}]}`

### ST-S2-B-03.2 详情（0.25d）
- **出参**：完整 messages + profile + plan + audit

### ST-S2-B-03.3 DELETE 软删除（0.25d）
- **验收**：
  - [ ] 数据保留 30 天

### ST-S2-B-03.4 写 useConsultation hook（0.125d）

### ST-S2-B-03.5 写单测（0.125d）

---

## T-B-04 · 4 个 plans 端点（1.0d · 5 子任务）

### ST-S2-B-04.1 列表（0.25d）
- **出参**：`{plans: [{id, name, created_at, profile, distribution: {rush,stable,safe}}]}`

### ST-S2-B-04.2 详情（0.125d）

### ST-S2-B-04.3 PATCH name 修改（0.25d）
- **验收**：
  - [ ] 仅支持 name，其他字段 PATCH 拒绝

### ST-S2-B-04.4 DELETE 软删除（0.25d）

### ST-S2-B-04.5 写单测（0.125d）

---

## T-B-05 · assessment + audit/upload（2.0d · 6 子任务）

### ST-S2-B-05.1 写 `useAssessment` hook（0.25d）
- **API**：`POST /api/assessment`（Holland RIAS）

### ST-S2-B-05.2 写 `useAudit.upload` multipart（0.5d）
- **验收**：
  - [ ] Excel 5MB / Image 10MB / PDF 10MB 限制
  - [ ] MIME 校验

### ST-S2-B-05.3 写上传进度条（0.25d）
- **API**：`XMLHttpRequest` + `progress` 事件

### ST-S2-B-05.4 写 AI 处理进度（0.5d）
- **API**：轮询 `/api/audit/{id}/status`

### ST-S2-B-05.5 错误码 E04001 处理（0.25d）
- **验收**：
  - [ ] 上游 AI 失败 → Toast 重试

### ST-S2-B-05.6 写单测（0.25d）

---

## Sprint 2 收口验收

- [ ] 15 主任务 / 58 子任务全部完成
- [ ] **G1 通过**：OpenAPI 生成 0 个 `any`
- [ ] 测试覆盖率：ModeIndicator/SafeMarkdown/FormCard 100% / 100% / 80%+
- [ ] E2E：theme.spec / navigation.spec 全绿
- [ ] 进入 Sprint 3 前 commit：`<feat(s2): vitest+playwright+openapi+5 endpoints>`
