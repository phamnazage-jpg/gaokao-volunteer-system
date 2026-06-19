# 2026-06-19 生产上线整改计划（基于当前真相）

目标：在不扩范围、不重写系统的前提下，把当前仍有效的上线阻塞项收口到“可受控上线评审”的状态。

原则：

1. 只修当前仍有效问题，不重开已收口旧问题。
2. 先修会影响真相、合规、支付状态判断的项，再修文档与运行说明。
3. 每项必须带测试或可重复验证证据。

---

## 批次 A：P0 真相与合规阻塞（必须优先）

### A1. 为删除/匿名化补保留期门禁

**优先级**：P0

**目标**：保证处于支付审计期 / 争议期 / 法定保留期的订单不能被直接删除或匿名化。

**涉及文件**：

- `data/orders/schema.py`
- `data/orders/models.py`
- `data/orders/deletion_service.py`
- `admin/routes/orders.py`
- `admin/tests/test_order_deletion.py`

**实现要求**：

1. 为订单增加保留期字段（如 `retention_until`）或等价策略字段。
2. `delete_order()` / `anonymize_order()` 执行前检查：
   - 未过保留期 → 明确拒绝
   - 已过保留期 → 允许执行
3. 管理后台接口必须返回明确的业务错误，而不是静默失败。
4. 增加至少两类回归测试：
   - 保留期内删除被拒绝
   - 过保留期删除成功

**验收命令**：

```bash
./.venv/bin/python -m pytest -q admin/tests/test_order_deletion.py
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

---

### A2. 重写产品/架构文档中的 Current / In Progress / Target 边界

**优先级**：P0

**目标**：消除“已是完整 Web 自助产品 / audit run 已包含全部能力”的误导。

**涉及文件**：

- `README.md`
- `product/PRD.md`
- `product/ROADMAP.md`
- `docs/TECH_ARCHITECTURE.md`
- `docs/API.md`

**实现要求**：

1. `README.md`：保留顶部真实口径，并让正文不再盖过该限制。
2. `product/PRD.md`：
   - 将 `Web系统` 明确标注为 `目标态/本地 MVP`，不得作为当前售卖渠道直接陈述
   - 定价矩阵中的 `闲鱼/Web`、`微信/Web` 改成分层表达
3. `product/ROADMAP.md`：
   - 把“AI方案审核 / 反扎堆 / 数据溯源”的完成状态拆成：已落地能力 vs 未接入 `audit run` 的能力
4. `docs/TECH_ARCHITECTURE.md`：
   - 保持 Current / In Progress / Target 明确分段
   - 删除或降级仍会被误读成“当前上线能力”的表述
5. `docs/API.md`：如果仍有“综合评分/完整审核闭环”式表述，应改成当前真实能力范围。

**验收标准**：

- 任意只读这几份文档的评审者，不应再得出“系统已是完整 Web 自助 SaaS”或“audit run 已做完反扎堆/综合评分”的结论。

---

## 批次 B：P1 业务状态与真相源同步

### B1. 为支付失败 webhook 持久化失败状态

**优先级**：P1

**目标**：让支付失败不只是一次 HTTP 错误，而是可审计的业务状态。

**涉及文件**：

- `data/payments/service.py`
- `data/payments/dao.py`（如需要）
- 相关 payment tests

**实现要求**：

1. 当 provider webhook 返回非 success 状态时：
   - 将 payment 记录持久化为 `failed`（或等价失败态）
   - 保留 callback payload / failure reason
2. 增加失败 webhook 回归测试。
3. 校准 portal / admin 对失败态的展示或处理语义。

**验收命令**：

```bash
./.venv/bin/python -m pytest -q data/payments/tests admin/tests/test_payment_alipay_notify.py
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

---

### B2. 更新唯一真相源文档

**优先级**：P1

**目标**：把 6/18-6/19 的真实变化纳入当前真相链，停止继续依赖旧快照。

**涉及文件**：

- `docs/CURRENT_STATE.md`
- `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md`（或新建 2026-06-19 板）
- `docs/ACTIVE_REMEDIATION_2026-06-19.md`（建议新建）
- `docs/NAVIGATION.md`

**实现要求**：

1. `CURRENT_STATE.md` 更新为最新日期，吸收：
   - 已收口项
   - 当前仍有效项
   - 当前上线判断边界
2. 旧执行板若继续保留，必须标成历史快照；建议新增 6/19 当前执行板。
3. 新 remediation 只保留当前有效问题：
   - 文档真相漂移
   - 删除保留期门禁
   - 失败支付状态机
   - 运行说明残留
4. `reports/PRODUCTION_STRICT_REVIEW_2026-06-19.md` 与本计划文档进入导航索引。

**验收标准**：

- 新会话从 `CURRENT_STATE.md` 出发时，不会再把 6/18 前已修复问题当作当前阻塞。

---

## 批次 C：P2 收尾与降低复发率

### C1. 收紧 README 的运行前提说明

**优先级**：P2

**目标**：避免继续把系统 `python3` 直跑误读为正式支持路径。

**涉及文件**：

- `README.md`
- 如有必要：`INSTALL.md`

**实现要求**：

1. 所有关键命令示例统一成 `.venv/bin/python` 或明确“需先激活 venv”。
2. 若保留 `python3` 示例，必须标明这是“已装依赖前提下”的简写，而不是裸系统 Python 保证可跑。

---

### C2. 可选增强：checkout token 落库最小化

**优先级**：P2

**目标**：进一步降低支付关联 token 泄露面。

**涉及文件**：

- `data/payments/service.py`
- `data/payments/dao.py`
- provider / payment tests

**实现要求**：

- 如成本可控，将 `checkout_token` 改成只存哈希，或明确该 token 的最小权限边界。

---

## 推荐执行顺序

1. **A1 删除保留期门禁**
2. **A2 文档 Current/Target 收口**
3. **B1 失败支付状态持久化**
4. **B2 真相源同步**
5. **C1 README/INSTALL 运行说明收口**
6. **C2 checkout token 最小化（可选）**

---

## 最终验收门槛

完成本计划后，至少应满足：

1. `GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh` 持续通过
2. 删除/匿名化存在明确保留期拒绝测试
3. 失败支付存在明确持久化失败态测试
4. `CURRENT_STATE.md` / 当前执行板 / remediation 已同步到 6/19 真相
5. PRD / ROADMAP / README / TECH_ARCHITECTURE 不再把 Target 写成 Current

在此之前，不得对外表述为“完整生产上线完成”。
