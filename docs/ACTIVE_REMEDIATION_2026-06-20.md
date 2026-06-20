# ACTIVE_REMEDIATION_2026-06-20

最后更新: 2026-06-20
状态词: 当前仍然有效的问题清单（仅保留未解决项）
真相源: `docs/CURRENT_STATE.md`
来源基线:

- `docs/ACTIVE_REMEDIATION_2026-06-19.md`（**已降级为历史快照**）
- `reports/PRODUCTION_STRICT_REVIEW_2026-06-19.md`（6/19 复审报告）
- `docs/plans/2026-06-19-production-readiness-remediation-plan.md`（6/19 整改计划）
- 6/20 端到端本地 acceptance 步骤：`docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` §8
- 本轮 TDD 执行结果（直接相关子集 205 passed, 0 failed, retention 6 passed；端到端 smoke 4 笔订单验证通过）

> 本文件取代 `docs/ACTIVE_REMEDIATION_2026-06-19.md`（已降级为历史快照）。

---

## 0. 使用规则（防止虚假完成和漂移）

本清单只保留"当前仍然有效"的问题。
以下类型不得再重复列为当前阻塞：

1. 已在代码中落地且已通过 `bash scripts/dev-verify.sh` 验证并已推送三仓的问题
2. 只属于历史评审快照、但已在 6/19 或 6/20 之前修复的问题
3. 尚未进入当前版本范围、且已明确标注为后续阶段（T12 Web 自助 MVP / 真实支付 acceptance）的能力缺口

判断规则：

- 已落地 = 代码/配置/脚本/测试/文档已存在并已通过 dev-verify 验证
- 已收尾 = 工作区干净 + main 已同步三仓
- 后续范围 = `CURRENT_STATE.md` 已明确声明"不属于 v2.1 当前完成范围"

---

## 1. 当前仍然有效的问题（按优先级，只保留未解决项）

### A. 投产级真实缺口（生产上线仍阻塞）

#### A-1 用户端 Web 自助闭环未完成（仍属 T12）

严重度: P0（面向 Web 自助产品时）
当前状态: 本地 MVP 主链已大部分落地，线上闭环仍未收口
范围归属: T12（后续阶段）

**当前未阻塞的关键能力**：

- 删除/匿名化 180 天保留期门禁（E02002）— 6/19 已落地
- 支付失败状态持久化（status='failed' + failed_at + failure_reason）— 6/19 已落地
- **retention cleanup 多订单连续 anonymize 修复 + 端到端本地 acceptance 步骤** — **6/20 已落地**（T12-D conn ownership）

**当前仍阻塞的关键能力**：

- 真实支付接入与回调验签的线上 acceptance（T12-A）
- `info_submitted -> serving` 自动处理主链 + 真实 worker/生成服务/线上调度收口（T12-B）
- 完整站内通知/交付产品化
- 前台删除工单流程（6/19 T12-C 已落地表单与保留期资格，**但生产化部署验收仍在 T12-D 范围**）
- 备案域名 + 公网 notify_url

### A-2 后台/外部渠道补录同意审计统一化（6/20 已完成）

严重度: P1
当前状态: **6/20 已完成**
范围归属: 合规/数据治理

已完成（6/20 增量）:

- `CreateOrderRequest.consent: ConsentInfo` 必填，缺失或非法 → HTTP 422
- `consent_method` 白名单: `verbal_chat / phone_recording / screenshot / written_form / self_declared`
- 4 个 source (xianyu / wechat / web / school) 一致处理
- `Order` 模型 + DAO + schema 增量加 `consent_method / consent_given_at` 字段（冗余避免 join）
- 创建订单后同步写 `order_intakes` 记录，与 portal 路径同口径
- `consent_operator` 严格按基线白名单 `self / guardian / admin_import`:
  - `web` 渠道: `guardian`（与 `intake_store.save` 默认值一致）
  - 其他渠道: `admin_import`（后台代录，同意来源是渠道商）
