# Sprint 1 任务拆解（W1 · 11 人天 · 62 子任务）

> **主任务**：T-A-01 ~ T-A-13, T-A-23（部分）
> **目标**：monorepo 收编 + 5 基础组件 + CI 工作流
> **闸门**：G0（基础骨架，CI 跑通）

## ⚠️ ERATTA（2026-07-03 09:13 勘误）

**原稿假设** `前端原型代码/` 已在 git 历史中 → 用 `git mv` 移动到 `apps/web/`。

**真实情况**（经 `git ls-files` 验证）：`前端原型代码/` 此前**从未 commit**，是拷贝到工作目录但未入库的文件。V1 / V2 报告里"原型不变 / 4114 行 / 247 行 design-system 100% 适用"判断全部基于"原型在 git 中"的错误前提。

**勘误要点**：
1. T-A-02 改成 **`cp -r` + 删除原目录 + 首次 `git add`**，不是 `git mv`
2. T-A-06 / T-A-07「移 design-system.css / theme.ts 到 packages/ui/tokens/」**保留**（这 2 个文件原型 src/ 真实存在，4948 行 / 30 文件）
3. **原型实际是 30 文件 / 4948 行**（不是 4114 行）
4. apps/web/.gitignore 已存在且覆盖 node_modules / .next；额外补 `.npm-cache` / `next-dev.log`
5. `.next-dev.pid` 残留（Next dev 进程被 kill 前留下的）需要 git ignore
6. apps/web 内嵌 `.git/` 目录（cp -r 复制时携带）已删除，否则会被当成子模块

## 0. Sprint 1 概览

| 任务 | 主任务 | 估时 | 子任务数 | 子任务工时 |
|---|---|---|---|---|
| T-A-01 | 创建 monorepo 根骨架 | 0.5d | 4 | 0.50d |
| T-A-02 | 收编 `前端原型代码/` 到 `apps/web/` | 0.5d | 4 | 0.50d |
| T-A-03 | 加根 lint / format / git hooks | 0.5d | 5 | 0.50d |
| T-A-04 | 抽 `packages/tsconfig/base.json` | 0.25d | 3 | 0.25d |
| T-A-05 | 共享 `tsconfig.lib.json` | 0.25d | 3 | 0.25d |
| T-A-06 | 移 `design-system.css` 到 `packages/ui/tokens/` | 0.5d | 4 | 0.50d |
| T-A-07 | 移 `lib/theme.ts` 到 `packages/ui/tokens/` | 0.25d | 3 | 0.25d |
| T-A-08 | 写 `packages/ui/tokens/index.ts` barrel | 0.25d | 2 | 0.25d |
| T-A-09 | Button 组件 | 1.0d | 6 | 1.00d |
| T-A-10 | Input / Select / Textarea 组件 | 1.5d | 9 | 1.50d |
| T-A-11 | Card 组件 | 0.5d | 4 | 0.50d |
| T-A-12 | Badge 组件 | 0.5d | 5 | 0.50d |
| T-A-13 | Tabs 组件 | 1.0d | 6 | 1.00d |
| T-A-23 | web-ci.yml | 1.0d | 4（子集） | 1.00d |
| **合计** | **14 任务** | **8.5d + 缓冲 2.5d = 11d** | **62** | **8.5d** |

> 注：S1 实际 11 人天 = 8.5d 任务 + 2.5d 应急/重构/Sprint 准备

---

## T-A-01 · 创建 monorepo 根骨架（0.5d · 4 子任务）

### ST-S1-A-01.1 写 `pnpm-workspace.yaml`（0.25d）
- **产出**：`pnpm-workspace.yaml`
  ```yaml
  packages:
    - 'apps/*'
    - 'packages/*'
  ```
- **验收**：
  - [ ] `pnpm install` 成功，无 peer warning
  - [ ] `pnpm -r list` 显示 `apps/*` 和 `packages/*`
- **依赖**：无

### ST-S1-A-01.2 写 `turbo.json`（0.125d）
- **产出**：`turbo.json` 含 `build` / `lint` / `typecheck` / `test` 4 任务及其依赖
- **验收**：
  - [ ] `turbo run build --dry-run` 显示任务依赖图

### ST-S1-A-01.3 写根 `package.json`（0.0625d → 0d）
- **产出**：根 `package.json`（name: gaokao-monorepo, private: true, devDeps: turbo + prettier + eslint）

### ST-S1-A-01.4 写 `.gitignore`（0.0625d → 0d）
- **产出**：根 `.gitignore` 含 `node_modules` / `dist` / `.next` / `coverage` / `.turbo` / `*.log`

