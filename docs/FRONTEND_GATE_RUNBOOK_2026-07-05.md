# FRONTEND_GATE_RUNBOOK_2026-07-05

> 生成时间：2026-07-05T21:47:26+08:00  
> 适用范围：`apps/web` / V10 React + TypeScript 前端本地门禁与 Review 复验。  
> 关联任务：`docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md` / T0-03。  
> 目的：避免再次把“node_modules / turbo 缺失”误报为前端代码失败，或把未执行的前端 gate 误报为通过。

---

## 1. 环境前置条件

当前仓库根 `package.json` 声明：

- `packageManager`: `pnpm@10.33.0`
- `engines.node`: `>=20`
- 根脚本依赖 `turbo run ...`

建议本地使用：

- Node.js 20.x（与 GitHub Actions 一致）或 Node.js 22.x（当前工作站已验证可运行）
- pnpm 10.33.0
- 从仓库根目录执行命令，不要只在 `apps/web` 子目录执行根 gate

检查命令：

```bash
node --version
pnpm --version
pnpm exec turbo --version
```

通过标准：

- `node --version` 为 v20.x 或 v22.x
- `pnpm --version` 输出 `10.33.0`
- `pnpm exec turbo --version` 可输出版本号，不得出现 `Command "turbo" not found`

---

## 2. 依赖安装

首次 clone、清理 `node_modules` 后、或 Review 复验前，必须先执行：

```bash
pnpm install --frozen-lockfile
```

安装后确认：

```bash
test -d node_modules && echo 'root node_modules exists'
test -d apps/web/node_modules && echo 'apps/web/node_modules exists'
pnpm exec turbo --version
```

禁止：

- 未执行 `pnpm install --frozen-lockfile` 就直接报告前端 gate 失败。
- 看到 `turbo: not found` 后把结果归类为代码失败。
- 用历史 green 报告替代当前 fresh gate。

---

## 3. 必跑本地前端门禁

从仓库根目录执行：

```bash
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

等价的包级调试命令：

```bash
pnpm --filter @gaokao/web typecheck
pnpm --filter @gaokao/web lint
pnpm --filter @gaokao/web test
pnpm --filter @gaokao/web build
```

通过标准：

- typecheck：0 error
- lint：0 error / 0 warning（按当前 eslint 配置）
- test：Vitest 全部通过
- build：Vite build 通过，`scripts/bundle-report.cjs` 输出 total gzip 不超过预算

当前 2026-07-05 fresh evidence 摘要：

```text
pnpm typecheck/lint/test/build: PASS
@gaokao/web build total: 393.60 KB gzip ✅
```

---

## 4. E2E / 浏览器 / 视觉门禁

本 runbook 的 `typecheck/lint/test/build` 通过只代表“前端本地基础门禁通过”，不代表 V10 全部前端验收闭环。

后续 Phase 1+ 必须继续补：

```bash
pnpm --filter @gaokao/web test:e2e
```

最低验收维度：

- Admin 真实登录，不再通过 localStorage seed 伪造 admin
- Admin 全导航遍历，所有 `adminNavItems` 不得落入 NotFound
- token 过期 / 401 / 403 错误态可恢复
- mobile-chrome 覆盖后台横向导航
- 关键用户页与后台页需真实浏览器视觉验收或等价截图基线

---

## 5. CI 口径

`.github/workflows/web-ci.yml` 当前 CI 使用 Node 20 + pnpm install，再执行：

```bash
pnpm typecheck
pnpm lint
pnpm test
pnpm build
pnpm --filter @gaokao/web test:e2e
```

仍需后续整改的 CI gate：

- LHCI preview 启动命令 / 端口 / ready pattern 必须显式一致
- Chromatic token 缺失时必须明确 skip / non-blocking / hard gate 语义
- Storybook / Chromatic 视觉基线尚不能被当作已闭环证据

---

## 6. 完成报告口径

正确表述：

- `前端本地基础门禁已 fresh PASS：typecheck/lint/test/build`
- `Playwright/LHCI/Chromatic/视觉验收仍待执行或待单独闭环`

禁止表述：

- `前端全部完成`（除非 e2e / LHCI / Chromatic / 视觉验收全部 fresh PASS）
- `历史报告显示通过，所以当前通过`
- `turbo not found，所以前端代码失败`
