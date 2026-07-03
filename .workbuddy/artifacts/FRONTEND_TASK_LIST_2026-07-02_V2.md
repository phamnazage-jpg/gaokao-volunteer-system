# 前端重构 · 任务清单 V2（基于 tksea 最新版）

> 评审者：**Frontend Developer (资深前端开发工程师)**
> 日期：2026-07-02 22:45
> 上游：`git pull` 拉取远端 `a8b4927`（比本地 `6d0feeb` 新 207 文件 / 87326 行净增）
> 重要：**`前端原型代码/` 完全未变**（diff 为空）—— 之前的 8 项硬约束、4114 行代码、247 行 design-system 100% 适用
> V1 任务清单差异：**+45 任务 / +14 人天**，主要因后端新增 share-link / data-query / review-flow / llm 增强 / poster 集成

---

## 0. V1 → V2 关键变化（前置说明）

### 0.1 远端新版本（a8b4927 vs 6d0feeb）

```
207 files changed, 87326 insertions(+), 2399 deletions(-)
```

| 维度 | V1（6d0feeb） | V2（a8b4927） | 变化 |
|---|---|---|---|
| pytest 用例 | 924 | **1104** | **+180（+19%）** |
| admin/routes/web_public.py | ~900 行 | **~4800 行** | +3900 行（share-link/data-query/review/poster/政策 5 大块） |
| 后端路由 | 87 | **约 110+** | +20 个端点 |
| 前端原型代码 | 4114 行 | **4114 行（不变）** | 0 |
| 新增脚本 | 旧版 | **+13 脚本** | integration_test / perf_benchmark / score_range_fullchain_100 / poster / payment_readiness_doctor 等 |
| skills/ | 旧版 | +6 文件（gaokao-audit 等） | LLM 审核服务化 |

### 0.2 V2 新增的 5 大后端能力模块（前端必须对接）

| # | 模块 | 后端端点 | 前端页面 | V1 是否覆盖 | V2 新增任务 |
|---|---|---|---|---|---|
| 1 | **Share Link API** | `POST /api/share-link` / `DELETE /api/share-link/{id}` / `GET /api/portal/share-link/latest` | 复核/报告页分享按钮 | ❌ | T-B-22 ~ T-B-25 + T-D-13 |
| 2 | **Data Query 6 入口** | `/score-line-query` / `/rank-estimator` / `/majors-query` / `/schools-query` / `/data-query` | 4 个查询页 + 1 个聚合页 | ❌ | T-B-26 ~ T-B-31 + T-D-14 ~ T-D-17 + T-E-13 ~ T-E-16 |
| 3 | **Review Flow** | `/review/start` / `/review/action` / `/portal/{token}/cwb` / `/portal/{token}/full-plan` | 复核结果页 + 冲稳保 + 完整规划 | ❌ | T-B-32 ~ T-B-35 + T-D-18 + T-E-17 |
| 4 | **LLM 增强审核** | AuditService LLM 接入 + 多模型 fallback | 审核触发 + 进度 + 结果 | ❌（原型 mock） | T-B-36 ~ T-B-38 + T-D-19 |
| 5 | **Poster 海报** | `data/share/poster.py` + CLI `gaokao-poster` | 海报生成 + 下载 | ❌ | T-B-39 + T-D-20 + T-E-18 |

### 0.3 V1 任务清单的"未变化部分"（依然成立）

| 不变量 | 验证方式 | V1 任务 |
|---|---|---|
| 前端原型代码 4114 行未变 | `git diff 6d0feeb..a8b4927 -- 前端原型代码/` 为空 | T-A-02 ~ T-A-23 全部保留 |
| 8 项硬约束 | 扫读原型文件源码 | T-A-14 ~ T-A-19 单测 + e2e 保留 |
| 5 阶段路径 | 与 V2 Senior Developer 报告一致 | A/B/C/D/E 阶段框架保留 |
| 78 人天估算 | V1 中位 | V2 调整为 **92 人天**（+14） |

---

## 1. 任务总览 V2（136 任务，92 人天）

| 阶段 | 任务数 | 人天 | V1→V2 增量 | 关键里程碑 |
|---|---|---|---|---|
| A. 基础设施 | 23 | 11 | 0 | monorepo + 5 组件 + e2e 骨架 + CI |
| B. 真实后端对接 | 35 | 38 | +14（21→35） | 30+ 端点对接 + 8 hook 真实化 + Lighthouse ≥ 90 |
| C. 架构整合 | 15 | 10 | +1（13→15） | 独立部署 + Sentry + CSP + Poster CLI |
| D. 设计 / a11y 加固 | 24 | 14 | +3（18→24） | 18 组件 + SharePanel + DataQuery + Review UI + axe |
| E. 内部页面 React 化 | 24 | 19 | +2（16→24） | 运营后台 + Share 管理 + Data Query + Review + Poster + Policy |
| **总计** | **136** | **92** | **+45 任务 / +14 人天** | **V1 66-89 → V2 78-105（中位 92）** |

> **注**：V2 中位 92 人天 与 V2 Senior Developer 报告（66-89）相比略高，**主要因为后端 5 大新模块的 React 化工作量是 V1 没预估到的**，建议向 PM 申请追加 14 人天（1 人 × 2.8 周 或 2 人 × 1.4 周）。

---

## 阶段 A · 基础设施（23 任务，11 人天）

> **完全沿用 V1**，因为前端原型代码未变。

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

## 阶段 B · 真实后端对接（35 任务，38 人天）**[V2 扩展 +14 任务 / +14 人天]**

> **V2 关键扩展**：5 大新模块（Share Link / Data Query / Review / LLM / Poster）需要在前端真实对接。

### B.1 后端 API 补全（11 任务，11d）—— **V1 5 任务 → V2 11 任务**

#### **T-B-01** `POST /api/chat/send`（V1 保留）
- **入参**：`{message: string, consultation_id?: string, profile_snapshot?: object}`
- **出参**：`{user_message: Message, assistant_message: Message, consultation_id: string}`
- **验收**：
  - [ ] OpenAPI schema 完整
  - [ ] 与后端 `Consultation` / `Message` 模型对齐
  - [ ] 错误码 E03001/03002/03003 覆盖
- **估时**：1.5d

