<!-- 历史快照提示：本文件保留为历史审计材料，不再代表当前项目状态。 -->
> ⚠️ **历史快照（非当前真相源）**：本文件仅保留当时审查/收口结论。当前状态与执行顺序以 `docs/CURRENT_STATE.md`、`docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`、`docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`、`docs/plans/2026-07-05-review-remediation-systemic-fix-plan.md` 和 `reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md` 为准。

---

# 生产上线严格复审报告（当前真相版）

- 项目：`/home/long/project/gaokao-volunteer-system`
- 复审日期：2026-06-19
- 复审目标：按生产上线要求复核昨天 strict review 之后的当前真实状态，剔除已修复项，只保留当前仍有效的上线问题。
- 复审依据：
  - `docs/CURRENT_STATE.md`
  - `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md`
  - `scripts/dev-verify.sh`
  - `.github/workflows/ci.yml`
  - 当前主干代码与本轮实跑结果

---

## 1. 结论

**状态**：本地验证完成，未达到生产上线质量要求。

**最短结论**：

1. 代码门禁已显著提升，当前 `dev-verify` 可真实通过：`1172 passed`，`coverage gate summary: overall=85.10%, core=100.00%`。
2. 昨日 strict review 中的大部分高危问题已在后续 commit 收口：
   - WAL SQLite 恢复校验
   - coverage 口径失真
   - 后台角色授权缺失
   - 订单报告路径任意文件读取
   - portal token 直接透传支付 URL
   - retention 未清理 `delivery_notifications.payload_json`
3. 但**当前仍有 4 类问题阻止按“生产可上线”对外表述**：
   - **P0 文档真相漂移**：PRD / ROADMAP 仍把 Web 自助售卖链与 AI 审核覆盖面写得过满，容易误导为“已是完整 Web 自助产品”
   - **P0 合规删除门禁缺失**：删除/匿名化没有保留期/审计期代码门禁
   - **P1 支付失败状态机未闭环**：失败 webhook 没有持久化 `failed` 状态
   - **P1 当前真相源未更新**：`CURRENT_STATE` / 执行板仍停留在 6/17 口径，没有吸收 6/18-6/19 的真实修复与剩余问题

因此，**当前真实结论是：可继续作为本地/受控试运行版本，不可宣称生产上线完成。**

---

## 2. 本轮直接验证证据

### 2.1 统一门禁

执行：

