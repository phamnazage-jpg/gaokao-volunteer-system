# Sprint 5 Progress · 2026-07-04

> **状态**：🚧 已启动非 Docker 后续任务，优先补齐不依赖新环境的基础 UI 完整性。
> **本轮范围**：T-D-01 DataTable、T-D-02 Tree、T-D-03 Chart、T-D-04 Modal、T-D-05 Toast、T-D-06 Tooltip、T-D-07 Select、T-D-08 DatePicker、T-D-09 Pagination、T-D-10 EmptyState、T-D-11 Skeleton、T-D-12 Avatar、T-D-13 Stepper、T-D-14 Accordion 的组件实现、页面接入与单测覆盖。
> **环境说明**：本机暂无 Docker，Sprint 4 的 T-C-44 本地镜像构建验证继续按环境阻塞处理。

---

## ✅ 本轮完成

| 任务 | 范围 | 状态 | 证据 |
|---|---|---|---|
| T-D-01 | `<DataTable>` 基础表格组件 | ✅ DONE | `apps/web/src/components/shared/DataTable.tsx` |
| T-D-01 | DataQuery 分数线表格替换接入 | ✅ DONE | `apps/web/src/pages/DataQueryPage.tsx` |
| T-D-01 | DataTable / DataQuery 回归单测 | ✅ DONE | `DataTable.test.tsx`, `DataQueryPage.test.tsx` |
| T-D-02 | `<Tree>` 基础树组件 | ✅ DONE | `apps/web/src/components/shared/Tree.tsx` |
| T-D-02 | About 能力地图树接入 | ✅ DONE | `apps/web/src/pages/AboutPage.tsx` |
| T-D-02 | Tree / About 回归单测 | ✅ DONE | `Tree.test.tsx`, `AboutPage.test.tsx` |
| T-D-03 | Line / Bar / Area / Pie 图表组件 | ✅ DONE | `apps/web/src/components/shared/Charts.tsx` |
| T-D-03 | DataQuery 分数线柱状图接入 | ✅ DONE | `apps/web/src/pages/DataQueryPage.tsx` |
| T-D-03 | Charts / DataQuery 回归单测 | ✅ DONE | `Charts.test.tsx`, `DataQueryPage.test.tsx` |
| T-D-04 | `<Modal>` 基础弹窗组件 | ✅ DONE | `apps/web/src/components/shared/Modal.tsx` |
| T-D-04 | DataQuery 数据口径说明弹窗接入 | ✅ DONE | `apps/web/src/pages/DataQueryPage.tsx` |
| T-D-04 | Modal / DataQuery 回归单测 | ✅ DONE | `Modal.test.tsx`, `DataQueryPage.test.tsx` |
| T-D-05 | `<Toast>` / `<Toaster>` 基础通知组件 | ✅ DONE | `apps/web/src/components/shared/Toast.tsx` |
| T-D-05 | 全局 Toaster 接入与 DataQuery 科类切换提示 | ✅ DONE | `apps/web/src/main.tsx`, `apps/web/src/pages/DataQueryPage.tsx` |
| T-D-05 | Toast / DataQuery 回归单测 | ✅ DONE | `Toast.test.tsx`, `DataQueryPage.test.tsx` |
| T-D-06 | `<Tooltip>` 基础提示组件 | ✅ DONE | `apps/web/src/components/shared/Tooltip.tsx` |
| T-D-06 | DataQuery 字段说明接入 | ✅ DONE | `apps/web/src/pages/DataQueryPage.tsx` |
| T-D-06 | Tooltip / DataQuery 回归单测 | ✅ DONE | `Tooltip.test.tsx`, `DataQueryPage.test.tsx` |
| T-D-07 | `<Select>` 基础选择器组件 | ✅ DONE | `apps/web/src/components/shared/Select.tsx` |
| T-D-07 | DataQuery 科类选择器接入 | ✅ DONE | `apps/web/src/pages/DataQueryPage.tsx` |
| T-D-07 | Select / DataQuery 回归单测 | ✅ DONE | `Select.test.tsx`, `DataQueryPage.test.tsx` |
| T-D-07 | `<Dropdown>` 基础菜单组件 | ✅ DONE | `apps/web/src/components/shared/Dropdown.tsx` |
| T-D-07 | HomePage 桌面快捷入口接入 | ✅ DONE | `apps/web/src/pages/HomePage.tsx` |
| T-D-07 | Dropdown / HomePage 回归单测 | ✅ DONE | `Dropdown.test.tsx`, `HomePage.test.tsx` |
| T-D-08 | `<DatePicker>` 原生日期选择组件 | ✅ DONE | `apps/web/src/components/shared/DatePicker.tsx` |
| T-D-08 | Consultations 更新时间筛选接入 | ✅ DONE | `apps/web/src/pages/ConsultationsPage.tsx` |
| T-D-08 | DatePicker / Consultations 回归单测 | ✅ DONE | `DatePicker.test.tsx`, `ConsultationsPage.test.tsx` |
| T-D-09 | `<Pagination>` 基础分页组件 | ✅ DONE | `apps/web/src/components/shared/Pagination.tsx` |
| T-D-09 | Plans / Consultations 客户端分页接入 | ✅ DONE | `PlansPage.tsx`, `ConsultationsPage.tsx` |
| T-D-09 | 分页组件与页面交互单测 | ✅ DONE | `Pagination.test.tsx`, `PlansPage.test.tsx`, `ConsultationsPage.test.tsx` |
| T-D-10 | `<EmptyState>` 基础空态组件 | ✅ DONE | `apps/web/src/components/shared/EmptyState.tsx` |
| T-D-10 | Plans / Consultations 空态接入 | ✅ DONE | `apps/web/src/pages/PlansPage.tsx`, `apps/web/src/pages/ConsultationsPage.tsx` |
| T-D-10 | 空态组件与页面单测 | ✅ DONE | `EmptyState.test.tsx`, `PlansPage.test.tsx`, `ConsultationsPage.test.tsx` |
| T-D-11 | `<Skeleton>` / `<CardListSkeleton>` 基础骨架屏组件 | ✅ DONE | `apps/web/src/components/shared/Skeleton.tsx` |
| T-D-11 | Plans / Consultations 加载态接入 | ✅ DONE | `PlansPage.tsx`, `ConsultationsPage.tsx` |
| T-D-11 | 骨架屏可访问性单测 | ✅ DONE | `Skeleton.test.tsx` |
| T-D-12 | `<Avatar>` 基础头像组件 | ✅ DONE | `apps/web/src/components/shared/Avatar.tsx` |
| T-D-12 | Consultations 列表头像接入 | ✅ DONE | `apps/web/src/pages/ConsultationsPage.tsx` |
| T-D-12 | Avatar / Consultations 回归单测 | ✅ DONE | `Avatar.test.tsx`, `ConsultationsPage.test.tsx` |
| T-D-13 | `<Stepper>` 基础步骤组件 | ✅ DONE | `apps/web/src/components/shared/Stepper.tsx` |
| T-D-13 | FormCard 步骤指示器抽取复用 | ✅ DONE | `apps/web/src/components/FormCard.tsx` |
| T-D-13 | Stepper / FormCard 回归单测 | ✅ DONE | `Stepper.test.tsx`, `FormCard.test.tsx` |
| T-D-14 | `<Accordion>` 基础折叠组件 | ✅ DONE | `apps/web/src/components/shared/Accordion.tsx` |
| T-D-14 | About 帮助页 FAQ 接入 | ✅ DONE | `apps/web/src/pages/AboutPage.tsx` |
| T-D-14 | Accordion / About 回归单测 | ✅ DONE | `Accordion.test.tsx`, `AboutPage.test.tsx` |