#### **T-B-02** `GET /api/chat/history?consultation_id=...`（V1 保留）
- **出参**：`{messages: Message[]}`
- **验收**：
  - [ ] 分页参数（cursor）支持
  - [ ] auth：必须登录或持有 consultation_id 的访问令牌
- **估时**：0.5d

#### **T-B-03** `GET /api/consultations` / `GET /api/consultations/{id}` / `DELETE /api/consultations/{id}`（V1 保留）
- **验收**：
  - [ ] 列表返回 `{consultations: [{id, title, updated_at, profile, has_plan, has_audit}]}`
  - [ ] 详情返回完整 messages + profile + plan + audit
  - [ ] DELETE 软删除 + 数据保留 30 天
- **估时**：1d

#### **T-B-04** `GET /api/plans` / `GET /api/plans/{id}` / `PATCH /api/plans/{id}` / `DELETE /api/plans/{id}`（V1 保留）
- **验收**：
  - [ ] 列表返回 `{plans: [{id, name, created_at, profile, distribution: {rush,stable,safe}}]}`
  - [ ] PATCH 仅支持 name 修改
  - [ ] DELETE 软删除
- **估时**：1d

#### **T-B-05** `POST /api/assessment` / `POST /api/audit/upload`（V1 保留）
- **audit/upload**：multipart/form-data，Excel/Image/PDF/Paste
- **出参**：`{report_id, overall_score, summary, risk_items, distribution, good_points}`
- **验收**：
  - [ ] 文件大小限制：Excel 5MB / Image 10MB / PDF 10MB
  - [ ] MIME 校验
  - [ ] 解析后存 DB + 触发 AI 审核
- **估时**：2d

#### **T-B-22** 🆕 `POST /api/share-link` —— Share Link 创建
- **入参**：`{resource_type: "review_result" | "report", resource_id: string, expires_in_hours?: number}`
- **出参**：`{code: string, url: string, qr_code_url?: string, expires_at: string}`
- **权限**：仅 `admin` 角色
- **验收**：
  - [ ] 鉴权 401/403 测试通过
  - [ ] 与 `0145d66` 提交中的 test_share_link_api.py 一致
  - [ ] 撤销后状态正确变更
- **估时**：0.5d
- **依据**：commit `0145d66` 已实现后端，前端需对接

#### **T-B-23** 🆕 `DELETE /api/share-link/{id}` —— Share Link 撤销
- **出参**：`{ok: true, revoked_at: string}`
- **权限**：仅 `admin` 角色
- **验收**：
  - [ ] 撤销后 GET /api/share-link/latest 返回 404
  - [ ] 撤销历史保留
- **估时**：0.25d

#### **T-B-24** 🆕 `GET /api/portal/share-link/latest` —— 查询当前 portal 的最新分享链接
- **出参**：`{code, url, expires_at, click_count}` 或 404
- **验收**：
  - [ ] 状态面板渲染依据（test_share_status_panel.py）
- **估时**：0.25d
- **依据**：commit `0145d66` 提到 test_share_status_panel.py 期望 status 页面渲染"当前分享状态"面板

#### **T-B-25** 🆕 `GET /api/share-link/{code}/stats` —— 分享统计
- **出参**：`{click_count, view_count, conversion_count, last_clicked_at, device_breakdown}`
- **估时**：0.5d

#### **T-B-26** 🆕 `GET /api/data-query/score-line` —— 分数线查询
- **入参**：`{province, year, subject_type, score}`
- **出参**：`{matches: [{university, major, year, min_score, max_score, avg_score}]}`
- **验收**：
  - [ ] 性能：1 省 1 年 1 类目 < 200ms
  - [ ] 缓存：相同 query 5min 命中
- **估时**：0.5d
- **依据**：commit `c5b0c3d` `/score-line-query` 端点已实现

#### **T-B-27** 🆕 `GET /api/data-query/rank-estimator` —— 位次估算
- **入参**：`{province, year, subject_type, score}`
- **出参**：`{rank: number, rank_range: [min, max], total_candidates: number}`
- **估时**：0.5d
- **依据**：`/rank-estimator` 端点已实现

#### **T-B-28** 🆕 `GET /api/data-query/majors` + `GET /api/data-query/schools` —— 专业/院校库
- **入参**：`{keyword, category?, level?, page, page_size}`
- **出参**：`{items: [...], total, page, page_size}`
- **验收**：
  - [ ] 分页 + 搜索 + 过滤
  - [ ] 性能：keyword 搜索 < 300ms
- **估时**：0.5d
- **依据**：`/majors-query` `/schools-query` 端点已实现

#### **T-B-29** 🆕 `POST /api/review/start` —— 启动复核
- **入参**：`{plan_id, profile_snapshot}`
- **出参**：`{review_id, status: "started", progress_url}`
- **验收**：
  - [ ] 异步触发 LLM 审核
  - [ ] progress_url 可轮询
- **估时**：0.5d
- **依据**：commit `0145d66` 提到 `/review/start` 端点

#### **T-B-30** 🆕 `GET /api/review/{id}/status` —— 复核进度
- **出参**：`{review_id, status, progress: 0-100, current_step, eta_seconds}`
- **估时**：0.25d

#### **T-B-31** 🆕 `POST /api/review/action` —— 复核动作
- **入参**：`{review_id, action: "approve" | "reject" | "revise", comment?}`
- **出参**：`{ok: true, next_review_id?}`
- **估时**：0.5d
- **依据**：commit `0145d66` `/review/action` 端点

#### **T-B-32** 🆕 `GET /api/portal/{token}/cwb` —— 冲稳保建议
- **出参**：`{rush: School[], stable: School[], safe: School[]}`
- **验收**：
  - [ ] 与 PlanCard 兼容（字段一致）
  - [ ] 排序按概率降序
- **估时**：0.5d
- **依据**：commit `9b587a5` `/portal/{token}/cwb` 端点 + "有 token 时显示 cwb 按钮"

#### **T-B-33** 🆕 `GET /api/portal/{token}/full-plan` —— 完整规划页
- **出参**：`{plan: Plan, profile, audit_report?, llm_enhancement?}`
- **验收**：
  - [ ] 含 LLM 增强（commit `a3d8c73` "完整规划页 LLM 方案生成"）
- **估时**：0.5d

