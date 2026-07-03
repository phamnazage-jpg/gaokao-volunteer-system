# Sprint 5 任务拆解（W8-9 · 9 人天 · 48 子任务）— V10 选项 B

> **技术栈**：Vite 5 + React 19 + Zustand 4 + TanStack Query 5 + RHF 7 + Zod
> **目标**：高级组件（DataTable/Tree/Chart/Modal/Toast/Tooltip 等）+ Storybook 收口
> **闸门**：G5（18 组件 dark story 全覆盖 + axe-core 0 critical）
> **V10 变化**：从 12d 缩到 9d（节省 3d = TanStack Table/Virtual 内置能力 + RHF 简化）
> **PM 决策（2026-07-03）**：整体重写为新实现；Playwright 视觉回归 + Chromatic 验收

---

## ⚠️ V10 关键变化（与 V2 对比）

| 维度 | V2 | V10 选项 B |
|---|---|---|
| DataTable | 手写 virtualization | **TanStack Table 8 + TanStack Virtual 3** |
| Tree 组件 | 手写递归 | **react-arborist** |
| Chart 组件 | recharts 基础 | **recharts 2 + V10 主题适配** |
| 表单组件 | 手写 | **RHF + Zod** |
| 总估时 | 12d | **9d** |

---

## 0. Sprint 5 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-D-01 | DataTable（TanStack Table + Virtual） | 1.0d | 4 |
| T-D-02 | Tree（react-arborist） | 0.5d | 3 |
| T-D-03 | Chart（recharts + 主题） | 1.0d | 4 |
| T-D-04 | Modal / Dialog | 0.5d | 3 |
| T-D-05 | Toast / Notification | 0.5d | 3 |
| T-D-06 | Tooltip | 0.25d | 2 |
| T-D-07 | Dropdown / Select 增强 | 0.5d | 3 |
| T-D-08 | DatePicker | 0.5d | 3 |
| T-D-09 | Pagination | 0.25d | 2 |
| T-D-10 | EmptyState | 0.25d | 2 |
| T-D-11 | Skeleton | 0.25d | 2 |
| T-D-12 | Avatar | 0.25d | 2 |
| T-D-13 | Stepper | 0.5d | 3 |
| T-D-14 | Accordion | 0.5d | 3 |
| T-D-15 | Storybook 配置 + dark story 全覆盖 | 1.5d | 5 |
| T-D-16 | axe-core CI 集成 | 0.5d | 3 |
| **合计** | **16 任务** | **8.5d + 缓冲 0.5d = 9d** | **47** |

---

## T-D-01 · DataTable（TanStack Table + Virtual · 1.0d · 4 子任务）⚠️ V10 升级

### ST-S5-D-01.1 安装依赖（0.125d）
```bash
pnpm --filter web add @tanstack/react-table @tanstack/react-virtual
```

### ST-S5-D-01.2 写 `<DataTable>` 组件（0.5d）
- **V10 收益**：TanStack Table headless + Virtualization
- **特性**：列排序/筛选/分页/虚拟滚动
- **类型**：泛型 `<TData, TValue>` 强类型

### ST-S5-D-01.3 写 4 列示例（0.125d）

### ST-S5-D-01.4 写 story + 测试（0.25d）

---

## T-D-02 · Tree（react-arborist · 0.5d · 3 子任务）⚠️ V10 升级

### ST-S5-D-02.1 安装依赖（0.125d）

### ST-S5-D-02.2 写 `<Tree>` 组件（0.25d）
- **特性**：拖拽 / 搜索 / 多选

### ST-S5-D-02.3 写 story + 测试（0.125d）

---

## T-D-03 · Chart（recharts + 主题 · 1.0d · 4 子任务）

### ST-S5-D-03.1 安装依赖（0.125d）

### ST-S5-D-03.2 写 4 类 chart（0.5d）
- LineChart / BarChart / PieChart / AreaChart
- **V10 关键**：与 design-system token 集成（247 行 CSS）

### ST-S5-D-03.3 写主题切换适配（0.25d）
- **行为**：dark 模式自动切换配色

### ST-S5-D-03.4 写 story + 测试（0.125d）

---

## T-D-04 · Modal / Dialog（0.5d · 3 子任务）

### ST-S5-D-04.1 写 `<Modal>` 组件（0.25d）
- **V10 收益**：用 `@radix-ui/react-dialog` 头less

### ST-S5-D-04.2 写动画 + 焦点陷阱（0.125d）

### ST-S5-D-04.3 写 story + 测试（0.125d）

---

## T-D-05 · Toast / Notification（0.5d · 3 子任务）

### ST-S5-D-05.1 安装 sonner（0.125d）
- **V10 收益**：用 `sonner` 库，避免手写 toast 系统

### ST-S5-D-05.2 写 `<Toaster>` 集成（0.25d）

### ST-S5-D-05.3 写 story + 测试（0.125d）

---

## T-D-06 · Tooltip（0.25d · 2 子任务）

### ST-S5-D-06.1 写 `<Tooltip>` 组件（0.125d）
- **V10 收益**：`@radix-ui/react-tooltip`

### ST-S5-D-06.2 写 story + 测试（0.125d）

---

## T-D-07 · Dropdown / Select 增强（0.5d · 3 子任务）

