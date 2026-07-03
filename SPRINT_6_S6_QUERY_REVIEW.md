# Sprint 6 任务拆解（W10-11 · 12 人天 · 56 子任务）— V10 选项 B

> **技术栈**：Vite 5 + React 19 + Zustand 4 + TanStack Query 5 + RHF 7 + Zod
> **目标**：查询/审核业务 UI（SharePanel / DataQueryForm / ReviewFlow / LLMEnhancement / PosterPreview）
> **闸门**：G6（视觉一致性 design pass + Chromatic 0 像素 diff）
> **V10 变化**：保持 12d（S6 是业务密集型，工时难压）
> **PM 决策（2026-07-03）**：整体重写为新实现；Playwright 视觉回归 + Chromatic 验收

---

## ⚠️ V10 关键变化（与 V2 对比）

| 维度 | V2 | V10 选项 B |
|---|---|---|
| DataQueryForm 4 变体 | 1.0d | **1.0d**（不变） |
| DataQueryResult 4 变体 | 1.0d | **1.0d**（不变） |
| 业务组件库 | 7 | 7（不变） |
| a11y 集成 | S6 末 | **S5 已完成**，S6 复用 |
| 总估时 | 11d | **12d**（略增：加 1d Chromatic 验证） |

---

## 0. Sprint 6 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-D-11 | axe-core 集成（复用 S5） | 0d | 0 |
| T-D-12 | 屏幕阅读器 + 键盘测试 | 0.5d | 3 |
| T-D-13 | 替换 alert() 为 Toast | 0.25d | 2 |
| T-D-14 | SharePanel 组件 | 0.75d | 5 |
| T-D-15 | ShareStatusPanel 组件 | 0.5d | 4 |
| T-D-16 | DataQueryForm（4 变体） | 1.0d | 6 |
| T-D-17 | DataQueryResult（4 变体） | 1.0d | 6 |
| T-D-18 | ReviewFlow 组件 | 0.75d | 4 |
| T-D-19 | LLMEnhancement 组件 | 0.75d | 4 |
| T-D-20 | PosterPreview 组件 | 0.5d | 4 |
| T-D-21 | 暗色变体审计 | 1.0d | 4 |
| T-D-22 | Chromatic 视觉回归（S6 增量） | 1.0d | 4 |
| T-D-23 | ESLint 0 warning 守门 | 0.5d | 3 |
| **合计** | **13 任务（含 1 复用）** | **9.5d + 缓冲 2.5d = 12d** | **49** |

---

## T-D-11 · axe-core 集成（复用 S5 · 0d · 0 子任务）

> **V10 收益**：Sprint 5 已集成，S6 直接复用

---

## T-D-12 · 屏幕阅读器 + 键盘测试（0.5d · 3 子任务）

### ST-S6-D-12.1 VoiceOver 测试（0.25d）
- **覆盖**：5 业务组件关键路径

### ST-S6-D-12.2 NVDA 测试（0.125d）

### ST-S6-D-12.3 键盘导航测试（0.125d）
- **覆盖**：Tab / Shift+Tab / Enter / Esc / 方向键

---

## T-D-13 · 替换 alert() 为 Toast（0.25d · 2 子任务）

### ST-S6-D-13.1 grep + 替换（0.125d）
- **命令**：`grep -rn "alert(" apps/web/src/`
- **替换**：`toast.error(message)` / `toast.success(message)`

### ST-S6-D-13.2 验证无 alert() 残留（0.125d）

---

## T-D-14 · SharePanel 组件（0.75d · 5 子任务）

### ST-S6-D-14.1 写组件骨架（0.25d）
- **V10 集成**：RHF + Zod
- **UI/交互 1:1**：与原型分享面板一致

### ST-S6-D-14.2 写表单字段（0.125d）
- 分享链接有效期（7/30/永久）
- 访问密码
- 备注

### ST-S6-D-14.3 接入 `useShareLinkCreate`（0.125d）
### ST-S6-D-14.4 写 story（0.125d）
### ST-S6-D-14.5 写 e2e（0.125d）

---

## T-D-15 · ShareStatusPanel 组件（0.5d · 4 子任务）

### ST-S6-D-15.1 写 3 统计卡片（0.125d）
### ST-S6-D-15.2 写访问趋势 mini chart（0.125d）
### ST-S6-D-15.3 写 story（0.125d）
### ST-S6-D-15.4 写 e2e（0.125d）

---

## T-D-16 · DataQueryForm（4 变体 · 1.0d · 6 子任务）

### ST-S6-D-16.1 写 scoreLine 变体（0.125d）
- **字段**：省份 / 年份 / 类型

### ST-S6-D-16.2 写 rankEstimator 变体（0.125d）
- **字段**：位次 / 选科 / 年份

### ST-S6-D-16.3 写 majors 变体（0.125d）
- **字段**：专业类 / 学历 / 院校

### ST-S6-D-16.4 写 schools 变体（0.125d）
- **字段**：院校 / 省份 / 类型

### ST-S6-D-16.5 接入 TanStack Query mutations（0.25d）
- **V10 收益**：4 变体复用同一表单骨架