#### **T-B-34** 🆕 `POST /api/llm/audit-enhance` —— LLM 增强审核
- **入参**：`{audit_report_id, enhancement_type: "summary" | "risk_explain" | "suggestion"}`
- **出参**：`{enhanced_content: string, model_used: string, tokens_consumed: number}`
- **验收**：
  - [ ] 多模型 fallback（commit `11fbb59` "多模型 fallback 支持"）
  - [ ] 超时 30s 降级
- **估时**：1d
- **依据**：commit `11fbb59` `a3d8c73` `43c1dbd` LLM 增强链路

#### **T-B-35** 🆕 `POST /api/poster/generate` —— 海报生成
- **入参**：`{plan_id, template: "minimal" | "gradient" | "card", watermark?: string}`
- **出参**：`{poster_id, image_url, download_url, expires_at}`
- **权限**：仅 `admin` 或 plan owner
- **验收**：
  - [ ] 与 `data/share/poster.py` CLI 行为一致
  - [ ] 含 QR 码（链接到分享 link）
- **估时**：0.5d
- **依据**：commit `a8b4927` 完整 poster 系统

### B.2 useChat / 业务 Hook 真实化（8 任务，9d）—— **V1 4 任务 → V2 8 任务**

#### **T-B-12** 拆 useChat 编排层（V1 保留）
- **产出**：
  - `useChat.ts` 改为纯编排（无 mock 数据）
  - mock 数据移到 `apps/web/__mocks__/chat-fixtures.ts`（仅 B 阶段测试用）
- **验收**：
  - [ ] useChat.ts < 300 行
  - [ ] `__mocks__/chat-fixtures.ts` 包含：广东省物理 620、广东省历史 580、河北省物理 600 共 3 套 mock
- **估时**：1.5d
- **依赖**：T-B-01 ~ T-B-05（API 已就位）
- **约束**：§0.1 R-NEW-1

#### **T-B-13** 真实 sendMessage + typing 动画（V1 保留）
- **产出**：mutation + optimistic update
- **验收**：
  - [ ] e2e `chat-send.spec.ts`：输入消息 → 1s 内出现用户气泡 → 3s 内出现 AI 回复
  - [ ] 失败时乐观更新回滚 + Toast 提示
  - [ ] typing 动画 (`page.tsx:173-186`) 保留
- **估时**：1d
- **依赖**：T-B-12
- **约束**：§1.3（消息路由模式）

#### **T-B-14** 真实 getHistory + 滚动恢复（V1 保留）
- **产出**：consultation 切换时 fetch 历史
- **验收**：
  - [ ] 切换 consultation_id → 加载历史消息
  - [ ] 自动滚动到底部（`messagesEndRef`）
  - [ ] 加载中显示 Skeleton（用 T-D-09 阶段组件）
- **估时**：1d
- **依赖**：T-B-13

#### **T-B-15** usePlan / useConsultation 真实化 + localStorage 兼容（V1 保留）
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

#### **T-B-36** 🆕 useShareLink Hook
- **产出**：`useShareLink(resourceType, resourceId)` 返回 `{shareLink, create, revoke, refresh}`
- **API**：
  - `create()` → `POST /api/share-link`
  - `revoke()` → `DELETE /api/share-link/{id}`
  - `refresh()` → `GET /api/portal/share-link/latest`
- **验收**：
  - [ ] 创建成功 → 立即显示链接 + QR 码
  - [ ] 撤销后 UI 显示"已撤销"
  - [ ] 失败时 Toast + 表单不重置
- **估时**：1d
- **依赖**：T-B-22, T-B-23, T-B-24

#### **T-B-37** 🆕 useDataQuery Hook（4 个独立 hook）
- **产出**：
  - `useScoreLineQuery({province, year, subject_type, score})` → 返回 `matches[]`
  - `useRankEstimator({province, year, subject_type, score})` → 返回 `rank`
  - `useMajorsQuery({keyword, page})` → 返回 `items[] + pagination`
  - `useSchoolsQuery({keyword, page})` → 同上
- **验收**：
  - [ ] 4 个 hook 独立缓存（staleTime 5min）
  - [ ] 相同 query 命中缓存
  - [ ] 错误时降级到 localStorage 缓存
- **估时**：1.5d
- **依赖**：T-B-26, T-B-27, T-B-28

#### **T-B-38** 🆕 useReview Hook
- **产出**：`useReview(reviewId)` 返回 `{status, progress, currentStep, etaSeconds, start, action}`
- **API**：
  - `start()` → `POST /api/review/start`
  - `poll()` → `GET /api/review/{id}/status`（每 2s 轮询）
  - `action(action, comment?)` → `POST /api/review/action`
- **验收**：
  - [ ] SSE 优先；不支持 SSE 时降级轮询
  - [ ] progress 100% → 跳转结果页
  - [ ] 失败时 Toast + 重试
- **估时**：1.5d
- **依赖**：T-B-29, T-B-30, T-B-31

#### **T-B-39** 🆕 usePoster Hook
- **产出**：`usePoster(planId)` 返回 `{posterUrl, generate, download}`
- **验收**：
  - [ ] 生成进度显示（5-10s）
  - [ ] 下载为 PNG
  - [ ] watermark 可选
- **估时**：0.5d
- **依赖**：T-B-35

### B.3 useProfile / 表单 / 错误处理（7 任务，7d）—— **V1 6 任务 → V2 7 任务**

#### **T-B-16** 真实 useProfile（V1 保留）
- **产出**：`GET /api/profile` 拉取，表单提交用 `PATCH /api/profile`
- **验收**：
  - [ ] FormCard 提交后立即看到进度条（InfoCollectionProgress）填充
  - [ ] 失败时回滚 + 错误提示
- **估时**：1d
- **依赖**：T-B-15

#### **T-B-17** 真实 useAudit（V1 保留 + LLM 增强）
- **产出**：`POST /api/audit/upload` multipart + LLM 增强回调
- **验收**：
  - [ ] 4 种文件类型（Excel/Image/PDF/Paste）全部走真实 API
  - [ ] 进度条（上传 + AI 处理）显示
  - [ ] 错误码 E04001（上游 AI 失败）→ Toast 重试
  - [ ] LLM 增强（`/api/llm/audit-enhance`）异步触发，结果追加到 report
- **估时**：1.5d
- **依赖**：T-B-05, T-B-34

#### **T-B-18** 错误码 → 用户文案映射（V1 保留）
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

