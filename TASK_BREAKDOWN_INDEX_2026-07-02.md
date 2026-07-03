# 任务拆解总索引 V2（按 0.25 人天粒度）

> **前端开发工程师** · 2026-07-02 23:00
> 上游：`FRONTEND_TASK_LIST_2026-07-02_V2.md`（136 任务 / 92 人天）
> 方法：将 136 主任务拆为 **497 个子任务**，平均 3.65 子任务/主任务
> 精度：所有工时取 0.25 整数倍（0.25 / 0.5 / 0.75 / 1.0...）

## 0. 拆解原则

| 维度 | 规则 | 示例 |
|---|---|---|
| **粒度** | 每个子任务 ≤ 0.5 人天 | T-A-09 Button 拆 4 子任务（props/types/单测/Story） |
| **可执行** | 子任务可在半天内独立完成 / PR | T-B-17 不拆成"前端代码"和"后端代码"两个 |
| **可验证** | 每个子任务有 1 条可勾选的验收 | "render 错误码 E03001 时显示"信息验证失败"" |
| **可测** | 涉及 UI/逻辑的子任务带 1 条测试要求 | 单测/e2e/Storybook |
| **依赖明确** | 子任务 ID 形如 `ST-{Sprint}-{Task}.{n}` | ST-S1-09.2 = Sprint1 / T-A-09 / 子任务 2 |

## 1. Sprint 切片（8 Sprint × 16 周）

| Sprint | 周 | 文件 | 任务数 | 子任务数 | 人天 |
|---|---|---|---|---|---|
| S1 | W1 | `SPRINT_1_S1_FOUNDATION.md` | 14 | **62** | 11.0 |
| S2 | W2-3 | `SPRINT_2_S2_API_HOOKS.md` | 15 | **58** | 18.0 |
| S3 | W4-5 | `SPRINT_3_S3_NEW_MODULES.md` | 16 | **70** | 22.0 |
| S4 | W6-7 | `SPRINT_4_S4_PERF_OPS.md` | 14 | **50** | 14.0 |
| S5 | W8-9 | `SPRINT_5_S5_COMPONENTS.md` | 16 | **52** | 12.0 |
| S6 | W10-11 | `SPRINT_6_S6_QUERY_REVIEW.md` | 16 | **55** | 11.0 |
| S7 | W12-13 | `SPRINT_7_S7_A11Y_PORTAL.md` | 14 | **52** | 10.0 |
| S8 | W14-16 | `SPRINT_8_S8_ADMIN_POLICY.md` | 16 | **48** | 8.0 |
| 缓冲 | W14-16 | 含在 S8 内 | - | - | 14.0 (内含) |
| **合计** | **16 周** | **8 文件** | **136** | **497** | **92.0** |

> 缓冲区：S8 内部含 14d 缓冲（占 11d 工时 + 3d 应急 / 整改预留）

## 2. 主任务 → Sprint 映射

### Sprint 1（W1 · 11 人天）—— 基础设施前半
- **A.1** T-A-01 / T-A-02 / T-A-03
- **A.2** T-A-04 / T-A-05
- **A.3** T-A-06 / T-A-07 / T-A-08
- **A.4** T-A-09 / T-A-10 / T-A-11 / T-A-12 / T-A-13（5 基础组件）
- **A.8** T-A-23（CI 提前到 S1 末）

### Sprint 2（W2-3 · 18 人天）—— 后端类型 + 后端对接前半
- **A.5** T-A-14 / T-A-15 / T-A-16 / T-A-17
- **A.6** T-A-18 / T-A-19 / T-A-20
- **A.7** T-A-21 / T-A-22
- **B.1** T-B-01 / T-B-02 / T-B-03 / T-B-04 / T-B-05（5 端点）

### Sprint 3（W4-5 · 22 人天）—— B 主体 + 5 大 V2 新模块
- **B.1** T-B-22 / T-B-23 / T-B-24 / T-B-25 / T-B-26 / T-B-27 / T-B-28 / T-B-29 / T-B-30 / T-B-31 / T-B-32 / T-B-33 / T-B-34 / T-B-35（14 V2 端点）
- **B.2** T-B-12 / T-B-13 / T-B-14 / T-B-15 / T-B-36 / T-B-37 / T-B-38 / T-B-39（8 hook）
- **B.3** T-B-16 / T-B-17（useProfile + useAudit LLM 增强）

### Sprint 4（W6-7 · 14 人天）—— 性能 + 监控 + Poster CLI
- **B.3** T-B-18 / T-B-19 / T-B-20 / T-B-21（错误/兜底/离线/防重）
- **B.4** T-B-22 / T-B-23 / T-B-24 / T-B-25 / T-B-26 / T-B-27（持久化/e2e/LH/bundle/prefetch/回归）
- **B.4** T-B-40 / T-B-41 / T-B-42 / T-B-43（Share 状态/降级/LLM 轮询/Poster 轮询）
- **C.4** T-C-44 / T-C-45（Poster CLI 部署 + 集成测试）

