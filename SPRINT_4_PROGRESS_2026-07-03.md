# Sprint 4 阶段进度报告 (V10 选项 B · 15/16 任务)

> **日期**：2026-07-05（e2e i18n 回归修复后）
> **真实状态**：⏳ **PARTIAL — 已完成 15/16 任务，T-C-44 配置/CI 已落地但本地 Docker 构建待环境验证**
> **不能宣称"Sprint 4 完成"** ❌
> **下一步**：剩余阻塞项为 T-C-44 Poster CLI Docker 本地构建验证

---

## ⚠️ 重要的更正

原 `SPRINT_4_CLOSEOUT_2026-07-03.md` 文件标题用了"收口报告"和"G3 闸门全部通过"，但实际：

- **Sprint 4 任务表共 16 任务 / 53 子任务 / 10 人天**
- **本次完成 5 任务 / 15 子任务**
- **G3 闸门定义包含**："8 e2e spec 全绿 + 真实后端 5 模块 200 + Lighthouse P/A/B/S ≥ 90"
- **已通过的 G3 子项**：typecheck / lint / vitest / playwright（Chromium + WebKit + mobile-chrome）/ build
- **待环境复验的 G3 子项**：Lighthouse / 真实后端回归（当前本机无 Docker，pytest 环境未作为本轮复验前置）
- **待环境验证的 G4 子项**：Poster CLI Docker 镜像本地构建

正确标签应该是"Sprint 4 阶段 1 完成"，而不是"Sprint 4 完成"。

---

## ✅ 实际完成（15 任务 · 47 子任务，截至 T-B-27 真实后端回归验证）

| ID | 任务 | 子任务 | 状态 | Commit |
|---|---|---|---|---|
| T-B-18 | 错误码映射 | 3/3 | ✅ | `86296bd` |
| T-B-19 | ErrorBoundary | 3/3 | ✅ | `ad261d7` |
| T-B-20 | 离线检测 | 4/4 | ✅ | `c4f12ca` |
| T-B-21 | SubmitButton 守卫 | 3/3 | ✅ | `411f225` |
| T-B-22 | Query 持久化 | 3/3 | ✅ | `f5e40a4` |
| **T-B-23** | **e2e 真实化（8 spec）** | **8/8** | ✅ | **`1a49439`** |
| **T-B-24** | **Lighthouse CI** | **4/4** | ✅ | **`61ba0ca`** |
| **T-B-25** | **Bundle 优化验证** | **3/3** | ✅ | **`bf5ad4a`** |
| **T-B-26** | **路由级 prefetch** | **2/2** | ✅ | **`97cd431`** |
| **T-B-27** | **真实后端回归** | **2/2** | ✅ | **`06a0f47`** |
| **T-B-40** | **Share Link 状态面板** | **3/3** | ✅ | **`fecdb67`** |
| **T-B-41** | **ShareLink 失败降级** | **3/3** | ✅ | **`c955459`** |
| **T-B-42** | **LLM 增强进度轮询** | **3/3** | ✅ | **`c7f1dd4`** |
| **T-B-43** | **Poster 异步生成 + 轮询** | **3/3** | ✅ | **`45e6719`** |
| **T-C-45** | **集成测试套件** | **2/2** | ✅ | **`45e6719`** |

---

## ⏳ 剩余 / 阻塞（1 任务 · 4 子任务）

### T-B-23 · e2e 真实化（2.0d · 8 子任务） ✅ DONE
8 个真实业务流 e2e：theme-switch / chat-send-receive / form-submit-validation / plan-create-view / data-query-search / review-flow-approve / poster-generate-download

**修复 3 类 e2e bug**：
- Playwright 多 handler 同时匹配：fallback `**/api/**` 覆盖精细 mock → 改用 `(url) => url.pathname.startsWith('/api/') && !includes(精确路径)`
- ReadableStream 不被 `route.fulfill` 接受 → 用 `Buffer.from(sse, 'utf-8')`
- Mobile viewport 下 fixed nav 拦截 click → 用 Enter 键 + `{force: true}` + 验证 disabled

2026-07-05 复验：i18n 迁移导致的 e2e selector 回归已在 `2194f89` 修复。