---

## ✅ 验证结果

| Gate | Command | Result |
|---|---|---|
| 新增单测 | `npm run test -- src/components/shared/Pagination.test.tsx src/components/shared/EmptyState.test.tsx src/components/shared/Skeleton.test.tsx src/pages/PlansPage.test.tsx src/pages/ConsultationsPage.test.tsx` | ✅ 5 files / 12 tests |
| TypeScript | `npm run typecheck` | ✅ PASS |
| ESLint | `npm run lint` | ✅ PASS |
| Codegen | `npm run codegen:check` | ✅ PASS |
| DataTable 回归 | `npm run test -- src/components/shared/DataTable.test.tsx src/pages/DataQueryPage.test.tsx` | ✅ 2 files / 7 tests |
| Tree 回归 | `npm run test -- src/components/shared/Tree.test.tsx src/pages/AboutPage.test.tsx` | ✅ 2 files / 4 tests |
| Chart 回归 | `npm run test -- src/components/shared/Charts.test.tsx src/pages/DataQueryPage.test.tsx` | ✅ 2 files / 7 tests |
| Modal 回归 | `npm run test -- src/components/shared/Modal.test.tsx src/pages/DataQueryPage.test.tsx` | ✅ 2 files / 5 tests |
| Toast 回归 | `npm run test -- src/components/shared/Toast.test.tsx src/pages/DataQueryPage.test.tsx` | ✅ 2 files / 6 tests |
| Tooltip 回归 | `npm run test -- src/components/shared/Tooltip.test.tsx src/pages/DataQueryPage.test.tsx` | ✅ 2 files / 2 tests |
| Select 回归 | `npm run test -- src/components/shared/Select.test.tsx src/pages/DataQueryPage.test.tsx` | ✅ 2 files / 5 tests |
| Dropdown 回归 | `npm run test -- src/components/shared/Dropdown.test.tsx src/pages/HomePage.test.tsx` | ✅ 2 files / 4 tests |
| DatePicker 回归 | `npm run test -- src/components/shared/DatePicker.test.tsx src/pages/ConsultationsPage.test.tsx` | ✅ 2 files / 6 tests |
| Avatar 回归 | `npm run test -- src/components/shared/Avatar.test.tsx src/pages/ConsultationsPage.test.tsx` | ✅ 2 files / 6 tests |
| Stepper 回归 | `npm run test -- src/components/shared/Stepper.test.tsx src/components/FormCard.test.tsx` | ✅ 2 files / 6 tests |
| Accordion 回归 | `npm run test -- src/components/shared/Accordion.test.tsx src/pages/AboutPage.test.tsx` | ✅ 2 files / 3 tests |

---

## ⏭️ 下一步候选

- T-D-15 Storybook / Chromatic：需要确认是否安装并启用 Storybook/Chromatic 配置与外部 token。
- T-C-44 Docker 构建验证：等待本机 Docker 可用后继续。