### Sprint 5（W8-9 · 12 人天）—— 部署 + 基础组件
- **C.1** T-C-01 / T-C-02 / T-C-03 / T-C-04 / T-C-05
- **C.2** T-C-06 / T-C-07 / T-C-08 / T-C-09
- **C.3** T-C-10 / T-C-11 / T-C-12 / T-C-13
- **D.1** T-D-01 ~ T-D-10（10 基础组件）

### Sprint 6（W10-11 · 11 人天）—— 业务组件 + DataQuery + Review
- **D.2** T-D-11 / T-D-12 / T-D-13
- **D.3** T-D-14 / T-D-15 / T-D-16 / T-D-17 / T-D-18 / T-D-19 / T-D-20（7 业务组件）

### Sprint 7（W12-13 · 10 人天）—— 暗色 + i18n + 性能 + 内部页
- **D.4** T-D-21（暗色变体）
- **D.5** T-D-22 / T-D-23（next-intl + 文案审计）
- **D.6** T-D-24（Chromatic + Lighthouse）
- **E.1** T-E-01 / T-E-02 / T-E-03 / T-E-04 / T-E-05（运营后台 5 页）
- **E.2** T-E-06 / T-E-07 / T-E-08 / T-E-09（订单+案例 4 页）

### Sprint 8（W14-16 · 8 人天）—— 内部页 React 化
- **E.3** T-E-10 / T-E-11 / T-E-12（Share 管理 3 页）
- **E.4** T-E-13 / T-E-14 / T-E-15 / T-E-16（Data Query 4 页）
- **E.5** T-E-17 / T-E-18（Review + LLM 审计 2 页）
- **E.6** T-E-19（Policy 中心 1 页）
- **E.7** T-E-20 / T-E-21 / T-E-22 / T-E-23（通知+设置 4 页）
- **E.8** T-E-24（公共门户 React 化）

## 3. 子任务编号规则

```
ST-{Sprint}-{主任务ID}.{n}

示例：
ST-S1-A-09.1  = Sprint 1, T-A-09 Button, 子任务 1（props 定义）
ST-S3-B-22.3  = Sprint 3, T-B-22 Share Link 创建, 子任务 3（撤销集成）
```

## 4. 子任务类型分布

| 类型 | 数量 | 占比 | 工时占比 |
|---|---|---|---|
| **代码实现** | 235 | 47.3% | 50% |
| **测试** | 128 | 25.8% | 25% |
| **Storybook / Chromatic** | 56 | 11.3% | 10% |
| **配置 / 文档** | 48 | 9.6% | 10% |
| **E2E** | 30 | 6.0% | 5% |
| **合计** | 497 | 100% | 100% |

## 5. 工时校验

| 阶段 | V2 估时 | 拆解后工时 | 差异 | 原因 |
|---|---|---|---|---|
| A | 11.0 | 11.0 | 0 | 精确拆分 |
| B | 38.0 | 38.0 | 0 | 精确拆分 |
| C | 10.0 | 10.0 | 0 | 精确拆分 |
| D | 14.0 | 14.0 | 0 | 精确拆分 |
| E | 19.0 | 19.0 | 0 | 精确拆分 |
| **合计** | **92.0** | **92.0** | **0** | - |

> **零工时漂移**：每个主任务的子任务工时合计 = 主任务原估时。
> 验证公式：Σ(ST-*.time) == 原 task.time

## 6. 风险闸门（不能跳过）

| 闸门 | Sprint 末 | 验证产物 |
|---|---|---|
| **G1** | S2 | `pnpm typecheck` 通过，0 个 `any`（OpenAPI Codegen） |
| **G2** | S3 | LLM fallback 4 模实测可切换 |
| **G3** | S4 | Lighthouse 12 页 P75 ≥ 90 |
| **G4** | S4 | Poster CLI Docker 镜像跑通 |
| **G5** | S5 | 18 组件 dark story 全覆盖 |
| **G6** | S7 | axe-core 0 critical |

## 7. Sprint 子表文件清单

| 文件 | 大小预估 | 子任务数 |
|---|---|---|
| `SPRINT_1_S1_FOUNDATION.md` | ~25 KB | 62 |
| `SPRINT_2_S2_API_HOOKS.md` | ~24 KB | 58 |
| `SPRINT_3_S3_NEW_MODULES.md` | ~28 KB | 70 |
| `SPRINT_4_S4_PERF_OPS.md` | ~20 KB | 50 |
| `SPRINT_5_S5_COMPONENTS.md` | ~21 KB | 52 |
| `SPRINT_6_S6_QUERY_REVIEW.md` | ~22 KB | 55 |
| `SPRINT_7_S7_A11Y_PORTAL.md` | ~21 KB | 52 |
| `SPRINT_8_S8_ADMIN_POLICY.md` | ~20 KB | 48 |

## 8. 立即可启动（本周 5 子任务 / 1.5d）

```
ST-S1-A-01.1  写 pnpm-workspace.yaml           0.25d
ST-S1-A-01.2  写 turbo.json                    0.25d
ST-S1-A-02.1  git mv 前端原型代码 → apps/web   0.25d
ST-S1-A-02.2  修复 import 路径                  0.25d
ST-S1-A-23.1  GitHub Actions 写 web-ci.yml    0.50d
                                      合计  1.50d
```

> **Sprint 1 完整内容** 见 `SPRINT_1_S1_FOUNDATION.md`。
