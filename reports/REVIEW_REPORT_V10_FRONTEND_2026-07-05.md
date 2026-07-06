<!-- 历史快照提示：本文件保留为历史审计材料，不再代表当前项目状态。 -->
> ⚠️ **历史快照（非当前真相源）**：本文件仅保留当时审查/收口结论。当前状态与执行顺序以 `docs/CURRENT_STATE.md`、`docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`、`docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`、`docs/plans/2026-07-05-review-remediation-systemic-fix-plan.md` 和 `reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md` 为准。

---

# V10 前端重构 · 真实状态复核报告

> **审查日期**：2026-07-05  
> **复核更新**：2026-07-05，已纳入 `2194f89 fix: stabilize e2e assertions after i18n migration` 与系统性二次 review  
> **审查范围**：Sprint 1 ~ Sprint 8 前端重构任务  
> **结论**：S1-S7 前端代码已落地，i18n 迁移导致的 14 个 e2e 回归已修复；二次 review 又发现后台导航断链、Admin mock 登录未对接真实 JWT、CI/Lighthouse/Chromatic 配置风险；因此仍不能宣称 V10 全部完成。

---

## 一、当前结论

原始审查发现的主要代码级 blocker 是 Sprint 7 i18n 迁移后 e2e selector 未同步，导致 navigation、data-query、poster、admin mobile/a11y 等用例在多项目矩阵下失败。

该问题已在 `2194f89` 修复：

- e2e 断言改为兼容 i18n 后的可访问名称或结构化 role/cell 定位。
- poster e2e mock 已匹配当前 job/status 生成模型。
- mobile-chrome 下 Admin 布局补齐移动端横向导航，修复真实 UI 缺口。

---

## 二、闸门复验

| 闸门 | 最新复验结果 | 状态 |
|---|---:|---|
| build | `pnpm run build` 通过；main 146.74 KB gzip，total 393.60 KB gzip | ✅ 通过 |
| lint | `pnpm run lint` 通过 | ✅ 通过 |
| typecheck | `pnpm run typecheck` 通过 | ✅ 通过 |
| vitest | 提权后 `pnpm run test` 通过；85 files / 317 tests | ✅ 通过 |
| targeted e2e | data-query + navigation + poster，8/8 passed | ✅ 通过 |
| Chromium e2e | 29/29 passed | ✅ 通过 |
| 非 Firefox e2e 矩阵 | Chromium + WebKit + mobile-chrome，87/87 passed | ✅ 通过 |
| Firefox e2e | 本机 Playwright `browserContext.newPage` 环境异常 | ⏳ 待环境复验 |
| Lighthouse / LHCI | 本机 Chrome 临时目录 EPERM，未复跑 | ⏳ 待 CI 或环境修复 |
| T-B-27 后端 regression | 本轮未复跑，需要真实后端 / pytest 环境 | ⏳ 待环境 |
| T-C-44 Poster Docker | 本机暂无 Docker | ⏳ 待环境 |

---

## 三、系统性二次 Review Findings

### F1 · 后台导航存在真实断链（High）

- `apps/web/src/layouts/AdminLayout.tsx` 暴露 `/admin/review` 导航项。
- `apps/web/src/router.tsx` 的 `/admin` 子路由没有 `review`，只有订单、案例、share-links、posters、score-lines、rank-estimator、majors、schools、error 等子路由。
- 确定性脚本校验结果：`missing admin nav routes: /admin/review`。
- 影响：后台用户点击“复核 / Review”会进入后台 NotFound，而不是复核页面。
- 测试缺口：现有 `admin-portal.spec.ts` 只覆盖登录、订单、案例、错误页，没有遍历全部后台导航链接。

### F2 · React Admin 登录仍是前端 mock（High）

- `apps/web/src/pages/admin/LoginPage.tsx` 只接受验证码 `123456`，然后直接 `setUser(... role: 'admin')` 写入 Zustand/localStorage。
- `apps/web/src/lib/api-client.ts` 没有从 user store 或 auth store 注入 `Authorization: Bearer ...`。
- 后端 admin API 依赖 `/api/auth/login` 返回 JWT，并通过 `Authorization` 头访问受保护路由。
- 影响：真实后端环境中可能出现“前端显示已登录，但 admin API 请求 401/403”的集成失败。

### F3 · Lighthouse CI 启动配置存在口径不一致（Medium）

- `.github/workflows/web-ci.yml` 使用 `treosh/lighthouse-ci-action@v12`，URL 指向 `http://127.0.0.1:8080/...`。
- `apps/web/lighthouserc.cjs` 也使用 8080 URL，但注释写“vite preview 启动（8081）”。
- workflow 未显式配置 `startServerCommand` / `startServerReadyPattern` / `staticDistDir`。
- 影响：LHCI 可能在 CI 中因服务未启动或端口口径不一致而假挂；也可能误以为 G3 Lighthouse 已真实复验。

### F4 · Chromatic token 缺失会阻塞 CI（Medium）

