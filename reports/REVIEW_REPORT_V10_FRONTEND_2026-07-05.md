# V10 前端重构 · 真实状态复核报告

> **审查日期**：2026-07-05  
> **复核更新**：2026-07-05，已纳入 `2194f89 fix: stabilize e2e assertions after i18n migration`  
> **审查范围**：Sprint 1 ~ Sprint 8 前端重构任务  
> **结论**：S1-S7 前端代码已落地，i18n 迁移导致的 14 个 e2e 回归已修复；但 Lighthouse / 后端 regression / Docker / Firefox 本机环境复验 / Sprint 8 仍未完成，不能宣称 V10 全部完成。

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
| targeted e2e | data-query + navigation + poster，8/8 passed | ✅ 通过 |
| Chromium e2e | 29/29 passed | ✅ 通过 |
| 非 Firefox e2e 矩阵 | Chromium + WebKit + mobile-chrome，87/87 passed | ✅ 通过 |
| Firefox e2e | 本机 Playwright `browserContext.newPage` 环境异常 | ⏳ 待环境复验 |
| Lighthouse / LHCI | 本机 Chrome 临时目录 EPERM，未复跑 | ⏳ 待 CI 或环境修复 |
| T-B-27 后端 regression | 本轮未复跑，需要真实后端 / pytest 环境 | ⏳ 待环境 |
| T-C-44 Poster Docker | 本机暂无 Docker | ⏳ 待环境 |

---

## 三、Sprint 状态

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

## 四、已修复项

- **B1 e2e 14 个 i18n selector 回归**：已由 `2194f89` 修复。
- **B2 e2e 数量/状态口径不一致**：核心文档已更新为当前 29 tests/project 与非 Firefox 87/87 复验结果。
- **S1 bundle 数值过时**：已更新为 main 146.74 KB gzip、total 393.60 KB gzip，仍在预算内。
- **S3 Sprint 4 标题不一致**：`SPRINT_4_PROGRESS_2026-07-03.md` 已从 9/16 修正为 15/16。
- **S4 working tree 标记过时**：Sprint 4 文档已改为实际 commit hash。
- **N1 MobileNav aria-label 测试不兼容 i18n**：e2e 已使用中英双语可访问名称匹配。
- **N2 poster alt 中文依赖**：e2e 已改为 `getByRole('img', { name: /海报预览|Poster preview/ })` 并补齐 job/status mock。

---

## 五、仍未完成项

- **Firefox 项目矩阵**：当前失败是本机 Playwright 环境级 `browserContext.newPage` 异常，需修复环境后补跑。
- **Lighthouse / LHCI**：需要 CI 或修复本机 Chrome 临时目录权限后复跑。
- **T-B-27 后端 regression**：需要真实后端与 pytest 环境。
- **T-C-44 Poster Docker**：需要 Docker 环境或 CI runner。
- **Sprint 8**：尚未启动，V10 不能宣称全部完成。

---

## 六、最终判断

**不能宣称 V10 前端重构全部完成。**

可以宣称：

- S1-S7 的主要前端代码已落地。
- 本轮发现的 14 个 i18n e2e 回归已修复。
- 非 Firefox 前端 e2e 矩阵已全绿。
- 核心进度文档中的 e2e、bundle、commit hash 口径已修正。

仍需完成：

1. 修复 Firefox 本机 Playwright 环境异常并补跑 Firefox 矩阵。
2. 在 CI 或完整本地环境补跑 Lighthouse + T-B-27 后端 regression。
3. Docker 环境就绪后跑 T-C-44 Poster Docker 构建。
4. 启动并完成 Sprint 8。

