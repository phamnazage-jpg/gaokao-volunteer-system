# Batch 1 审计收敛执行板（2026-06-16）

真相源输入：

1. `docs/plans/2026-06-16-optimization-program.md`
2. `docs/CURRENT_STATE.md`
3. Batch 1-A/B/C/D 审计结论（主代理复核）

---

## 一、Batch 1 总结论

四条优化线里，**最该先做的不是 CLI，而是“规则可信 + 专业数据可信”**。

当前项目的主要风险顺序：

### P0

1. **规则规范可信度不足**
   - 当前 `skills/gaokao-spec-checker/scripts/spec_checker_v2.py` 内置了 27 省规则字典，但证据链主要是手工编码规则 + 官方 URL 字段；缺“2026 年规则来源快照 / 更新时间 / 逐省证据状态”。
   - 当前能做“规范检查”，但还不能对外稳妥宣称“已具备可追溯的 2026 各省官方规则验证能力”。

2. **专业目录真相源缺失**
   - 当前仓库里**没有 2026 官方专业目录数据集**。
   - 也没有“近两年高校新增/取消专业”的正式接入层。
   - 这会直接导致方案建议与审计结果可能引用过时专业。

### P1

3. **CLI 能力分散且偏脚本化**
   - 已有 CLI/脚本很多，但主要是：`gaokao-checker`、`gaokao-collect-info.py`、`gaokao-visual-report-v2.py`、`gaokao-shortlink`、备份/运维脚本。
   - **没有统一的“客服/运营/智能体调用层”**，尤其缺 create-order / get-order / list-orders / run-audit / generate-report 这一套正式命令面。

4. **规划 / 实现漂移明显**
   - README / PRD / ROADMAP / CURRENT_STATE / 架构文档 / 代码实现之间有多处口径漂移。
   - 其中最严重的是：
     - Web 自助主链代码已大量落地，但文档仍长期按“未完成”叙述
     - PRD 套餐价格/档位与代码实现不一致
     - 状态机设计与实现路线未落锤

---

## 二、四条线收敛结论

### A. 规则规范线

**已知现状**

- 规则检查核心入口：
  - `scripts/gaokao-checker`
  - `skills/gaokao-spec-checker/scripts/spec_checker_v2.py`
- 已有 27 省规则字典
- 有多省自动识别能力
- 有测试覆盖 `tests/test_coverage_gate_core.py`、`tests/test_all.py`

**缺口**

- 缺 2026 规则证据矩阵
- 缺“全国通用规则”抽象层文档与结构化表达
- 缺规则版本化与更新时间字段

**判断**

- 能做“规范检查工具”
- 但还不够“2026 官方规则可信审计系统”

---

### B. 专业目录数据线

**已知现状**

- 当前仓库没有正式的 2026 官方专业目录数据真相源
- 没有教育部目录 + 高校招生专业变更的统一接入层
- 推荐/报告/审计逻辑会消费专业名，但缺版本化目录底座

**缺口**

- 没有 `major catalog` 数据模型
- 没有官方/准官方数据导入流程
- 没有近两年专业增减风险标记

**判断**

- 这是当前项目最核心的数据风险之一
- 应与规则规范线并列最高优先级

---

### C. CLI 能力线

**已知现状**

- 当前已有 CLI/脚本入口：
  - `scripts/gaokao-checker`
  - `scripts/gaokao-collect-info.py`
  - `scripts/gaokao-visual-report-v2.py`
  - `scripts/gaokao-shortlink`
  - `scripts/payment_provider_doctor.py`
  - `scripts/gaokao-delivery-dispatch.py`
  - `scripts/gaokao-delivery-watchdog.py`
  - `scripts/gaokao-retention-cleanup.py`
  - `scripts/backup_snapshot.sh`
  - `scripts/backup_verify.sh`
- 后台 API 已有可被 CLI 包装的能力：
  - auth
  - orders
  - users
  - stats
  - notifications
  - public orders / portal 链路

**缺口**

- 没有统一 `gaokao-cli` 命令面
- 没有客服/运营最小权限命令集
- 没有“脚本 vs 正式 CLI vs HTTP wrapper”分层规范

**判断**

- CLI 适合做成第二批实现
- 前提是先把规则/专业数据底座定下来

---

### D. 规划 / 实现优化线

**已知现状**

- 漂移点已明确：
  - 项目定位文档 vs Web 自助实现状态
  - PRD SKU/价格 vs 实现
  - 状态机计划 vs 实现
  - README 目录图 vs 实际目录
  - 双架构文档并存
- 这不是代码 bug，而是**真相源治理问题**

**判断**

- 不先收敛真相源，后面的规则/专业/CLI 做出来也会继续漂
- 但它不该优先于规则/专业数据本身

---

## 三、建议优先级（执行顺序）

### Batch 2（建议立即启动）

#### Lane 1 - 规则规范可信化（P0）

目标：把当前“可检查”提升为“可追溯的 2026 规则检查”。

交付物：

- `docs/CURRENT_RULES_STATE_2026-06-16.md`
- `docs/RULES_SOURCE_OF_TRUTH.md`
- `docs/plans/rules-2026-gap-remediation.md`

实现重点：

- 逐省规则证据矩阵
- 全国通用规则抽象
- 规则版本字段 / 更新时间字段
- 统一审计入口整理

#### Lane 2 - 专业目录可信化（P0）

目标：建立 2026 专业目录真相源与变更风险模型。

交付物：

- `docs/MAJOR_DATA_SOURCE_OF_TRUTH.md`
- `docs/MAJOR_DATA_RISK_MATRIX_2026.md`
- `docs/plans/major-catalog-2026-ingestion.md`

实现重点：

- 国家级目录 vs 高校招生专业分层
- 数据结构设计
- 更新策略（年度全量 + 差异更新）
- 高风险专业变更标记

### Batch 3（规则/专业方案出来后）

#### Lane 3 - CLI 能力面（P1）

建议最小命令集：

- `create-order`
- `get-order`
- `list-orders`
- `run-audit`
- `generate-report`
- `create-shortlink`
- `payment-doctor`

#### Lane 4 - 真相源与规划收敛（P1）

重点：

- SKU/价格统一
- 状态机决策落锤
- README/ROADMAP/PRD/CURRENT_STATE 对齐
- 双架构文档收敛

---

## 四、推荐子智能体分工（下一轮实现）

### Agent-A（规则规范）

- 先产出规则证据矩阵
- 再补统一规则模型与审计入口方案

### Agent-B（专业目录）

- 先产出专业数据真相源方案
- 再定义数据模型与接入策略

### Agent-C（CLI）

- 不立刻写实现
- 先做命令契约与权限边界设计
- 等 A/B 收敛后再落地 CLI

### Agent-D（规划/真相源）

- 先收敛 SKU / 状态机 / README / CURRENT_STATE 漂移
- 作为 A/B/C 的公共文档治理支撑

---

## 五、当前建议

**建议下一步直接启动 Batch 2，但只开两条实现线：**

1. 规则规范可信化
2. 专业目录可信化

同时让规划/真相源线做轻量配套收敛；CLI 暂不重实现，只先出契约设计。

这样能避免：

- 先做 CLI，后面数据模型再返工
- 先做规划文档，结果没有真实数据底座支撑
- 规则和专业目录口径继续分裂
