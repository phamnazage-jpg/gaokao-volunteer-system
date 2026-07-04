# 高考志愿系统 - 长期项目记忆

## 项目核心
- **业务**：高考志愿填报辅助系统（chat-based AI + 数据查询 + 审核流）
- **后端**：Python 3.10/3.11/3.12 + FastAPI + sqlite3 + Pydantic + Fernet 加密
- **前端**：Vite 5 + React 19 + Zustand 4 + TanStack Query 5 + RHF 7 + Zod
- **测试**：Vitest 2 + Playwright 1.55 + Chromatic
- **monorepo**：pnpm 10.33 + Turborepo 2.10
- **仓库**：`https://tksea.top/niuniu/gaokao-volunteer-system.git`（自定义 Git 服务器）

## 文档体系
- `V10_REFACTOR_STRATEGY_UI_VS_TECH.md` ⭐ UI/交互层 × 技术层解耦（PM 拍板文档）
- `EXECUTION_ROADMAP_V10_2026-07-03.md` ⭐ V10 路线图
- `REVIEW_REPORT_2026-07-02_SENIOR_DEVELOPER.md` V2 全面审查
- `FRONTEND_REFACTOR_PLAN_2026-07-02.md` V2 重构方案
- `SPRINT_1_S1_FOUNDATION.md` ~ `SPRINT_8_S8_ADMIN_POLICY.md` 8 个 Sprint 子文档
- `SPRINT_1_CLOSEOUT_2026-07-03.md` Sprint 1 收口
- `SPRINT_2_CLOSEOUT_2026-07-03.md` Sprint 2 收口
- `SPRINT_3_CLOSEOUT_2026-07-03.md` Sprint 3 收口
- `SPRINT_4_CLOSEOUT_2026-07-03.md` Sprint 4 收口（含 4 防虚假完成铁律）
- `SPRINT_4_CLOSEOUT_2026-07-03_SUPERSEDED.md` ⚠️ 旧虚假收口（反面教材）
- `SPRINT_4_PROGRESS_2026-07-03.md` Sprint 4 真实阶段进度（5/16 任务）
- `REVIEW_REPORT_SPRINT_1_TO_4_2026-07-03.md` Sprint 1-4 文件级审查报告

## Sprint 状态
- **S1 ✅ 完成**（2026-07-03 G0 通过）
- **S2 ✅ 完成**（2026-07-03 G1 通过，33 any 清零，49 warning 清零）
- **S3 ✅ 完成**（2026-07-03 G2 通过，5 模块端到端 + LLM 4 模 fallback）
- **S4 ⏳ 阶段 1 + 2 完成（9/16 任务）** — T-B-18/19/20/21/22/23/24/25/26 ✅，剩余 7 任务未启动
- **S5-S8 ⏳ 待启动**

## Sprint 4 真实状态（2026-07-03 深夜审计 + 推进）

**已完成（9/16，截至 commit 97cd431）**：
- T-B-18 错误码 / T-B-19 ErrorBoundary / T-B-20 离线 / T-B-21 SubmitButton / T-B-22 Query 持久化
- **T-B-23 e2e 真实化**（commit `1a49439`）— 8 spec 全跑通，84/84 4 浏览器 × 21 测试通过
- **T-B-24 Lighthouse CI**（commit `61ba0ca`）— desktop P=100 / a11y=95 / best=96 / seo=91 全 ≥ 90
- **T-B-25 Bundle 优化**（commit `bf5ad4a`）— sourcemap=false + 8 vendor chunks + budget 校验（总 301 KB gzip）
- **T-B-26 路由 prefetch**（commit `97cd431`）— 4 page 拆 lazy + hover prefetch + Suspense fallback（main chunk 81.30 KB）

**未启动（7/16）**：
- 🔴 T-B-27 真实后端回归（docker compose）
- 🔴 T-C-44 Poster CLI Docker（G4 闸门）
- 🟡 T-B-40 Share Link 状态面板 / T-B-41 失败降级 / T-B-42 LLM 轮询 / T-B-43 Poster 轮询
- 🟢 T-C-45 集成测试套件