当前可验证结果：
- Targeted 回归 spec：**8/8 passed**
- Chromium 全量：**29/29 passed**
- Chromium + WebKit + mobile-chrome：**87/87 passed**
- Firefox：本机 Playwright 环境触发 `browserContext.newPage` 异常，需环境修复后单独复验；不再计入本轮 i18n selector 回归。

### T-B-24 · Lighthouse CI 集成（1.5d · 4 子任务） ✅ DONE
- 装 `@lhci/cli` v0.14
- `apps/web/lighthouserc.cjs`: desktop preset, 3 runs, P/A/B/S ≥ 90 断言
- GitHub Action `treosh/lighthouse-ci-action@v12` + temporaryPublicStorage
- 本地实测：P=100 / a11y=95 / best=96 / seo=91

### T-B-25 · Bundle 优化验证（0.5d · 3 子任务） ✅ DONE
- `vite.config.ts`: production sourcemap=false（build time 17.89s → 6.89s）
- `scripts/bundle-report.cjs`: 总 500KB / 单 chunk 150KB budget
- 8 vendor manualChunks 保持 + lazy page chunks 新增

### T-B-26 · 路由级 prefetch（0.5d · 2 子任务） ✅ DONE
- `usePrefetchLazyRoute` hook：lazy route loaders 注册表
- `RouteFallback` Suspense fallback（48px min-height）
- `Sidebar` NavLink onMouseEnter/onFocus 触发 prefetch
- 2026-07-05 最新构建：main chunk 146.74 KB gzip，total 393.60 KB gzip；仍低于单 chunk 150 KB / total 500 KB 预算，但不再沿用 81.30 KB 旧口径。

### T-C-44 · Poster CLI Docker（1.0d · 4 子任务）
- ✅ `Dockerfile.poster` 已补
- ✅ `docker-compose.yml` 已添加 `gaokao-poster` profile 服务
- ✅ CI 已添加 Poster CLI Docker 合同测试与 `docker build -f Dockerfile.poster`
- ⏳ 本地 Docker 构建验证未跑：当前环境未安装 `docker`

---

## 🔍 当前 G 闸门真实状态（2026-07-03 深夜）

| 闸门 | 定义 | 实测 | 状态 |
|---|---|---|---|
| typecheck | `tsc --noEmit` 0 error | 0 error | ✅ |
| lint | `eslint .` 0 error 0 warning | 0 error 0 warning | ✅ |
| vitest | 单测全过 | 69/69 (17 文件) | ✅ |
| e2e | 8+ spec 全绿 | Chromium 29/29；Chromium + WebKit + mobile-chrome 87/87；Firefox 待本机环境修复后复验 | ⚠️ |
| build | bundle 主 chunk < 150KB gzip | main 146.74 KB · total 393.60 KB | ✅ |
| **Lighthouse** | **P/A/B/S ≥ 90（desktop）** | 历史 P=100, a11y=95, best=96, seo=91；本轮未复跑 | ⏳ |
| 真实后端 | 5 模块 200 | 历史报告 `reports/sprint4-real-backend-regression.json` 存在；本轮未复跑 | ⏳ |
| G4 Poster CLI | Docker 镜像本地构建 | Dockerfile/compose/CI 已落地；本地构建待 Docker 环境 | ⏳ |

---

## 🛡 防止再"虚假完成"

上一版本 Sprint 4 closeout 文档把"5/16 任务完成"包装成"全部通过 G3 + Sprint 4 完成"。这是用户已知的问题。**新规则**：

1. **任务表 vs 状态表**：每篇 closeout 必须用任务表的真实状态（完成 5/16），而不是"全部通过"
2. **闸门 vs 子任务**：G3 闸门定义要拆成可独立标记的子项
3. **阶段完成 ≠ Sprint 完成**：5 任务完成是"Sprint 4 阶段 1 完成"，不是"Sprint 4 完成"
4. **真实命令输出 ≠ 真实实现**：每个 commit 都要看实际文件

---

## 下一步

建议继续：
- 选项 A：安装/启用 Docker 后，跑 T-C-44 Poster CLI Docker 本地构建验证
- 选项 B：在可用 Python 后端环境中补跑后端 pytest 契约测试