### ST-S5-D-07.1 写 `<Dropdown>` 组件（0.25d）
- **V10 收益**：`@radix-ui/react-dropdown-menu`

### ST-S5-D-07.2 写 `<Select>` 组件（0.125d）
- **V10 收益**：`@radix-ui/react-select` + RHF `Controller`

### ST-S5-D-07.3 写 story + 测试（0.125d）

---

## T-D-08 · DatePicker（0.5d · 3 子任务）

### ST-S5-D-08.1 安装 react-day-picker（0.125d）

### ST-S5-D-08.2 写 `<DatePicker>` 组件（0.25d）
- **V10 集成**：RHF `Controller` + Zod `coerce.date()`

### ST-S5-D-08.3 写 story + 测试（0.125d）

---

## T-D-09 · Pagination（0.25d · 2 子任务）

### ST-S5-D-09.1 写 `<Pagination>` 组件（0.125d）
- **V10 集成**：TanStack Table `getPaginationRowModel`

### ST-S5-D-09.2 写 story + 测试（0.125d）

---

## T-D-10 · EmptyState（0.25d · 2 子任务）

### ST-S5-D-10.1 写 `<EmptyState>` 组件（0.125d）
### ST-S5-D-10.2 写 story + 测试（0.125d）

---

## T-D-11 · Skeleton（0.25d · 2 子任务）

### ST-S5-D-11.1 写 `<Skeleton>` 组件（0.125d）
- **V10 集成**：与 design token 集成

### ST-S5-D-11.2 写 story + 测试（0.125d）

---

## T-D-12 · Avatar（0.25d · 2 子任务）

### ST-S5-D-12.1 写 `<Avatar>` 组件（0.125d）
- **V10 收益**：`@radix-ui/react-avatar`

### ST-S5-D-12.2 写 story + 测试（0.125d）

---

## T-D-13 · Stepper（0.5d · 3 子任务）

### ST-S5-D-13.1 写 `<Stepper>` 组件（0.25d）
- **V10 集成**：与 FormCard RHF 集成
- **V10 不变量 C3**：3-step guards 保持

### ST-S5-D-13.2 写动画（0.125d）

### ST-S5-D-13.3 写 story + 测试（0.125d）

---

## T-D-14 · Accordion（0.5d · 3 子任务）

### ST-S5-D-14.1 写 `<Accordion>` 组件（0.25d）
- **V10 收益**：`@radix-ui/react-accordion`

### ST-S5-D-14.2 写动画（0.125d）

### ST-S5-D-14.3 写 story + 测试（0.125d）

---

## T-D-15 · Storybook 配置 + dark story 全覆盖（1.5d · 5 子任务）⚠️ V10 关键

### ST-S5-D-15.1 安装 Storybook 8（0.25d）

### ST-S5-D-15.2 配置 Vite builder（0.25d）
- **V10 关键**：Storybook 用 Vite 构建，与生产一致

### ST-S5-D-15.3 写 18 组件 story（1.0d）
- **覆盖**：D-01 ~ D-14 共 14 个 + Sprint 1 5 个 = 19 个组件
- **每个 story**：default / dark / disabled / loading / error 5 态

### ST-S5-D-15.4 配置 Chromatic 集成（0d）
- **V10 关键**：每个 PR 自动截图

### ST-S5-D-15.5 部署到 Chromatic（0d）
- **命令**：`pnpm chromatic --project-token=xxx`

---

## T-D-16 · axe-core CI 集成（0.5d · 3 子任务）⚠️ V10 新增

> **PM 决策（2026-07-03）**：Chromatic 验收；axe-core 是其中关键

### ST-S5-D-16.1 安装 @axe-core/playwright（0.125d）

### ST-S5-D-16.2 写 a11y.spec（0.25d）
- **覆盖**：18 组件 + 8 页面
- **断言**：0 critical / 0 serious

### ST-S5-D-16.3 接入 CI（0.125d）
- **失败**：a11y 测试不通过 → 阻止合并

---

## V10 验收清单（Sprint 5 G5 闸门）

```
G5 闸门（必须全部通过）：
  [ ] 18 组件（含 Sprint 1 5 组件）Storybook dark story 全覆盖
  [ ] axe-core 0 critical 0 serious
  [ ] pnpm typecheck 0 error
  [ ] pnpm lint 0 error 0 warning
  [ ] pnpm test:storybook 全绿
  [ ] pnpm chromatic 视觉基线 19 组件 × 5 态全提交
  [ ] DataTable 万行数据 < 100ms 渲染
  [ ] Tree 千节点拖拽流畅
```

---

## V10 风险（Sprint 5 特有）

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| V10-S5-R1 | 第三方组件库（RHF/Radix）与原型 UI 风格冲突 | 中 | 用 design token 强制覆盖 |
| V10-S5-R2 | Storybook 与 Vite 集成问题 | 低 | Storybook 8 原生支持 Vite |
| V10-S5-R3 | axe-core 误报 | 低 | 优先级 critical/serious 强制；moderate 仅警告 |

---

**Sprint 5 文档状态**：V10 选项 B 重写完成
**总工时**：9 人天（V2 是 12 人天，节省 3d）
**总子任务**：47 个（V2 是 52 个）
**下一步**：Sprint 4 完成后立即启动