```bash
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

本轮结果（摘录）：

- `1172 passed, 6 warnings in 87.54s`
- `coverage gate summary: overall=85.10%, core=100.00%`
- `ruff: All checks passed!`
- `mypy: Success: no issues found in 225 source files`

### 2.2 当前代码直接核对

已直接核对关键实现：

- `admin/auth.py`：存在 `require_role(*allowed_roles)`
- `admin/routes/orders.py`：订单列表/导出/详情/创建等高权限接口已挂 `Depends(require_role("admin"))`
- `admin/routes/orders.py`：`audit_report/pdf_path/plan_file` 已走 `_validate_report_artifact_path()`
- `admin/routes/web_public.py`：portal 支付回跳已改为 `/portal/{token}/payment-success`，不再用 `?token=`
- `scripts/check_coverage_gate.py`：已忽略 `tests/`、`admin/tests/`、`docs/`
- `scripts/backup_verify.sh`：live SQLite staging 已改用 `sqlite3.backup()`

### 2.3 当前仍未闭环的代码事实

#### A. 删除/匿名化缺保留期门禁

直接搜索：

- 在 `data/orders/*.py` 未找到 `retention_until` / `retain_until` / 删除拒绝门禁相关实现
- `data/orders/deletion_service.py` 的 `delete_order()` / `anonymize_order()` 仅做存在性检查、文件删除、数据清空、审计落库，**没有任何保留期/支付审计期阻断逻辑**

#### B. 失败支付状态未持久化

`data/payments/service.py` 当前逻辑：

- `normalized_status not in {"paid", "TRADE_SUCCESS", "TRADE_FINISHED"}` 时直接 `raise PaymentError("payment status not successful")`
- 没有把 payment 记录更新为 `failed`

#### C. 文档仍会误导上线判断

本轮直接复核到的关键残留：

- `README.md` 顶部口径是正确的，但正文仍以产品能力介绍为主，容易盖过“非完整 Web 自助产品”的限制
- `product/PRD.md` 第 9 章仍将 `Web系统` 放入渠道矩阵与定价矩阵，且 `AI审核版/基础版/标准版` 仍写 `闲鱼/Web`、`微信/Web`
- `product/ROADMAP.md` 仍把“AI方案审核 / 反扎堆 / 数据溯源”整体打成“已完成”，但当前 `audit run` 实际只承认“省规则 + 专业目录状态”两类检查
- `docs/TECH_ARCHITECTURE.md` 已比旧版收紧，但仍有“当前(v2.0)技术栈 / 已实现模块 / v2.1新增技术栈”混排，容易让评审混淆 Current 与 Target

---

## 3. 当前仍有效的问题清单（只保留当前真实问题）

## P0 / 必须修复后才可按生产上线表述

### P0-1 文档真相漂移：PRD / ROADMAP 仍高估 Web 自助与 AI 审核覆盖面

**问题**：

当前真相源 `docs/CURRENT_STATE.md` 已明确：

- 项目定位是人工服务运营增强系统
- 用户端 Web 自助闭环仅为本地 MVP / 目标态
- `audit run` 当前只承认“省规则 + 专业目录状态”两类真实检查

但 PRD / ROADMAP 仍存在会误导上线判断的表述：

- `product/PRD.md` 第 9 章仍将 `Web系统` 作为推广渠道、订单来源和适用定价渠道直接列入主表
- `product/ROADMAP.md` 仍将“AI方案审核 / 反扎堆推荐 / 数据溯源”整体标为“已完成”，易被理解为当前完整产品能力已收口

**影响**：

- 会把“本地 MVP / 目标态”误读成“已上线能力”
- 会把独立能力误读成 `audit run` 已全量覆盖
- 会直接污染对外承诺、验收口径和后续 review 基线

**定位**：

- `product/PRD.md`
- `product/ROADMAP.md`
- `docs/TECH_ARCHITECTURE.md`
- `README.md`（需进一步收口正文口径）

---

### P0-2 删除/匿名化缺少保留期/审计期代码门禁

**问题**：

`data/orders/deletion_service.py` 当前支持：

- 直接删除订单
- 匿名化订单
- 清理文件、payments callback、order_intakes、delivery_notifications
- 写入删除审计表

但没有看到：

- `retention_until` 一类字段
- 删除前检查“支付审计期/争议期/法定保留期”的 guard
- “应拒绝删除”的回归测试

**影响**：

- 当前后台可对仍处于保留期的订单直接删除/匿名化
- 与 `docs/DATA_RETENTION_AND_DELETION.md` 的合规口径不一致
- 这是当前最重的真实代码缺口

**定位**：

- `data/orders/deletion_service.py`
- `data/orders/schema.py`
- `admin/routes/orders.py`
- `admin/tests/test_order_deletion.py`

---

## P1 / 生产前应补齐

### P1-1 失败支付状态机未闭环

**问题**：

`data/payments/service.py` 对失败 webhook 当前行为是：

- 直接抛 `PaymentError("payment status not successful")`
- 不写 `payment.status = failed`
- 不形成失败持久化审计状态

**影响**：

- 管理后台与后续排障无法从 payment 记录直接看到“失败态”
- 失败支付只能体现为一次 HTTP 失败，而不是完整业务状态

**定位**：

- `data/payments/service.py`
- 相关 payment tests

---

### P1-2 当前真相源未吸收 6/18-6/19 的真实变化

**问题**：

- `docs/CURRENT_STATE.md` 仍停留在 2026-06-17
- `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md` 也未反映 6/18 strict review 后的修复与剩余问题
- 昨日 review 与整改计划仍是未提交/未纳管状态

**影响**：

- 后续 agent 或评审者仍会引用旧口径
- 已修复项可能被继续误报为未完成
- 当前仍有效问题无法进入唯一真相链

---

### P1-3 README/运行说明仍有少量“python3 直接运行”口径残留

**问题**：

当前项目真实运行依赖 `.venv`。虽然顶层门禁已统一，但 README 正文仍有若干命令示例容易让人误以为系统 `python3` 直跑就是正式支持路径。

**影响**：

- 新环境复现时仍可能踩到解释器/依赖漂移问题

---

## 4. 已确认收口、不应再重复列为当前阻塞的问题

以下问题本轮已直接复核为**代码层收口**，不应继续按“当前未修”表述：

1. `backup_verify.sh` 对 WAL SQLite 的 live verify 不可信
2. coverage gate 把测试代码算入应用覆盖率
3. 后台无角色授权边界
4. `audit_report/pdf_path/plan_file` 任意本地路径可被 portal 读出
5. portal token 直接通过支付 URL / return_url 传播
6. retention cleanup 漏掉 `delivery_notifications.payload_json`

> 注意：这些问题的“代码修复已完成”不等于“整体上线完成”；仍需由当前真相源同步吸收，避免旧报告重复污染判断。

---

## 5. 当前上线判断

### 代码门禁

- **本地验证**：✅ 通过
- 证据：`dev-verify.sh` 本轮实跑通过

### 运维/恢复门禁

- **本地恢复链**：✅ 基本通过
- 证据：`backup_verify.sh` 已改用 SQLite backup 路径

### 文档/产品边界门禁

- **对外表述边界**：❌ 未通过
- 原因：PRD / ROADMAP / README / CURRENT_STATE 尚未完全对齐当前真实定位

### 合规/业务闭环门禁

- **删除保留期门禁**：❌ 未通过
- **失败支付状态机**：⚠️ 未完全通过

### 真实环境验收

- **线上真实支付/公网 notify/备案域名 acceptance**：⏸️ 仍待执行

---

## 6. 结论

**结论：不可上线（按“完整生产上线”标准）。**

更准确的状态分级：

- **代码与本地门禁**：本地验证完成
- **生产文档真相源**：未完成
- **生产合规删除门禁**：未完成
- **支付失败业务状态机**：部分完成
- **线上真实验收**：未完成

因此当前只能表述为：

> 项目已具备较强的本地验证与受控试运行基础，但距离“生产上线可对外承诺”仍差一轮收口，当前阻塞集中在：文档真相、删除保留期门禁、失败支付状态机、真相源同步。
