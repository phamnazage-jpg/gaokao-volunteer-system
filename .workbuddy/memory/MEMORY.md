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

## Sprint 状态
- **S1 ✅ 完成**（2026-07-03 G0 通过）
- **S2 ✅ 完成**（2026-07-03 G1 通过，33 any 清零，49 warning 清零）
- **S3-S8 ⏳ 待启动**

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

## 经验教训
1. **原型未在 git 中**：Sprint 1 勘误。原"git mv"假设是错的，用 `cp -r` 替代
2. **G0 闸门先于 Sprint 2**：确保 monorepo + CI 灯绿后再启动业务开发
3. **整体重写 vs 渐进重构**：当原型有 33 any + 49 warning 时，整体重写更划算
4. **设计 token 提前抽取**：避免后续 Sprint 反复修改
5. **主题持久化双源方案**：ThemeToggle 同步写 localStorage['theme-pref']，index.html 内联脚本读，刷新不丢
6. **MobileNav fixed 定位**：Playwright 768px 视口能正确识别，避免 flex 父级挤压
7. **Vite 切框架保留 monorepo**：turbo.json/pnpm-workspace.yaml/CI 已 Sprint 1 验证，S2 只在 apps/web 内部切

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
