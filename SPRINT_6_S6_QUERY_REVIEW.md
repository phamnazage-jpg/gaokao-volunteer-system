# Sprint 6 任务拆解（W10-11 · 11 人天 · 55 子任务）

> **主任务**：T-D-11 ~ T-D-20
> **目标**：a11y + 7 业务组件（Share / DataQuery / Review / LLMEnhancement / Poster）
> **闸门**：G6（视觉一致性 design pass）

## 0. Sprint 6 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-D-11 | axe-core 集成 | 0.5d | 3 |
| T-D-12 | 屏幕阅读器 + 键盘测试 | 1.0d | 4 |
| T-D-13 | 替换 alert() 为 Toast | 0.5d | 3 |
| T-D-14 | 🆕 SharePanel 组件 | 0.75d | 5 |
| T-D-15 | 🆕 ShareStatusPanel 组件 | 0.5d | 4 |
| T-D-16 | 🆕 DataQueryForm（4 变体） | 1.0d | 6 |
| T-D-17 | 🆕 DataQueryResult（4 变体） | 1.0d | 6 |
| T-D-18 | 🆕 ReviewFlow 组件 | 0.5d | 4 |
| T-D-19 | 🆕 LLMEnhancement 组件 | 0.5d | 4 |
| T-D-20 | 🆕 PosterPreview 组件 | 0.5d | 4 |
| T-D-21（提前） | 暗色变体审计 | 1.5d | 5 |
| **合计** | **11 任务** | **8.25d + 缓冲 2.75d = 11d** | **55** |

> 注：D.4 暗色审计提前到 S6 末启动，给 S7 留 1 天收口

---

## D.2 a11y 全量审计（3 任务 · 10 子任务 · 2d）

### T-D-11 · axe-core 集成（0.5d · 3 子任务）
- ST-S6-D-11.1 接入 `@axe-core/playwright`（0.25d）
- ST-S6-D-11.2 扩展到 12 个页面自动扫描（0.125d）
- ST-S6-D-11.3 CI 卡点（0.125d）
- **验收**：
  - [ ] 0 critical / 0 serious 违规

### T-D-12 · 屏幕阅读器 + 键盘测试（1.0d · 4 子任务）
- ST-S6-D-12.1 NVDA 测试（0.25d）
- ST-S6-D-12.2 VoiceOver 移动端测试（0.25d）
- ST-S6-D-12.3 Tab 顺序测试（0.25d）
- ST-S6-D-12.4 Skip link 验证（0.25d）
- **产出**：`docs/A11Y_TEST_2026-XX.md`

### T-D-13 · 替换 alert() 为 Toast（0.5d · 3 子任务）
- ST-S6-D-13.1 `plans/[id]/page.tsx:143,152` 替换（0.25d）
- ST-S6-D-13.2 异步下载（`URL.createObjectURL` + `<a download>`）（0.125d）
- ST-S6-D-13.3 写 e2e（0.125d）
- **约束**：**R-NEW-4 应对**
- **验收**：
  - [ ] 导出图片 / PDF 真实下载
  - [ ] Toast 提示"已导出方案 / 导出失败"

---

## D.3 业务组件扩展（7 任务 · 33 子任务 · 4.25d）

### T-D-14 · 🆕 SharePanel 组件（0.75d · 5 子任务）
- ST-S6-D-14.1 写 `<SharePanel resourceType resourceId />`（0.25d）
- ST-S6-D-14.2 创建 / 链接展示 / QR / 复制 / 撤销 5 状态（0.125d）
- ST-S6-D-14.3 复用 T-B-36 useShareLink（0.125d）
- ST-S6-D-14.4 Vitest 4 状态全覆盖（0.125d）
- ST-S6-D-14.5 Storybook 4 故事（0.125d）
- **验收**：
  - [ ] 视觉与原型一致（沿用 Card + Badge）

### T-D-15 · 🆕 ShareStatusPanel 组件（0.5d · 4 子任务）
- ST-S6-D-15.1 写 `<ShareStatusPanel resourceId />`（0.25d）
- ST-S6-D-15.2 复用 T-B-40 useShareStatusPanel（0.0625d → 0d）
- ST-S6-D-15.3 30s 自动刷新（0.125d）
- ST-S6-D-15.4 test_share_status_panel.py 通过（0.125d）
- **依据**：commit `0145d66` 提到 test_share_status_panel.py 期望但当前未通过