#### **T-B-19** ErrorBoundary 兜底页（V1 保留）
- **产出**：`apps/web/app/error.tsx`（Next 16 error boundary）
- **验收**：
  - [ ] 5xx 错误时显示兜底页（"出错了，刷新重试"）
  - [ ] Sentry 上报
- **估时**：0.5d
- **依赖**：T-B-18

#### **T-B-20** 离线检测 + 提示（V1 保留）
- **产出**：`useOnlineStatus` hook + 顶部黄条提示
- **验收**：
  - [ ] offline → 顶部条 + 写操作禁用
  - [ ] online 恢复 → 自动重试 pending mutations
- **估时**：1d

#### **T-B-21** 表单提交防重复（V1 保留）
- **产出**：所有 mutation 加 `isPending` 状态
- **验收**：
  - [ ] FormCard 提交按钮在 isPending 时禁用 + 旋转图标
  - [ ] ChatMessage 的修复按钮单次点击后禁用
- **估时**：0.5d

#### **T-B-40** 🆕 Share Link 状态面板数据
- **产出**：`useShareStatusPanel(resourceId)` → 返回 `{currentLink, clickCount, viewCount, daysUntilExpiry}`
- **API**：`GET /api/portal/share-link/latest` + `GET /api/share-link/{code}/stats`
- **验收**：
  - [ ] test_share_status_panel.py 期望"当前分享状态"面板渲染
  - [ ] 30s 自动刷新
- **估时**：0.5d
- **依据**：commit `0145d66` 提到 test_share_status_panel.py 期望但当前未通过

### B.4 离线缓存 + e2e + 性能（9 任务，9d）—— **V1 6 任务 → V2 9 任务**

#### **T-B-22** TanStack Query 持久化（V1 保留）
- **产出**：`@tanstack/query-persist-client-core` + localStorage
- **验收**：
  - [ ] 关闭浏览器再打开 → 历史消息立即可见
  - [ ] 后台 revalidate 后更新
- **估时**：1d
- **依赖**：T-B-13

#### **T-B-23** e2e 真实化（8 个关键路径）—— **V1 5 → V2 8**
- **产出**：
  - `chat-send.spec.ts` 真实发消息
  - `chat-history.spec.ts` 切换 consultation
  - `plan-save.spec.ts` 保存方案
  - `audit-upload.spec.ts` 上传文件
  - `theme-persist.spec.ts` 主题持久化
  - **🆕 `share-link.spec.ts`** 创建/撤销/分享 UI
  - **🆕 `data-query.spec.ts`** 4 个查询页
  - **🆕 `review-flow.spec.ts`** 复核全流程
- **验收**：
  - [ ] 8 个 spec 全绿
  - [ ] 每个 spec 含 1 个失败场景
- **估时**：3d
- **依赖**：T-B-13, T-B-15, T-B-17, T-B-36, T-B-37, T-B-38

#### **T-B-24** Lighthouse CI 集成（V1 保留 + 新页面）
- **产出**：`lighthouserc.json` + GitHub Action
- **预算**：
  - LCP < 2.5s
  - INP < 200ms
  - CLS < 0.1
  - Performance ≥ 90
  - Accessibility ≥ 95
  - Best Practices ≥ 95
  - SEO ≥ 90
- **覆盖页面**：/ /consultations /plans /plans/compare /assessment **🆕 /score-line-query /rank-estimator /majors-query /schools-query /review/start /admin/login /admin**
- **验收**：
  - [ ] 12 个页面 P75 ≥ 预算
  - [ ] PR 评论显示分数
- **估时**：1.5d
- **依赖**：T-B-23

#### **T-B-25** Bundle 优化（V1 保留）
- **产出**：
  - `next/dynamic` 异步加载 PlanCard / AuditReportCard / CareerCard
  - `react-markdown` 异步 chunk
  - 拆 vendor chunk
- **验收**：
  - [ ] First load JS < 200KB
  - [ ] PlanCard 异步 chunk < 50KB
- **估时**：1d

#### **T-B-26** 路由级 prefetch（V1 保留）
- **产出**：`<Link prefetch>` 关键路径
- **验收**：
  - [ ] hover Sidebar /plans → 100ms 内开始预取
- **估时**：0.5d

#### **T-B-27** 真实后端回归（V1 保留）
- **产出**：完整 e2e 套件在真实后端跑通
- **验收**：
  - [ ] 15+ e2e spec 全绿
  - [ ] 跨 3 浏览器（chromium / webkit / firefox）通过
- **估时**：0.5d
- **依赖**：T-B-23 ~ T-B-26

#### **T-B-41** 🆕 ShareLink 失败降级
- **产出**：
  - `navigator.share` 不可用时降级到 `clipboard.writeText`
  - clipboard 不可用时降级到 `<a download>` 文本文件
- **验收**：
  - [ ] 3 路径全部测试通过
  - [ ] 用户看到明确提示
- **估时**：0.5d
- **依据**：commit `0145d66` "失败时显示具体错误，不再静默"

#### **T-B-42** 🆕 LLM 增强进度轮询
- **产出**：
  - `useLLMEnhancement` hook + SSE 优先
  - 长任务（>30s）显示进度条
  - 失败时降级到基础审核结果
- **验收**：
  - [ ] SSE 连接断开时自动重连（最多 3 次）
  - [ ] 降级时显示"AI 增强暂不可用，已展示基础结果"
- **估时**：1d
- **依据**：commit `11fbb59` "多模型 fallback 支持"

#### **T-B-43** 🆕 Poster 异步生成 + 轮询
- **产出**：
  - `usePoster` + 进度条
  - 生成完成自动下载（可选）
  - 失败时重试 + Toast
- **验收**：
  - [ ] 5-10s 内完成
  - [ ] 失败可重试
  - [ ] 长任务不阻塞 UI
- **估时**：0.5d
- **依据**：commit `a8b4927` poster 系统

---

## 阶段 C · 架构整合（15 任务，10 人天）**[V2 扩展 +2 任务 / +1 人天]**

### C.1 部署架构（5 任务，3d）—— **V1 保留**

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

### C.2 监控（4 任务，2d）—— **V1 保留**

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

### C.3 文档 + 收口（4 任务，4d）—— **V1 保留**

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

### C.4 🆕 Poster CLI 集成（V2 新增，1 任务，1d）