- `.github/workflows/web-ci.yml` 的 `chromatic` job 直接使用 `${{ secrets.CHROMATIC_TOKEN }}`，没有 secret 存在性条件。
- 当前项目状态仍把 Chromatic / Storybook baseline 视为外部 token 待配置项。
- 影响：未配置 token 的 push / PR 可能被 Chromatic job 阻断，与“外部 token 待配置”的文档口径不一致。

### F5 · 后端非 Docker 测试当前被本机 Python 环境阻塞（Environment）

- `python -m pytest ...` 失败：系统 Python 是 `C:\Python314\python.exe`，未安装 pytest。
- 项目 `.venv` 不存在。
- `uv run pytest ...` 失败：`uv trampoline failed to spawn Python child process`。
- 结论：这不是业务断言失败，但当前本机无法完成后端非 Docker regression 复验。

---

## 四、Sprint 状态

| Sprint | 当前状态 | 说明 |
|---|---|---|
| Sprint 1 | ✅ 完成 | Monorepo / CI 基础已落地 |
| Sprint 2 | ✅ 完成 | Vite + Zustand + TanStack Query 基础已落地 |
| Sprint 3 | ✅ 完成 | 5 新模块 + LLM fallback 已落地 |
| Sprint 4 | ⚠️ 部分完成 | 15/16 任务代码落地；e2e 回归已修；Lighthouse / 后端 / Docker 仍待环境复验 |
| Sprint 5 | ✅ 完成 | 14 shared 组件及测试已落地 |
| Sprint 6 | ✅ 完成 | 业务组件、暗色态、a11y 守门已落地 |
| Sprint 7 | ⚠️ 部分完成 | i18n + Admin 页面已落地；e2e 回归已修；G6.1 Lighthouse ≥95 待复验 |
| Sprint 8 | ❌ 未启动 | 仍无 Sprint 8 progress 文档和落地进度 |

---

## 五、已修复项

- **B1 e2e 14 个 i18n selector 回归**：已由 `2194f89` 修复。
- **B2 e2e 数量/状态口径不一致**：核心文档已更新为当前 29 tests/project 与非 Firefox 87/87 复验结果。
- **S1 bundle 数值过时**：已更新为 main 146.74 KB gzip、total 393.60 KB gzip，仍在预算内。
- **S3 Sprint 4 状态文档过时**：旧根目录 Sprint progress/closeout 文档已清理，当前状态以 `docs/CURRENT_STATE.md` 和 2026-07-05 review remediation 文档为准。
- **N1 MobileNav aria-label 测试不兼容 i18n**：e2e 已使用中英双语可访问名称匹配。
- **N2 poster alt 中文依赖**：e2e 已改为 `getByRole('img', { name: /海报预览|Poster preview/ })` 并补齐 job/status mock。

---

## 六、仍未完成项

- **F1 后台 `/admin/review` 断链**：需要补 admin 子路由或移除/改指导航项，并新增全量后台导航 e2e。
- **F2 React Admin 真实鉴权**：需要接入 `/api/auth/login`、保存 JWT，并在 `apiClient` 注入 `Authorization`。
- **F3 Lighthouse CI**：需要显式配置 LHCI 启动方式，统一 8080/8081 口径后在 CI 复跑。
- **F4 Chromatic CI**：需要在无 token 时跳过或降级为非阻塞 job。
- **Firefox 项目矩阵**：当前失败是本机 Playwright 环境级 `browserContext.newPage` 异常，需修复环境后补跑。
- **Lighthouse / LHCI**：需要 CI 或修复本机 Chrome 临时目录权限后复跑。
- **T-B-27 后端 regression**：需要真实后端与 pytest 环境。
- **T-C-44 Poster Docker**：需要 Docker 环境或 CI runner。
- **Sprint 8**：尚未启动，V10 不能宣称全部完成。

---

## 七、最终判断

**不能宣称 V10 前端重构全部完成。**

可以宣称：

- S1-S7 的主要前端代码已落地。
- 本轮发现的 14 个 i18n e2e 回归已修复。
- 非 Firefox 前端 e2e 矩阵已全绿。
- 本轮系统性二次 review 已完成前端 lint / typecheck / unit / build / Chromium e2e 验证，并识别出新的真实集成风险。
- 核心进度文档中的 e2e、bundle、commit hash 口径已修正。

仍需完成：

1. 修复 `/admin/review` 后台导航断链，并补全后台导航 e2e。
2. 将 React Admin 登录从 mock 改为真实 `/api/auth/login` + Bearer JWT。
3. 修复 Lighthouse / Chromatic CI 配置口径。
4. 修复 Firefox 本机 Playwright 环境异常并补跑 Firefox 矩阵。
5. 在 CI 或完整本地环境补跑 Lighthouse + T-B-27 后端 regression。
6. Docker 环境就绪后跑 T-C-44 Poster Docker 构建。
7. 启动并完成 Sprint 8。