- 测试: 4 个参数化 missing_consent_block + 3 个 audit 字段校验 + 1 个白名单校验 + 1 个 detail 返回值 + 1 个 update
- 验证: 25/25 admin orders + alias 测试全过；ruff + mypy 通过；端到端 smoke 通过
- 提交: `187b2ae` fix(compliance): A-2 admin/外部渠道补录同意审计统一化 → `bd27b01` merge: A-2 admin/外部渠道补录同意审计统一化

## 1. 当前仍然有效的问题（按优先级，只保留未解决项）

#### B-1 真实支付 acceptance 仍依赖外部前置

严重度: P0
当前状态: 6/19 失败 webhook 持久化已落地，剩余阻塞在线上 acceptance
范围归属: T12 / 真实环境联调

已完成（6/19 增量）：

- `data.payments.service.handle_webhook`：非 success 状态不再抛 PaymentError，而是持久化 `payment.status='failed'` + `failed_at` + `failure_reason` + 完整 `callback_payload`
- schema 增量升级：`_ensure_column` 幂等 `ALTER TABLE payments ADD COLUMN failed_at / failure_reason`
- 幂等保证：终态（paid / refunded / failed）后到达的失败 webhook 走 idempotent 路径
- 测试覆盖：`test_handle_webhook_persists_failed_status` 锁住新契约

仍缺：

- 真实商户主体 / 产品签约 / app_id
- 私钥与支付宝公钥在真实环境装载
- 备案域名与公网 `notify_url`
- 沙箱/生产真实支付 acceptance
- 对账任务与退款回写/异常补偿产品化

#### B-2 T12-D retention cleanup conn ownership 修复（已完成 6/20）

严重度: P1
当前状态: **6/20 已完成**
范围归属: 合规/数据治理

已完成（6/20 增量）：

- `OrdersDAO.__init__` 新增 `owns_conn: bool = False` 参数
- `OrdersDAO.__exit__` 仅在 `owns_conn=True` 时 close
- `OrdersDAO.connect()` classmethod 创建的连接自动设 `owns_conn=True`（保持原行为）
- 回归测试：`test_retention_cleanup_apply_anonymizes_multiple_old_orders_in_sequence` 锁住多订单连续 anonymize 契约
- 端到端本地 acceptance 步骤：`docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` §8
- runbook 部署前 checklist
- 验证: 6 个 retention 测试全过 + 205 个直接相关子集全过 + ruff + mypy 通过

#### B-3 删除/匿名化前台工单仍待收口

严重度: P1
当前状态: 6/19 T12-C 前台表单已落地，**生产化运维仍待补**
范围归属: 合规/数据治理

已完成（6/19 增量）：

- 路由层 `_assert_retention_expired` 守卫：`admin/routes/orders.py`
- 错误码 `BIZ_ORDER_RETENTION_NOT_EXPIRED` (E02002) → HTTP 409
- 配置 `GAOKAO_RETENTION_DAYS`（默认 180）可经环境变量覆盖
- 前台 portal 删除工单 + "保留期外可申请" 文案 + 6 个测试
- 测试覆盖：3 个新失败/放行用例 + `_expire_retention_window` 测试 helper

仍缺：

- `scripts/gaokao-retention-cleanup.py` 的生产化部署与定时接入验收（**T12-D 端到端 acceptance 步骤已就绪，实际部署动作待 ops 执行**）
- 正式法务审定版本

### C. 文档与执行板一致性（6/19 已收口）

#### C-1 4 个产品/工程文档 Current/Target 校准到 6/19

严重度: P1
当前状态: 6/19 已完成

已完成：

- `README.md` 顶部指向 6/19 执行板，加 6/19 新增约束（E02002 / 180 天）
- `product/PRD.md` 顶部"最后更新"升级为 6/19，加删除/匿名化能力校准
- `product/ROADMAP.md` 顶部校准说明从 6/13 升级到 6/19
- `docs/TECH_ARCHITECTURE.md` 顶部 Current/Target 说明指向 6/19 执行板
- `docs/ACTIVE_REMEDIATION_2026-06-13.md` 与 `docs/ACTIVE_EXECUTION_BOARD_2026-06-13.md` 顶部加历史快照头注

#### C-2 真相源分层与历史快照降级

严重度: P1
当前状态: 6/20 已完成（6/19 增量 + 6/20 增量）

已完成：