### ST-S6-D-16.6 写 story（0.25d）

---

## T-D-17 · DataQueryResult（4 变体 · 1.0d · 6 子体）

### ST-S6-D-17.1 写 scoreLine 变体（0.125d）
- **展示**：分数段分布表 + chart

### ST-S6-D-17.2 写 rankEstimator 变体（0.125d）
- **展示**：等效分数 + 院校推荐

### ST-S6-D-17.3 写 majors 变体（0.125d）
- **展示**：专业列表 + 院校

### ST-S6-D-17.4 写 schools 变体（0.125d）
- **展示**：院校卡片

### ST-S6-D-17.5 接入虚拟滚动（0.25d）
- **V10 收益**：TanStack Virtual 万行流畅

### ST-S6-D-17.6 写 story（0.25d）

---

## T-D-18 · ReviewFlow 组件（0.75d · 4 子任务）

### ST-S6-D-18.1 写审核步骤指示器（0.25d）
- **V10 集成**：复用 S5-D-13 Stepper

### ST-S6-D-18.2 写审核表单（RHF 版 · 0.25d）
- **字段**：审批意见 / 风险等级 / 备注

### ST-S6-D-18.3 接入 useReview* hooks（0.125d）
### ST-S6-D-18.4 写 story + e2e（0.125d）

---

## T-D-19 · LLMEnhancement 组件（0.75d · 4 子任务）

### ST-S6-D-19.1 写 Provider 选择器（0.25d）
- **V10 集成**：复用 T-B-17 LLM provider

### ST-S6-D-19.2 写流式结果展示（0.25d）
- **V10 集成**：SSE + Markdown 渲染

### ST-S6-D-19.3 接入 useAuditEnhanceMutation（0.125d）
### ST-S6-D-19.4 写 story + e2e（0.125d）

---

## T-D-20 · PosterPreview 组件（0.5d · 4 子任务）

### ST-S6-D-20.1 写海报渲染（0.125d）
- **V10 集成**：html2canvas

### ST-S6-D-20.2 写 QR Code 嵌入（0.125d）
### ST-S6-D-20.3 接入 usePosterGenerateMutation（0.125d）
### ST-S6-D-20.4 写 story + e2e（0.125d）

---

## T-D-21 · 暗色变体审计（1.0d · 4 子任务）⚠️ V10 关键

### ST-S6-D-21.1 截图所有 7 业务组件 dark mode（0.25d）

### ST-S6-D-21.2 Chromatic diff 检测（0.25d）
- **验收**：0 像素 diff

### ST-S6-D-21.3 修复对比度问题（0.25d）
- **目标**：WCAG AA（4.5:1）

### ST-S6-D-21.4 提交 Chromatic 基线（0.25d）

---

## T-D-22 · Chromatic 视觉回归（S6 增量 · 1.0d · 4 子任务）⚠️ V10 新增

### ST-S6-D-22.1 7 业务组件 × 3 主题（0.25d）
- light / dark / system × 7 组件 = 21 截图

### ST-S6-D-22.2 移动端 viewport（0.25d）
- 375px / 768px / 1024px × 7 组件 = 21 截图

### ST-S6-D-22.3 交互态截图（0.25d）
- hover / focus / active / disabled / loading / error

### ST-S6-D-22.4 提交基线（0.25d）

---

## T-D-23 · ESLint 0 warning 守门（0.5d · 3 子任务）

### ST-S6-D-23.1 清理 S6 引入的 any（0.25d）
### ST-S6-D-23.2 清理 S6 引入的 unused（0.125d）
### ST-S6-D-23.3 守住 Sprint 1-5 已修复规则（0.125d）

---

## V10 验收清单（Sprint 6 G6 闸门）

```
G6 闸门（必须全部通过）：
  [ ] 7 业务组件全部完成 + story 全覆盖
  [ ] axe-core 0 critical 0 serious
  [ ] pnpm typecheck 0 error 0 any
  [ ] pnpm lint 0 error 0 warning
  [ ] pnpm test:storybook 全绿
  [ ] pnpm chromatic 视觉基线 7 组件 × 3 主题 × 3 viewport × 6 态 = 378 截图
  [ ] WCAG AA 对比度全通过
  [ ] DataQueryForm 万行结果 < 200ms 渲染
```

---

## V10 风险（Sprint 6 特有）

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| V10-S6-R1 | 4 变体 DataQueryForm 代码重复 | 中 | 提取 `<QueryForm variant=...>` 单一组件 |
| V10-S6-R2 | 暗色变体对比度不达标 | 中 | 用 design token 强制；S6-D-21 强制审计 |
| V10-S6-R3 | Chromatic 配额超限 | 低 | 累计 S2-S5 用 4 次，剩 6 次给 S6-S8 |

---

**Sprint 6 文档状态**：V10 选项 B 重写完成
**总工时**：12 人天（V2 是 11 人天，+1d Chromatic 验证）
**总子任务**：49 个（V2 是 55 个）
**下一步**：Sprint 5 完成后立即启动