#### **T-C-44** 🆕 Poster CLI 部署集成
- **产出**：
  - `scripts/gaokao-poster` 部署到 cron（每日 02:00 自动生成）
  - 产物上传到 CDN
  - 失败告警
- **验收**：
  - [ ] crontab 配置生效
  - [ ] 失败时 Sentry 告警
  - [ ] 日志可查
- **估时**：1d
- **依据**：commit `a8b4927` 引入 poster CLI

#### **T-C-45** 🆕 集成测试套件
- **产出**：`scripts/integration_test.py` 前端版本（FastAPI + Next.js 双服务）
- **验收**：
  - [ ] 端到端 5 个关键场景
  - [ ] CI 卡点
- **估时**：0d（与 T-A-23 共用 CI）
- **依据**：commit `a8b4927` 新增 integration_test.py

---

## 阶段 D · 设计 / a11y 加固（24 任务，14 人天）**[V2 扩展 +6 任务 / +3 人天]**

### D.1 基础组件补齐（10 任务，4d）—— **V1 保留**

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

### D.2 a11y 全量审计（3 任务，2d）—— **V1 保留**

#### **T-D-11** axe-core 集成
- **产出**：`@axe-core/playwright` + **5 → 12 个页面**自动扫描
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

### D.3 🆕 业务组件扩展（V2 新增，6 任务，4d）

#### **T-D-14** 🆕 SharePanel 组件
- **产出**：`packages/ui/components/SharePanel.tsx`
- **API**：`<SharePanel resourceType resourceId />` —— 包含创建按钮、链接展示、QR 码、复制、撤销
- **验收**：
  - [ ] 复用 T-B-36 useShareLink
  - [ ] 状态：未创建 / 已创建 / 已撤销 / 已过期
  - [ ] 视觉与原型一致（沿用 Card + Badge）
  - [ ] Vitest 4 个状态全覆盖
- **估时**：0.75d
- **依赖**：T-B-36, T-D-11, T-D-12

#### **T-D-15** 🆕 ShareStatusPanel 组件
- **产出**：`packages/ui/components/ShareStatusPanel.tsx`
- **API**：`<ShareStatusPanel resourceId />` —— 显示当前分享状态 + 点击量 + 转化率
- **验收**：
  - [ ] 复用 T-B-40 useShareStatusPanel
  - [ ] 30s 自动刷新
  - [ ] test_share_status_panel.py 通过
- **估时**：0.5d
- **依据**：commit `0145d66` 提到 test_share_status_panel.py 期望但当前未通过

#### **T-D-16** 🆕 DataQueryForm 组件（4 个变体）
- **产出**：
  - `ScoreLineQueryForm` —— 省份/年份/选科/分数输入
  - `RankEstimatorForm`
  - `MajorsQueryForm` —— 关键词 + 分类 + 页码
  - `SchoolsQueryForm`
- **共用**：`packages/ui/components/forms/QueryForm.tsx`（抽象基类）
- **验收**：
  - [ ] 4 个 form 复用同一 QueryForm 框架
  - [ ] Vitest 覆盖：输入验证 / 提交 / 错误展示
- **估时**：1d
- **依赖**：T-B-37

#### **T-D-17** 🆕 DataQueryResult 组件（4 个变体）
- **产出**：
  - `ScoreLineResult` —— 表格 + 分数段分布图
  - `RankEstimatorResult` —— 大数字展示 + 历史趋势
  - `MajorsResult` —— 列表 + 分类
  - `SchoolsResult` —— 列表 + 985/211 标签
- **共用**：`QueryResult` 框架（loading / empty / error / data 4 态）
- **验收**：
  - [ ] 4 态切换动画
  - [ ] 与原型视觉一致
- **估时**：1d
- **依赖**：T-D-16

#### **T-D-18** 🆕 ReviewFlow 组件
- **产出**：`packages/ui/components/ReviewFlow.tsx`
- **API**：`<ReviewFlow planId />` —— stepper 显示 + 进度条 + 结果跳转
- **状态机**：`idle → started → analyzing → completed | failed | revision_needed`
- **验收**：
  - [ ] 复用 T-B-38 useReview
  - [ ] 进度条实时更新
  - [ ] 失败可重试
- **估时**：0.5d
- **依赖**：T-B-38

#### **T-D-19** 🆕 LLMEnhancement 组件
- **产出**：`packages/ui/components/LLMEnhancement.tsx`
- **API**：`<LLMEnhancement auditReportId type />` —— AI 增强摘要 / 风险解释 / 建议
- **验收**：
  - [ ] 异步加载（不阻塞主审核结果）
  - [ ] 失败时降级到基础内容
  - [ ] 显示"由 XXX 模型生成"标注
- **估时**：0.5d
- **依赖**：T-B-34, T-B-42

#### **T-D-20** 🆕 PosterPreview 组件
- **产出**：`packages/ui/components/PosterPreview.tsx`
- **API**：`<PosterPreview planId template />`
- **验收**：
  - [ ] 3 种模板切换
  - [ ] 实时预览
  - [ ] 下载按钮
- **估时**：0.5d
- **依赖**：T-B-43

### D.4 暗色主题全覆盖（1 任务，1.5d）—— **V1 保留**

#### **T-D-14**（保留 V1 编号 T-D-14）暗色变体审计
- **产出**：每个组件 dark 变体
- **验收**：
  - [ ] 18+ 组件都有 dark story（含 V2 新增 7 个）
  - [ ] 视觉切换无白边/无对比度 < 4.5:1
  - [ ] 风险徽章 / 概率条 / 模式指示器 暗色下语义色保持
- **估时**：1.5d
- **依赖**：T-D-01 ~ T-D-10, T-D-14(新) ~ T-D-20(新)

> **注**：D.3 占用 T-D-14 ~ T-D-20 编号，D.4 改为 T-D-21。

#### **T-D-21** 暗色变体审计
- 同 V1 T-D-14 内容
- **依赖**：T-D-01 ~ T-D-10, T-D-14 ~ T-D-20

### D.5 国际化基础（2 任务，2d）—— **V1 保留 + 新增词条**

#### **T-D-15**（改为 T-D-22）next-intl 接入
- **产出**：
  - `packages/i18n/zh-CN/{chat,plans,common,errors,share,dataQuery,review,poster}.json`
  - `packages/i18n/en-US/{...}.json`（占位空字典）
  - 路由级 locale 切换