**G3 闸门真实状态**：
- ✅ typecheck / lint / vitest 69 / e2e 84/84 / build 81.30KB main / Lighthouse P/A/B/S 全 ≥ 90
- ⏳ T-B-27 真实后端 5 模块 200（用户需提供后端 docker compose）/ T-C-44 Poster Docker

**教训**：原 `SPRINT_4_CLOSEOUT_2026-07-03.md` 把"5/16 任务"包装成"全部通过"是虚假收口，已重命名为 `_SUPERSEDED.md`。正确文档见 `SPRINT_4_PROGRESS_2026-07-03.md` + `REVIEW_REPORT_SPRINT_1_TO_4_2026-07-03.md`。

## V10 关键决策（2026-07-03 PM 拍板）
- 原型只锁 UI/交互，不锁技术栈
- 整体重写为新实现（解决 33 any + 16 unused + 49 warning）
- Playwright + Chromatic 双验收
- 82 人天（节省 10d vs V2）

## Sprint 2 关键成果（2026-07-03 下午）
- 切 Vite 5 + React 19 框架（删除 Next.js 16）
- 4 Zustand slice 替代 7 手写 hook（800+ 行 → 320 行）
- 15 TanStack Query hooks（chat/consultation/plan/audit/upload）
- 25 单测 + 20 e2e（4 浏览器）
- Vite build 192 KB gzip（目标 < 300 KB）
- Git: commit `e8b8ad0` + merge `5ea8221`

## Sprint 3 关键成果（2026-07-03 傍晚）
- 5 个新模块（Share / Query / Review / LLM / Poster）端到端跑通
- 30+ TanStack Query hooks + 5 页面 + 1 LLM 适配器
- 4 模 fallback 链：claude → gpt → gemini → deepseek
- 37 单测 + 24 e2e（4 浏览器 × 6 spec）
- Vite build 312 KB gzip（recharts 拆分后主 chunk 83KB）
- Git: commit `e24cbb7`

## Sprint 4 关键成果（2026-07-03 晚间）
- 5 个韧性 + 质量任务：错误码映射 / ErrorBoundary / 离线恢复 / SubmitButton 守卫 / Query 持久化
- 69 单测 + 28 e2e（4 浏览器 × 7 spec） · 主 chunk 87.85 KB gzip
- 修复 T-B-22 真实"虚假完成"：build 缺包已修复，5 闸门全绿

## 经验教训
1. **原型未在 git 中**：Sprint 1 勘误。原"git mv"假设是错的，用 `cp -r` 替代
2. **G0 闸门先于 Sprint 2**：确保 monorepo + CI 灯绿后再启动业务开发
3. **整体重写 vs 渐进重构**：当原型有 33 any + 49 warning 时，整体重写更划算
4. **设计 token 提前抽取**：避免后续 Sprint 反复修改
5. **主题持久化双源方案**：ThemeToggle 同步写 localStorage['theme-pref']，index.html 内联脚本读，刷新不丢
6. **MobileNav fixed 定位**：Playwright 768px 视口能正确识别，避免 flex 父级挤压
7. **Vite 切框架保留 monorepo**：turbo.json/pnpm-workspace.yaml/CI 已 Sprint 1 验证，S2 只在 apps/web 内部切
8. **4 模 LLM fallback 链**：enhanceWithFallback(order) 接受 provider 数组，依次尝试，最后一个失败时抛错
9. **apiClient 强制 Zod schema**：所有 API 调用第二个参数必须是 ZodSchema，无 schema 编译失败（保持 0 any）
10. **大体积包拆 manualChunk**：recharts 375KB 拆 chart-vendor，触发懒加载时下载
11. **Portal token 路由**：/portal/:token 共享 token 字段，自动级联 CWB + 完整方案
12. **🛡 防虚假完成铁律（**Sprint 4 核心收获**）**：
    - **build 失败 ≠ 测试通过**：typecheck/lint/test/build/e2e 五件套缺一不可
    - **commit message ≠ 真实实现**：每个 closeout 必须附真实命令输出，不能只贴 ✅
    - **pnpm install 不重装**：用 `--force` 才能真正同步 node_modules
    - **装依赖 ≠ 类型有**：use 时若类型仍 unknown，要把测试 / 调用改写匹配生产代码