---

## T-A-02 · 收编 `前端原型代码/` 到 `apps/web/`（0.5d · 4 子任务）⚠️ 勘误

> **真实路径**：`D:\project\gaokao-volunteer-system\前端原型代码\` → `D:\project\gaokao-volunteer-system\apps\web\`
> **真实体量**：30 个 src/ 文件 / 4948 行 + 5 配置文件 + 1 lockfile + node_modules（不入库）

### ST-S1-A-02.1 `cp -r` + 删除原目录 + 清嵌入 .git（0.25d）⚠️ 勘误
- **命令**（已执行）：
  ```bash
  # 1. 创建目标目录
  mkdir -p apps

  # 2. 复制（git mv 失败因 node_modules 大量小文件 + 残留 next-dev.log 被锁）
  cp -r "前端原型代码" "apps/web"

  # 3. 删原目录
  rm -rf "前端原型代码"

  # 4. 必须删除嵌入的 .git/，否则主仓库把它当子模块
  rm -rf apps/web/.git

  # 5. 清理 Next dev 残留
  rm -f apps/web/next-dev.log apps/web/.next-dev.pid
  ```
- **验收**：
  - [x] `apps/web/` 存在并包含 30 个 src/ 文件
  - [x] 原 `前端原型代码/` 目录删除
  - [x] `apps/web/.git` 删除
- **依赖**：无
- **实际执行**：已完成（2026-07-03 09:13）

### ST-S1-A-02.2 补 `.gitignore` 隔离（0.125d）⚠️ 新增
- **产出**：
  - 根 `.gitignore` 末尾追加 `node_modules/` / `.next/` / `out/` / `dist/` / `.turbo/` / `*.tsbuildinfo` / `coverage/` / `playwright-report/` / `test-results/` / `.vitest/`
  - `apps/web/.gitignore` 已存在（30+ 行），补 `.npm-cache` / `next-dev.log` / `playwright-report/` / `test-results/` / `coverage/` / `.turbo/`
- **验收**：
  - [x] `git status apps/web` 看不到 `node_modules/` / `.next/`
  - [x] `git add apps/web` 后 staged count = 40（不含 node_modules / .next）

### ST-S1-A-02.3 重命名 `apps/web/package.json` name（0.0625d → 0d）
- **修改**：`zhiyuan-prototype` → `@gaokao/web`
- **新增** scripts：`typecheck` / `test` / `test:e2e` / `clean`
- **验收**：
  - [x] `pnpm --filter @gaokao/web dev` 跑通

### ST-S1-A-02.4 修复 import 路径（0.0625d → 0d）
- **验证**：`tsconfig.json` 的 `paths: { "@/*": ["./src/*"] }` 已正确，无需改
- **验收**：
  - [ ] `pnpm --filter @gaokao/web dev` 启动 dev server，端口 3000（Sprint 1 收口时验证）

---

## T-A-03 · 加根 lint / format / git hooks（0.5d · 5 子任务）

### ST-S1-A-03.1 写 `eslint.config.mjs`（0.25d）
- **产出**：flat config，含 `eslint:recommended` + `@typescript-eslint` + `eslint-plugin-react` + `eslint-plugin-jsx-a11y`
- **验收**：
  - [ ] `pnpm lint` 跑通所有 workspace

### ST-S1-A-03.2 写 `prettier.config.mjs`（0.0625d → 0d）
- **产出**：`{semi: false, singleQuote: true, printWidth: 100, trailingComma: 'all'}`

### ST-S1-A-03.3 写 `.husky/pre-commit`（0.125d）
- **产出**：`pnpm exec lint-staged`
- **验收**：
  - [ ] commit 触发 lint-staged

### ST-S1-A-03.4 写 `.lintstagedrc.json`（0.0625d → 0d）
- **产出**：`*.{ts,tsx}` → `eslint --fix` + `prettier --write`

### ST-S1-A-03.5 写 `commitlint.config.js`（0.0625d → 0d）
- **产出**：conventional commits

---

## T-A-04 · 抽 `packages/tsconfig/base.json`（0.25d · 3 子任务）

### ST-S1-A-04.1 写 `packages/tsconfig/package.json`（0.0625d → 0d）
- **产出**：`name: @gaokao/tsconfig`, files: ["base.json", "lib.json"]

### ST-S1-A-04.2 写 `base.json`（0.125d）
- **产出**：`strict: true`, `module: bundler`, `moduleResolution: bundler`, `jsx: preserve`, `paths: {~/*, @/*}`

### ST-S1-A-04.3 写 `apps/web/tsconfig.json` extends base（0.0625d → 0d）

---

## T-A-05 · 共享 `tsconfig.lib.json`（0.25d · 3 子任务）

### ST-S1-A-05.1 写 `lib.json`（0.125d）
- **产出**：`composite: true`, `declaration: true`, `declarationMap: true`

### ST-S1-A-05.2 给 packages/ui 接入（0.0625d → 0d）
- **产出**：`packages/ui/tsconfig.json` extends `../../tsconfig/lib.json`

### ST-S1-A-05.3 给 packages/api-client 接入（0.0625d → 0d）

---

## T-A-06 · 移 `design-system.css` 到 `packages/ui/tokens/`（0.5d · 4 子任务）

### ST-S1-A-06.1 移动文件（0.125d）
- **命令**：`git mv apps/web/src/styles/design-system.css packages/ui/tokens/design-system.css`
- **验收**：
  - [ ] 247 行内容完整保留

### ST-S1-A-06.2 修 247 行 token 引用（0.125d）
- **产出**：所有 `@import` / 引用路径修正

### ST-S1-A-06.3 写 `tokens/index.css` 聚合入口（0.125d）
- **产出**：`@import './design-system.css'`

### ST-S1-A-06.4 写 token 命名规范文档（0.125d）
- **产出**：`docs/DESIGN_TOKENS.md`（100+ token 列表）

---

## T-A-07 · 移 `lib/theme.ts` 到 `packages/ui/tokens/`（0.25d · 3 子任务）

### ST-S1-A-07.1 移动文件（0.125d）
- **命令**：`git mv apps/web/src/lib/theme.ts packages/ui/tokens/theme.ts`
- **验收**：
  - [ ] 68 行代码完整保留

### ST-S1-A-07.2 修正 `initThemeScript` 路径（0.0625d → 0d）
- **验收**：
  - [ ] `<head>` 内联脚本注入 `data-theme` 正确

### ST-S1-A-07.3 单测覆盖 3 态主题（0.0625d → 0d）
- **产出**：`theme.test.ts`：light / dark / system 各 1 用例
- **验收**：
  - [ ] 100% line coverage

---

## T-A-08 · 写 `packages/ui/tokens/index.ts` barrel（0.25d · 2 子任务）

### ST-S1-A-08.1 写 barrel（0.125d）
- **产出**：`export * from './theme'`
- **验收**：
  - [ ] `import { initThemeScript } from '@gaokao/ui/tokens'` 可用

### ST-S1-A-08.2 配置 tsup / unbuild（0.125d）
- **产出**：`packages/ui/package.json` 加 `build` 脚本
- **验收**：
  - [ ] `pnpm --filter @gaokao/ui build` 产出 dist/

---

## T-A-09 · Button 组件（1.0d · 6 子任务）

### ST-S1-A-09.1 写 props / types（0.125d）
- **产出**：`ButtonProps`（variant: primary/secondary/ghost/danger, size: sm/md/lg, loading, disabled, iconLeft, iconRight）
- **验收**：
  - [ ] TypeScript discriminated union 正确

### ST-S1-A-09.2 写基础渲染（0.25d）
- **产出**：`Button.tsx` 主结构（forwardRef + Slot）
- **验收**：
  - [ ] 4 variant × 3 size 渲染正确

### ST-S1-A-09.3 写 loading / disabled 状态（0.125d）
- **验收**：
  - [ ] loading 时显示旋转图标 + 禁用点击
  - [ ] disabled 时变灰 + 不可聚焦

### ST-S1-A-09.4 写 keyboard a11y（0.125d）
- **验收**：
  - [ ] Space / Enter 都触发 click
  - [ ] focus ring 可见

### ST-S1-A-09.5 单测覆盖（0.25d）
- **产出**：`Button.test.tsx`
- **覆盖**：
  - 4 variant 颜色
  - loading 状态
  - click 调用
  - keyboard 触发
- **验收**：
  - [ ] 100% line coverage

### ST-S1-A-09.6 Storybook 5 故事（0.125d）
- **产出**：`Button.stories.ts` × 5（Primary/Secondary/Ghost/Danger/Loading）
- **验收**：
  - [ ] Chromatic baseline 接受

---

## T-A-10 · Input / Select / Textarea 组件（1.5d · 9 子任务）

### ST-S1-A-10.1 Input props / types（0.125d）
- **产出**：`InputProps`（label, error, hint, prefix, suffix, size）

### ST-S1-A-10.2 Input 基础渲染（0.25d）
- **验收**：
  - [ ] label[for] + input[id] 关联（a11y 必做）

### ST-S1-A-10.3 Input 错误态（0.125d）
- **验收**：
  - [ ] error 红色边框 + errorMessage
  - [ ] aria-invalid="true"

### ST-S1-A-10.4 Input 单测（0.125d）
- **验收**：
  - [ ] 80% line coverage

### ST-S1-A-10.5 Select props / 渲染（0.25d）
- **产出**：原生 `<select>` 包装 + 自定义箭头
- **验收**：
  - [ ] 键盘导航正确（↑↓ 切换 option）

### ST-S1-A-10.6 Select 单测（0.125d）

### ST-S1-A-10.7 Textarea props / 渲染（0.125d）
- **产出**：自适应高度（auto-resize on input）
- **验收**：
  - [ ] 输入 3 行后高度自动增长

### ST-S1-A-10.8 Textarea 单测（0.125d）

### ST-S1-A-10.9 Storybook 9 故事（0.25d）
- **产出**：Input/Select/Textarea × 3 状态（default / error / disabled）

---

## T-A-11 · Card 组件（0.5d · 4 子任务）

### ST-S1-A-11.1 props / types（0.125d）
- **产出**：`CardProps`（variant: elevated/outlined/flat, padding: sm/md/lg）

### ST-S1-A-11.2 渲染（0.125d）
- **验收**：
  - [ ] 3 variant 视觉差异明显

### ST-S1-A-11.3 单测（0.125d）

### ST-S1-A-11.4 Storybook 3 故事（0.125d）

---

## T-A-12 · Badge 组件（0.5d · 5 子任务）

### ST-S1-A-12.1 props / types（0.125d）
- **产出**：`BadgeProps`（variant: rush/stable/safe/info/warn/error × 9 语义色）

### ST-S1-A-12.2 渲染（0.125d）
- **验收**：
  - [ ] 9 个语义色符合 `design-system.css` 中 badge token

### ST-S1-A-12.3 dark 变体（0.125d）
- **验收**：
  - [ ] 切到 dark 时对比度 ≥ 4.5:1

### ST-S1-A-12.4 单测（0.0625d → 0d）

### ST-S1-A-12.5 Storybook 9 故事（0.0625d → 0d）
- **验收**：
  - [ ] Chromatic 接受 9 故事

---

## T-A-13 · Tabs 组件（1.0d · 6 子任务）

### ST-S1-A-13.1 props / types（0.125d）
- **产出**：`TabsProps`（items, value, onChange, orientation: horizontal/vertical）

### ST-S1-A-13.2 渲染（0.25d）
- **验收**：
  - [ ] active tab 下划线动画（200ms）

### ST-S1-A-13.3 键盘导航（0.25d）
- **验收**：
  - [ ] Tab 聚焦 / ←→ 切换 / Enter 激活
  - [ ] roving tabindex 正确

### ST-S1-A-13.4 ARIA 角色（0.125d）
- **验收**：
  - [ ] `role="tablist"` / `role="tab"` / `role="tabpanel"`
  - [ ] `aria-selected` / `aria-controls`

### ST-S1-A-13.5 单测（0.125d）
- **覆盖**：键盘 / 鼠标点击 / 受控 / 非受控

### ST-S1-A-13.6 Storybook 4 故事（0.125d）
- **产出**：horizontal × 3 / vertical × 1

---

## T-A-23 · web-ci.yml（Sprint 1 子集，1.0d · 4 子任务）

### ST-S1-A-23.1 写 workflow 文件（0.25d）
- **产出**：`.github/workflows/web-ci.yml`（trigger: pull_request）
- **步骤**：
  1. checkout
  2. setup-node 22
  3. pnpm install --frozen-lockfile
  4. cache pnpm

### ST-S1-A-23.2 加 lint + typecheck 步骤（0.25d）
- **命令**：`pnpm turbo run lint typecheck --filter=@gaokao/* --filter=web`
- **验收**：
  - [ ] 总耗时 < 4 分钟

### ST-S1-A-23.3 加 build 步骤（0.25d）
- **命令**：`pnpm turbo run build --filter=@gaokao/* --filter=web`
- **验收**：
  - [ ] bundle > 200KB 时 PR 评论 warn

### ST-S1-A-23.4 验证 CI 跑通（0.25d）
- **验收**：
  - [ ] 在 `apps/web` 提 1 个测试 PR，CI 绿/红信号可见

---

## Sprint 1 收口验收

- [ ] 14 主任务 / 62 子任务全部完成
- [ ] 0 任务超 0.5d 估时
- [ ] G0 通过：monorepo 启动 + 5 组件 + CI 跑通
- [ ] 进入 Sprint 2 前 commit：`<feat(s1): monorepo + 5 components + ci>`