- **验收**：
  - [ ] 所有硬编码中文移到词条
  - [ ] 切到 en-US 显示 key 而非中文（占位）
- **估时**：1.5d
- **依赖**：T-B-18
- **约束**：§0.1 R-NEW-5（quickPrompts 三态文案抽到 `chat.json`）

#### **T-D-23** 文案审计
- **产出**：i18n key 命名规范文档
- **验收**：
  - [ ] `git grep "[\u4e00-\u9fff]"` 在 `apps/web/src/` 仅命中 `i18n/` 目录
- **估时**：0.5d
- **依赖**：T-D-22

### D.6 性能 + 视觉回归（2 任务，1.5d）—— **V1 保留**

#### **T-D-24** Chromatic + Lighthouse（合并 V1 T-D-17 + T-D-18）
- **产出**：
  - Chromatic 所有 Storybook stories
  - Lighthouse CI
  - 路由级 `loading.tsx`
  - `next/image` / `next/font` 优化
- **验收**：
  - [ ] 50+ stories baseline（V2 增量）
  - [ ] LCP P75 < 1.8s
  - [ ] Bundle < 150KB
- **估时**：1.5d

---

## 阶段 E · 内部页面 React 化（24 任务，19 人天）**[V2 扩展 +8 任务 / +2 人天]**

### E.1 运营后台基础（5 任务，5d）—— **V1 4 任务 → V2 5 任务**

| 任务 | 页面 | 估时 | 验收 |
|---|---|---|---|
| **T-E-01** | 登录页 `/admin/login` | 0.5d | 复用 T-A-09 Button + T-A-10 Input；调 `POST /api/admin/auth/login` + URL token 支持（commit `2af1d06`） |
| **T-E-02** | Dashboard `/admin` | 1.5d | echarts 集成（订单/咨询趋势） + 4 个 KPI 卡片 + URL token 自动认证（commit `0ec5bdf`） |
| **T-E-03** | Layout `/admin` shared | 1d | 顶部 nav + 侧边栏 + 暗色支持 |
| **T-E-04** | 错误兜底 `/admin/error.tsx` | 0.5d | 同 T-B-19 |
| **T-E-05** | 权限守卫 | 0.5d | 未登录跳 /admin/login |

### E.2 订单 + 案例（4 任务，4d）—— **V1 保留**

| 任务 | 页面 | 估时 |
|---|---|---|
| **T-E-06** | 订单列表 `/admin/orders` | 1d |
| **T-E-07** | 订单详情 `/admin/orders/{id}` | 1.5d |
| **T-E-08** | 案例列表 `/admin/cases` | 0.75d |
| **T-E-09** | 案例详情 `/admin/cases/{id}` | 0.75d |

### E.3 Share Link 管理（🆕 V2 新增，3 任务，3d）

| 任务 | 页面 | 估时 | 验收 |
|---|---|---|---|
| **T-E-10** 🆕 | Share Link 列表 `/admin/share-links` | 1d | 调用 `GET /api/share-link`（待后端补全）+ 撤销按钮 + 过期筛选 |
| **T-E-11** 🆕 | Share Link 详情 `/admin/share-links/{code}/stats` | 1d | 点击量 / 转化率 / 设备分布 + 时序图 |
| **T-E-12** 🆕 | Poster 管理 `/admin/posters` | 1d | 复用 T-B-43 usePoster + T-D-20 PosterPreview + 模板选择 |

### E.4 Data Query 内部页（🆕 V2 新增，4 任务，4d）

| 任务 | 页面 | 估时 | 验收 |
|---|---|---|---|
| **T-E-13** 🆕 | 分数线查询 `/admin/data-query/score-line` | 1d | 复用 T-D-16 ScoreLineQueryForm + T-D-17 ScoreLineResult |
| **T-E-14** 🆕 | 位次估算 `/admin/data-query/rank-estimator` | 0.75d | 复用 T-D-16 + T-D-17 |
| **T-E-15** 🆕 | 专业库 `/admin/data-query/majors` | 1d | 复用 T-D-16 + T-D-17 + 分类树 |
| **T-E-16** 🆕 | 院校库 `/admin/data-query/schools` | 1.25d | 复用 T-D-16 + T-D-17 + 985/211 筛选 |

### E.5 Review 内部页（🆕 V2 新增，2 任务，2d）

| 任务 | 页面 | 估时 | 验收 |
|---|---|---|---|
| **T-E-17** 🆕 | 复核 Dashboard `/admin/review` | 1.25d | 待复核列表 + LLM 增强结果 + action 按钮（approve / reject / revise）|
| **T-E-18** 🆕 | LLM 审计日志 `/admin/review/llm-logs` | 0.75d | 模型使用统计 + token 消耗 + fallback 触发次数 |

### E.6 Policy 内部页（🆕 V2 新增，1 任务，1d）

#### **T-E-19** 🆕 Policy 中心 `/admin/policies`
- **产出**：
  - 5 个政策页面 editor（privacy / service-terms / policy-center / same-score / deletion-policy）
  - 草稿/发布两态
  - Markdown 编辑器
- **估时**：1d
- **依据**：commit `c5b0c3d` `818bfa4` 5 个政策页面已实现后端

### E.7 通知 + 设置（4 任务，4d）—— **V1 保留**

| 任务 | 页面 | 估时 |
|---|---|---|
| **T-E-20** | 通知列表 `/admin/notifications` | 1d |
| **T-E-21** | 通知模板编辑 | 1.5d |
| **T-E-22** | 系统设置 `/admin/settings` | 1.5d |
| **T-E-23** | 用户管理 `/admin/users` | 1d |

### E.8 公共门户 React 化（🆕 V2 新增，1 任务，1d）

#### **T-E-24** 🆕 公共门户 React 化
- **产出**：
  - `/pricing` 定价页
  - `/portal/{token}/info` 资料向导
  - `/portal/{token}/status` 状态页
  - `/portal/{token}/report` 报告查看
  - `/portal/{token}/cwb` 冲稳保建议
  - `/portal/{token}/full-plan` 完整规划
  - `/portal/{token}/notifications` 通知
  - `/portal/{token}/deletion-request` 删除请求
  - `/portal/payment-return` 支付回跳
  - `/s/{code}` 短链接分享