- 6/13 整改板/执行板顶部加"⚠ 历史快照"头注，指向 6/19 版本
- 6/19 新建 `docs/ACTIVE_REMEDIATION_2026-06-19.md` + `docs/ACTIVE_EXECUTION_BOARD_2026-06-19.md`
- 6/20 重复上述动作，新建 6/20 版本，把 6/19 降级为历史快照
- `docs/CURRENT_STATE.md` 顶部加 6/19 增量段 + 6/20 增量段，指向新真相源

---

## 2. 明确不再重复追踪的问题（已解决）

以下问题已经修复，不应再出现在新的整改清单里：

1. 删除/匿名化缺保留期门禁 — 6/19 已修复（E02002）
2. 失败 webhook 抛 PaymentError 而不持久化 — 6/19 已修复
3. retention cleanup 多订单连续 anonymize 崩溃（`Cannot operate on a closed database`）— 6/20 已修复
4. PRD P2/P3 功能编号冲突
5. ROADMAP 中已落地功能仍未勾选
6. TECH_ARCHITECTURE 仍标"设计中"
7. FINAL_COMPLETION_REPORT 仍为"条件完成"
8. requirements 未声明 Jinja2 / WeasyPrint / cairocffi / ruff / mypy
9. CI 的 `--cov-fail-under=80` 与实际门槛冲突
10. GitHub origin 凭据阻塞发布
11. T1~T11 Goal 阻塞链问题
12. 6/19 之前的 P1 整改项（P1-1 / P1-2 / P1-3 / P1-5 / P1-7 / P1-8 / P2-1~P2-5）
13. 6/19 完成的 3 项（P0 保留期门禁 / P1 支付失败持久化 / P1 T12-C 前台删除工单）

这些问题如果未来再次出现，应视为新回归，而不是沿用旧问题编号。

---

## 3. 推荐的单一后续主线

为了避免继续漂移，建议把后续工作只收敛到 3 条主线：

### 主线 1：T12 Web 自助 MVP + 真实支付 acceptance

目标：补齐"用户端自助下单/支付/资料填写/站内交付"闭环 + 真实支付 acceptance

### 主线 2：合规与数据治理

目标：后台/外部渠道补录同意审计统一化 / 隐私政策正式审定 / 备份恢复生产化 / 密钥轮换记录

### 主线 3：数据质量增强

目标：提升非湖南省份的 crowd_db 置信度与可解释性

不建议再做的事：

- 重复写"已完成能力"的审计报告
- 继续把历史快照问题当作当前阻塞
- 在 T12 未闭环前继续泛化更多高级功能

---

## 4. 最小执行板（当前仍值得做）

| ID    | 任务                                 | 优先级 | 是否属于已完成阶段问题                                         |
| ----- | ------------------------------------ | ------ | -------------------------------------------------------------- |
| T12-A | 真实支付 acceptance (沙箱/生产联调)  | P0     | 否（后续阶段）                                                 |
| T12-B | `info_submitted -> serving` 自动主链 | P0     | 否（后续阶段）                                                 |
| T12-C | 前台删除工单与"保留期外可申请"页     | P1     | ✅ **6/19 已收口**                                             |
| T12-D | retention cleanup 生产化部署验收     | P1     | ⚠ **6/20 端到端 acceptance 步骤就绪，实际部署动作待 ops 执行** |
| L-A   | 隐私政策 / 服务协议正式法务审定      | P1     | 是（当前真实缺口）                                             |
| L-B   | 备份恢复异机演练 + 密钥轮换记录      | P1     | 是（当前真实缺口）                                             |
| Q-A   | crowd_db 非湖南省份高置信数据密度    | P1     | 是（当前真实缺口）                                             |
| A-2   | 后台/外部渠道补录同意审计统一化      | P1     | ✅ **6/20 已收口**                                             |

---

## 5. 当前最准确的最终表述

> 6/20 v2.1.1 已完成"retention cleanup 多订单 conn ownership 修复 + 端到端本地 acceptance 步骤"；当前真正仍有效的问题集中在 T12 Web 自助闭环、真实支付 acceptance、合规、备份恢复和多省高置信数据质量这五个方向。