### T-D-16 · 🆕 DataQueryForm 组件（4 变体，1.0d · 6 子任务）
- ST-S6-D-16.1 写 `QueryForm` 抽象基类（0.25d）
- ST-S6-D-16.2 `ScoreLineQueryForm`（0.125d）
- ST-S6-D-16.3 `RankEstimatorForm`（0.125d）
- ST-S6-D-16.4 `MajorsQueryForm`（0.125d）
- ST-S6-D-16.5 `SchoolsQueryForm`（0.125d）
- ST-S6-D-16.6 Vitest + Storybook（0.25d）
- **验收**：
  - [ ] 4 form 复用同一 QueryForm 框架

### T-D-17 · 🆕 DataQueryResult 组件（4 变体，1.0d · 6 子任务）
- ST-S6-D-17.1 写 `QueryResult` 框架（loading/empty/error/data 4 态）（0.25d）
- ST-S6-D-17.2 `ScoreLineResult`（表格 + 分数段分布图）（0.125d）
- ST-S6-D-17.3 `RankEstimatorResult`（大数字 + 历史趋势）（0.125d）
- ST-S6-D-17.4 `MajorsResult`（列表 + 分类）（0.125d）
- ST-S6-D-17.5 `SchoolsResult`（列表 + 985/211 标签）（0.125d）
- ST-S6-D-17.6 Vitest + Storybook（0.25d）
- **验收**：
  - [ ] 4 态切换动画

### T-D-18 · 🆕 ReviewFlow 组件（0.5d · 4 子任务）
- ST-S6-D-18.1 写 `<ReviewFlow planId />`（0.125d）
- ST-S6-D-18.2 状态机 `idle → started → analyzing → completed | failed | revision_needed`（0.125d）
- ST-S6-D-18.3 进度条实时更新 + 失败重试（0.125d）
- ST-S6-D-18.4 Vitest + Storybook（0.125d）
- **验收**：
  - [ ] 复用 T-B-38 useReview

### T-D-19 · 🆕 LLMEnhancement 组件（0.5d · 4 子任务）
- ST-S6-D-19.1 写 `<LLMEnhancement auditReportId type />`（0.125d）
- ST-S6-D-19.2 异步加载（不阻塞主审核结果）（0.125d）
- ST-S6-D-19.3 失败降级 + "由 XXX 模型生成"标注（0.125d）
- ST-S6-D-19.4 Vitest + Storybook（0.125d）

### T-D-20 · 🆕 PosterPreview 组件（0.5d · 4 子任务）
- ST-S6-D-20.1 写 `<PosterPreview planId template />`（0.125d）
- ST-S6-D-20.2 3 模板切换 + 实时预览（0.125d）
- ST-S6-D-20.3 下载按钮（0.125d）
- ST-S6-D-20.4 Vitest + Storybook（0.125d）

---

## D.4 暗色变体审计（提前到 S6 末，1.5d · 5 子任务）

### T-D-21 · 暗色变体审计（1.5d · 5 子任务）
- ST-S6-D-21.1 18+ 组件 dark story 补全（0.5d）
  - Button / Input / Select / Textarea / Card / Badge / Tabs
  - Dialog / Toast / Tooltip / Dropdown / Avatar / Skeleton / ProgressBar / Switch / Checkbox / Radio
  - + 7 业务组件：SharePanel / ShareStatusPanel / DataQueryForm×4 / DataQueryResult×4 / ReviewFlow / LLMEnhancement / PosterPreview
- ST-S6-D-21.2 视觉切换无白边（0.25d）
- ST-S6-D-21.3 风险徽章 / 概率条 / 模式指示器 暗色语义色保持（0.25d）
- ST-S6-D-21.4 对比度 < 4.5:1 修复（0.25d）
- ST-S6-D-21.5 Chromatic visual diff 验证（0.25d）

---

## Sprint 6 收口验收

- [ ] 11 主任务 / 55 子任务全部完成
- [ ] **G6 通过**：视觉一致性 design pass
- [ ] axe-core 12 页面 0 critical
- [ ] 18+ 组件 dark story 完整
- [ ] 7 V2 业务组件全绿
- [ ] 进入 Sprint 7 前 commit：`<feat(s6): a11y+7 business components+dark audit>`