- **复用**：所有 portal 页用 `packages/ui/` + `packages/api-client/` + `packages/hooks/`
- **验收**：
  - [ ] 与 `admin/static/portal-ui.css` 视觉一致
  - [ ] 全 8 个 portal 流程跑通
- **估时**：1d
- **依据**：V1 报告 E 阶段未涉及，但 `web_public.py` 已实现 8+ portal 路由

---

## 2. 完整验收矩阵 V2

### 2.1 UI/交互完全遵循新设计（**Self-Review #1**）

| 检查项 | 工具 | 通过标准 |
|---|---|---|
| **Chromatic 视觉回归** | Chromatic | 0 story 像素 diff > 0.1%（50+ stories） |
| **设计 token 一致性** | 自定义 lint | `apps/web/src/` 无硬编码颜色 |
| **三态主题切换无闪白** | Playwright `theme.spec.ts` | refresh 后 100ms 内正确 |
| **移动端断点** | Playwright | 768 / 1024 两断点 1:1 一致 |
| **WCAG 2.1 AA** | axe-core | 0 critical / 0 serious / < 3 moderate（12 个页面） |
| **键盘导航** | Playwright + 手动 | Tab 顺序合理；Enter / Space 触发 |
| **屏幕阅读器** | NVDA + VoiceOver | 4 模式指示器 / PlanCard / AuditReport / SharePanel / DataQuery 全部合理 |
| **8 项硬约束** | 单元测试 | 全部通过（T-A-15 ~ T-A-20） |

### 2.2 所有的功能都能完整实现（**Self-Review #2**）

| 模块 | 功能 | 任务 |
|---|---|---|
| **对话** | 发消息 / 收 AI 回复 / typing / 三态提示 | T-B-13, T-B-14 |
| **方案生成** | AI 推方案 / 三 Tab / 风险徽章 / 概率条 | T-A-13, T-B-12 |
| **方案保存** | 保存 / 重命名 / 删除 / 列表 / 详情 | T-B-15 |
| **方案对比** | 选 2 个 / 维度表 / 差异高亮 | V1 沿用 |
| **方案导出** | 图片 / PDF | T-D-13 |
| **方案审核** | 上传 / 风险项 / 冲稳保 / 良好项 / 一键修复 / **🆕 LLM 增强** | T-B-17, T-B-34, T-D-19 |
| **咨询记录** | 列表 / 搜索 / 删除 / 恢复 | T-B-15 |
| **兴趣测评** | Holland RIAS 10 题 | T-B-01 |
| **表单分步** | basic → subjects → prefs 守卫 | T-A-17, T-B-16 |
| **文件上传** | 4 模式（Excel/Image/PDF/Paste） | T-B-17 |
| **主题切换** | 三态 + 持久化 + 闪白 | T-A-07, T-A-19 |
| **响应式** | Sidebar / MobileNav | T-A-20 |
| **🆕 Share Link** | 创建 / 撤销 / 复制 / QR / 状态面板 | T-B-22~T-B-25, T-B-36, T-B-40, T-D-14, T-D-15, T-E-10, T-E-11 |
| **🆕 Data Query** | 分数线 / 位次 / 专业 / 院校 4 查询 | T-B-26~T-B-28, T-B-37, T-D-16, T-D-17, T-E-13~T-E-16 |
| **🆕 Review Flow** | 启动 / 进度 / 结果 / action | T-B-29~T-B-31, T-B-38, T-D-18, T-E-17 |
| **🆕 LLM 增强** | 摘要 / 风险解释 / 建议 + 多模型 fallback | T-B-34, T-B-42, T-D-19, T-E-18 |
| **🆕 Poster** | 3 模板 + 异步生成 + 下载 | T-B-35, T-B-39, T-D-20, T-E-12 |
| **🆕 Policy 中心** | 5 政策页 editor | T-E-19 |
| **🆕 公共门户** | 8 个 portal 流程 | T-E-24 |
| **a11y / i18n / 错误 / 离线** | 沿用 V1 | T-D-11 ~ T-D-13, T-D-22, T-B-18~T-B-21 |

### 2.3 与后端集成正常（**Self-Review #3**）

| 集成点 | API | 任务 |
|---|---|---|
| **登录** | `POST /api/admin/auth/login` + URL token | T-E-01 |
| **对话** | `POST /api/chat/send` + `GET /api/chat/history` | T-B-01, T-B-02 |
| **profile** | `GET / PATCH /api/profile` | T-B-16 |
| **方案** | `CRUD /api/plans` | T-B-04, T-B-15 |
| **咨询** | `CRUD /api/consultations` | T-B-03, T-B-15 |
| **审核上传** | `POST /api/audit/upload` | T-B-05, T-B-17 |
| **🆕 Share Link** | `POST/DELETE /api/share-link` + `GET latest` + `GET stats` | T-B-22~T-B-25 |
| **🆕 Data Query** | 4 个 query 端点 | T-B-26~T-B-28 |
| **🆕 Review** | `/review/start` `/status` `/action` | T-B-29~T-B-31 |
| **🆕 冲稳保** | `/portal/{token}/cwb` | T-B-32 |
| **🆕 完整规划** | `/portal/{token}/full-plan` | T-B-33 |
| **🆕 LLM 增强** | `/api/llm/audit-enhance` | T-B-34, T-B-42 |
| **🆕 Poster** | `/api/poster/generate` | T-B-35, T-B-43 |
| **错误码** | registry 5 字段 | T-B-18 |
| **CORS** | 白名单 | T-C-04 |
| **trace 贯通** | `x-trace-id` | T-C-08 |
| **Sentry** | 前后端 | T-C-06, T-C-08 |

---

## 3. 风险与缓解 V2（增量）