13. **离线等待用 event 而不是 polling**：api-client.waitUntilOnline 监听 'online' 事件 + signal.abort，省 CPU + 立即响应
14. **useSyncExternalStore for navigator.onLine**：3 参版（subscribe/getSnapshot/serverSnapshot），SSR 返回 true 无 hydration mismatch
15. **queryPersistenceBuster 版本号**：作为 storage key 后缀，schema 升级时 bump 即可失效旧缓存
16. **🚨 防止"虚假完成"（Sprint 4 自我纠错）**：
    - **任务表 vs 状态表**：closeout 必须用任务表的真实进度（"5/16 任务"），不能写"全部通过"
    - **闸门必须可独立标记**：G3 含 typecheck/lint/vitest/e2e/build/Lighthouse/后端 7 子项，**不能合并**
    - **阶段完成 ≠ Sprint 完成**：5 任务完成是"阶段 1"，不是"Sprint 完成"
    - **commit message 不算数**：每个交付要看实际文件 + 跑真实命令
    - **closeout 文档需要 PM 拍板**：自动产出的 closeout 标 ⏳，人工确认后改 ✅
17. **G3 闸门 Sprint 4 真实缺口**：当前 e2e 5/8 spec，Lighthouse / 真实后端 / Poster Docker 全部未启动
18. **Playwright 多 handler 同时匹配 bug**：先注册的 handler 被先调用，所以 `**/api/**` fallback 会覆盖前面的精细 mock。修复：fallback 用 `(url) => url.pathname.includes(...)` 排除精确路径，或者直接不注册 fallback
19. **Playwright ReadableStream 不被 route.fulfill 接受**：用 `Buffer.from(sse, 'utf-8')` 替代 `body: stream`
20. **Mobile viewport fixed 元素拦截 click**：mobile chrome 下 MobileNav 的 fixed bottom nav 会覆盖 send button。用 Enter 键或者 `{force: true}` 触发；测试逻辑改成"验证 disabled 状态"更稳定
21. **treosh/lighthouse-ci-action@v12 serverUrl**：默认 8080 port，treosh 自动启 vite preview。如果 url 写错端口会假阴性
22. **production sourcemap=false build time 大幅下降**：17.89s → 6.89s（65% ↓），bundle 仅 -30% size，生产 CI 收益显著
23. **React.lazy + Suspense 拆 page chunk**：4 page 拆出去后 main 81.30 KB（-4.27 KB），但 vendor (recharts 101 KB) 仍在主 chunk — manualChunks vs lazy load 不能互替，需要保留双层拆分
24. **🆕 T-B-26 e2e+real bundle**：split lazy 后 main chunk 85→81 KB / app chunks 1→6，hover prefetch 让用户 0 延迟进入下一页
25. **Lighthouse desktop preset 比 mobile 宽松**：mobile preset 90+ 几乎不可能，V10 默认 desktop 已被 PM 接受

## UI/交互 12 项不变量（V10 锁定）
- 布局 4 项：1024px 断点 / 移动 48px Tab / 中间折叠 / 容器宽度
- 组件 4 项：PlanCard 3-Tab / ModeIndicator 4 模式 / FormCard 3-step / Badge 8 态
- 行为 2 项：Typing 三态 / SafeMarkdown XSS
- 设计 2 项：247 行 design token / 三主题 + 1.2s 缓动 + SSR/CSR 一致

## 视觉基线（Chromatic）
- S1: 5 组件 × 5 态 = 25 截图
- S2: 8 页面 × 3 主题 = 24 截图
- S3: 13 页面（含 5 新模块）= 13 截图
- S6: 7 业务组件 × 3 主题 × 3 viewport × 6 态 = 378 截图
- S7: 所有 admin 页面
- S8: 12 后台 + 10 公共门户页