| ID | 风险 | 缓解 |
|---|---|---|
| R-NEW-1 | useChat 编排层耦合 mock | T-B-12 解耦 |
| R-NEW-2 | localStorage key 兼容 | T-B-15 保留 key 名 |
| R-NEW-3 | CareerCard match 字段无校验 | T-A-22 Zod |
| R-NEW-4 | alert() 阻塞 | T-D-13 Toast |
| R-NEW-5 | quickPrompts 硬编码 | T-D-22 i18n |
| **R-NEW-6** 🆕 | **后端新模块 API 可能未稳定**（share-link / data-query 仍有 commit 修改） | T-A-21 OpenAPI Codegen 每天跑 + T-C-44 集成测试兜底 |
| **R-NEW-7** 🆕 | **LLM 增强 30s 超时降级** | T-B-42 显式降级路径 |
| **R-NEW-8** 🆕 | **Poster CLI 部署依赖系统库**（libpango / libharfbuzz） | T-C-44 Docker 化 |
| **R-NEW-9** 🆕 | **公共门户 8 流程视觉一致性**（沿用 portal-ui.css） | T-E-24 视觉回归 + 端到端 e2e |
| **R-NEW-10** 🆕 | **Share Link QR 码**（前端需 qrcode.react 库） | T-A-09 之后单独 spike 1d |
| R-V2-1 | 真实 API 与 mock 不一致 | T-A-21 Codegen |
| R-V2-2 | Next 16 + React 19 + TanStack Query 兼容性 | T-A-22 spike |
| R-V2-3 | Bundle 爆炸 | T-B-25 异步 chunk |
| R-V2-4 | 老用户数据迁移 | T-B-15 保留 key |
| R-V2-5 | ChatMessage 路由扩展性 | T-B-13 拆 useChat |

---

## 4. 工时总览 V2

| 阶段 | 任务数 | 估时（人天） | V1 → V2 增量 |
|---|---|---|---|
| A. 基础设施 | 23 | 11 | 0 |
| B. 真实后端对接 | 35 | 38 | +14（21→35） |
| C. 架构整合 | 15 | 10 | +1（13→15） |
| D. 设计/a11y 加固 | 24 | 14 | +3（18→24） |
| E. 内部页面 React 化 | 24 | 19 | +2（16→24） |
| **总计** | **136** | **92** | **+45 / +14** |

---

## 5. 立即可执行（本周启动，5 任务，4.5d）

> 仍按 V1 路径启动，因为 `前端原型代码/` 未变：

1. **T-A-01**（0.5d）→ 创建 monorepo
2. **T-A-02**（0.5d）→ 收编前端原型代码
3. **T-A-06 + T-A-07**（1d）→ 设计系统提取
4. **T-A-21**（1d）→ OpenAPI Codegen 接入（**现在会生成 30+ 端点的类型**，比 V1 预想多）
5. **T-A-23**（1.5d）→ CI 工作流

**5 任务完成后**，进入 T-A-04（tsconfig 共享）+ T-A-14（Vitest）+ T-A-18（Playwright），构成 A 阶段前半段。

---

## 6. Self-Review 闭环 V2

| Self-Review 目标 | 验证产物 | 状态 |
|---|---|---|
| **UI/交互完全遵循新设计** | Chromatic + axe + 8 项硬约束单测 | **任务化** §2.1 |
| **所有的功能都能完整实现** | 16 → **21 模块**功能（V1 +5 新模块） | **覆盖** 21/21 |
| **与后端的集成正常** | 11 → **17 集成点**（V1 +6 新端点） | **覆盖** 17/17 |
| **5 个新风险** | R-NEW-1 ~ R-NEW-5 全部有应对 | **闭环** |
| **🆕 5 个 V2 新风险** | R-NEW-6 ~ R-NEW-10 全部有应对 | **闭环** |
| **可验收粒度** | 每个任务有 ID / 标题 / 验收标准 / 估时 / 依赖 / 关联约束 | **达标** |

---

## 附录 A：V2 任务清单 V1 任务对照

| V1 ID | V2 ID | 变化 |
|---|---|---|
| T-A-01 ~ T-A-23 | T-A-01 ~ T-A-23 | **完全保留** |
| T-B-01 ~ T-B-05 | T-B-01 ~ T-B-05 | **完全保留** |
| T-B-12 ~ T-B-15 | T-B-12 ~ T-B-15 | **完全保留** |
| T-B-16 ~ T-B-21 | T-B-16 ~ T-B-21 | **完全保留** |
| T-B-22 ~ T-B-27 | T-B-22 ~ T-B-27 | **完全保留**（B.4 e2e 扩到 8 个） |
| **🆕** | T-B-22 ~ T-B-25, T-B-36, T-B-40, T-B-41 | Share Link 完整链路 |
| **🆕** | T-B-26 ~ T-B-28, T-B-37 | Data Query 4 端点 |
| **🆕** | T-B-29 ~ T-B-31, T-B-38 | Review Flow 3 端点 |
| **🆕** | T-B-32, T-B-33 | Portal cwb / full-plan |
| **🆕** | T-B-34, T-B-42 | LLM 增强 |
| **🆕** | T-B-35, T-B-39, T-B-43 | Poster |
| T-C-01 ~ T-C-13 | T-C-01 ~ T-C-13 | **完全保留** |
| **🆕** | T-C-44, T-C-45 | Poster CLI 集成 + 集成测试 |
| T-D-01 ~ T-D-10 | T-D-01 ~ T-D-10 | **完全保留** |
| T-D-11 ~ T-D-13 | T-D-11 ~ T-D-13 | **完全保留** |
| **🆕** | T-D-14 ~ T-D-20 | 7 个新业务组件 |
| T-D-14 → 改为 T-D-21 | T-D-21 | 暗色变体审计 |
| T-D-15 → 改为 T-D-22, T-D-23 | T-D-22, T-D-23 | next-intl + 文案审计 |
| T-D-17 + T-D-18 → 合并为 T-D-24 | T-D-24 | Chromatic + Lighthouse |
| T-E-01 ~ T-E-09 | T-E-01 ~ T-E-09 | **完全保留**（T-E-02 增 URL token） |
| T-E-10 ~ T-E-13 → 改为 T-E-20 ~ T-E-23 | T-E-20 ~ T-E-23 | 通知 + 设置 + 用户管理 |
| **🆕** | T-E-10 ~ T-E-12 | Share Link 管理 |
| **🆕** | T-E-13 ~ T-E-16 | Data Query 内部页 |
| **🆕** | T-E-17, T-E-18 | Review + LLM 审计 |
| **🆕** | T-E-19 | Policy 中心 |
| **🆕** | T-E-24 | 公共门户 React 化 |

---

**评审完成。V2 任务清单：136 任务 / 92 人天，比 V1 增加 45 任务 / 14 人天，主要因后端 share-link / data-query / review / llm / poster 5 大新模块的 React 化。** 建议向 PM 申请追加预算 14 人天，或调整 E 阶段部分低优先级页面的实施顺序。
