# CURRENT_STATE

最后更新: 2026-06-20
状态词: 本地验证完成（6/19 复审 + 6/19 整改计划 + A1 保留期门禁 + B1 支付失败持久化

- A2/B2 文档与执行板校准 + 6/20 T12-D retention cleanup conn ownership 修复
- 端到端本地 acceptance 步骤落地 + 6/20 A-2 admin/外部渠道补录同意审计统一化
  落地；下一阶段 = 推进 T12 真实支付 acceptance + 隐私政策正式审定 + 备份恢复
  异机演练）

真相源优先级:

1. 本文件
2. `docs/ACTIVE_REMEDIATION_2026-06-20.md`（6/20 当前整改清单，**取代 6/19 历史快照**）
3. `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`（6/20 当前执行板，**取代 6/19 历史快照**）
4. `docs/ACTIVE_REMEDIATION_2026-06-19.md`（**已降级为历史快照**）
5. `docs/ACTIVE_EXECUTION_BOARD_2026-06-19.md`（**已降级为历史快照**）
6. `docs/plans/2026-06-19-production-readiness-remediation-plan.md`（6/19 整改计划）
7. `reports/PRODUCTION_STRICT_REVIEW_2026-06-19.md`（6/19 复审报告）
8. `docs/plans/2026-06-17-phase2-majors-catalog-implementation-plan.md`（Phase 2 已收口快照）
9. `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md`（设计快照；Phase 编号需与执行口径消歧）
10. `docs/PROJECT_PLANNING_REALIGNMENT_2026-06-16.md`（历史规划/实现漂移审计）
11. `docs/RULES_SOURCE_OF_TRUTH.md`（规则真相源索引；待补建）
12. `docs/MAJOR_DATA_SOURCE_OF_TRUTH.md`（专业目录真相源索引）
13. `docs/CLI_API_MAPPING.md`（CLI/API 映射索引）
14. `docs/P0_P1_P2_REMEDIATION_PLAN_2026-06-14.md`（历史整改板；§4 卡片以 §2.1 状态归一为准）
15. `docs/FRONTEND_UI_AUDIT_2026-06-16.md` / `docs/FRONTEND_UI_EXECUTION_BOARD_2026-06-16.md`
16. `docs/ACTIVE_REMEDIATION_2026-06-13.md`（**已降级为历史快照**）
17. `docs/ACTIVE_EXECUTION_BOARD_2026-06-13.md`（**已降级为历史快照**）
18. `product/PRD.md` / `product/ROADMAP.md` / `docs/IMPLEMENTATION_PLAN_v2.md`
19. `docs/PRODUCTION_DEPLOYMENT_CHECKLIST_2026-06-15.md`
20. `reports/PRODUCT_PLANNING_TECH_ALIGNMENT_REVIEW_2026-06-13.md`（历史评审快照）

---

## 0. 6/20 增量段（叠加在 6/19 真相源之上）

6/20 落地了 1 项 P1 整改 + 端到端本地 acceptance 步骤 + 1 项合规补录统一化 + 真相源分层。
**本节是当前唯一增量**：

### 0.1 T12-D retention cleanup conn ownership 修复（P1）

- 现象: `retention_cleanup.run_cleanup(apply=True)` 一次命中 ≥ 2 笔终端态订单时，第二笔起全部 `sqlite3.ProgrammingError: Cannot operate on a closed database`
- 根因: `OrdersDAO.__exit__` 不区分连接所有权，对外部 service 传入的 `self._conn` 也 `close()`；`deletion_service.anonymize_order` 把 service 持有的连接包成 `OrdersDAO(self._conn)` 走 with-block，第一笔执行完就把连接关掉
- 修复: `OrdersDAO.__init__` 新增 `owns_conn: bool = False` 参数；`__exit__` 仅在 `owns_conn=True` 时 close；`connect()` classmethod 创建的连接自动设 `owns_conn=True`（保持原行为）；外部 service 包成 DAO 走 with-block 默认不 close
- 回归测试: `tests/test_retention_cleanup.py::test_retention_cleanup_apply_anonymizes_multiple_old_orders_in_sequence` 锁住多订单连续 anonymize 契约
- 端到端 smoke 实测: 4 笔订单（2 笔旧 terminal + 1 笔 fresh pending + 1 笔 paid-in-window）→ dry-run 报 2 candidates / 0 anonymized；apply 真把 2 笔匿名化，pending/paid-in-window 严格不动，deletion log 1 条被裁，share events 2 条被裁
- runbook §8 新增 T12-D 本地端到端 acceptance 步骤 + 部署前 checklist + 历史 bug 背景
- 验证: 6 个 retention 测试 + 205 个直接相关子集全过，ruff + mypy 通过

### 0.2 A-2 admin/外部渠道补录同意审计统一化（P1）

- 现象: `admin/routes/orders.py:543-590` `create_order` 路径不收任何 consent 字段
  （grep `consent` 0 命中），直接违反 `LEGAL_PRIVACY_BASELINE §6`。
  portal 路径早已自动落 `consent_channel=portal / consent_operator=guardian`
- 修复: `CreateOrderRequest.consent: ConsentInfo` 必填；`consent_method` 白名单
  `verbal_chat / phone_recording / screenshot / written_form / self_declared`
- 落地: `Order` 模型 + DAO + schema 增量加 `consent_method / consent_given_at`
  （冗余避免 join）；创建订单后同步写 `order_intakes` 记录（独立 `IntakeStore.for_db`）
  - `consent_channel` = source
  - `consent_operator` 严格按基线白名单 `self / guardian / admin_import`:
    - `web` 渠道: `guardian`（与 `intake_store.save` 默认值一致）
    - 其他渠道: `admin_import`（后台代录，同意来源是渠道商）
- 验证: 25 个 admin orders + alias 测试全过；ruff + mypy 通过；端到端 smoke 通过
- 测试: 4 个参数化 missing_consent_block + 3 个 audit 字段校验 + 1 个白名单校验
  - 1 个 detail 返回值 + 1 个 update test_create_order_returns_masked_payload

### 0.3 真相源分层与历史快照降级（6/20 增量）

- 6/19 整改板/执行板顶部加"⚠ 历史快照"头注，指向 6/20
- 6/20 新建 `docs/ACTIVE_REMEDIATION_2026-06-20.md` + `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`
- 本节作为 6/20 增量叠加在 6/19 真相源之上

---

## 6/19 增量段（叠加在 6/13 真相源之上）

6/19 落地了 3 项 P0/P1 整改 + 1 项真相源分层。**本节是当前唯一增量**：

### 0.1 A1 — 删除/匿名化保留期门禁（P0）

- 错误码 `BIZ_ORDER_RETENTION_NOT_EXPIRED` (E02002) → HTTP 409
- 配置 `GAOKAO_RETENTION_DAYS`（默认 180）
- 路由层 `_assert_retention_expired` 守卫，状态子集 paid/serving/delivered/completed/refunded 触发，pending 直接放行
- 口径来源: `docs/DATA_RETENTION_AND_DELETION.md` §2
- 测试: 3 个新失败/放行用例 + `_expire_retention_window` helper
- 验证: dev-verify all checks passed（1175 passed）

### 0.2 B1 — 支付失败状态持久化（P1）

- `data.payments.service.handle_webhook`: 非 success 状态不再抛 PaymentError，改为持久化 `payment.status='failed'` + `failed_at` + `failure_reason` + 完整 `callback_payload`
- schema 增量升级：`_ensure_column` 幂等 `ALTER TABLE payments ADD COLUMN failed_at / failure_reason`
- 幂等保证：终态（paid / refunded / failed）后到达的失败 webhook 走 idempotent 路径
- 测试: `test_handle_webhook_persists_failed_status` 锁住新契约
- 验证: dev-verify all checks passed

### 0.3 A2 — 4 个产品/工程文档 Current/Target 校准（P1）

- `README.md` 顶部执行板指向 6/19 + 6/19 新增约束
- `product/PRD.md` 顶部"最后更新"升级为 6/19
- `product/ROADMAP.md` 顶部校准从 6/13 升级到 6/19
- `docs/TECH_ARCHITECTURE.md` 顶部 Current/Target 指向 6/19 执行板

### 0.4 B2 — 真相源分层与历史快照降级（P1）

- 6/13 整改板/执行板顶部加"⚠ 历史快照"头注
- 新建 `docs/ACTIVE_REMEDIATION_2026-06-19.md` + `docs/ACTIVE_EXECUTION_BOARD_2026-06-19.md`
- 本节作为 6/19 增量叠加在 6/13 真相源之上

### 0.5 T12-C — 前台删除工单 + 保留期外可申请（P1，本节落盘即收口）

- 落地:
  - `admin/routes/web_public.py` 加 `_resolve_retention_status` + `_next_step_for_retention`
  - `DeletionRequestCreate` Pydantic 锁 `scope` 到白名单 + `confirm_guardian` 强制 bool
  - `POST /portal/{token}/deletion-request` 根据订单保留期返回 3 种 next_step 文案
  - `GET /portal/{token}/deletion-request` 在表单上方加"保留期状态"提示卡
- 测试: 4 个新测试 + 2 个 helper 复用
- 验证: 1179 passed, dev-verify all checks passed

---

## 0. 单一执行口径（2026-06-17）

为消除设计 Phase 编号与执行 Phase 编号漂移，本节是当前唯一口径：

| 设计层 Phase（DESIGN_RULES_TRUSTED_CLI_2026-06-16.md） | 执行层 Phase（当前真相）                   | 状态                                           |
| ------------------------------------------------------ | ------------------------------------------ | ---------------------------------------------- |
| Phase 1 规则真相源化                                   | 执行 Phase 1                               | ✅ 已收口（`ae4835e` + `8a61b8f`，三仓同步）   |
| Phase 2 统一审计引擎最小可用                           | 执行 Phase 1.5（verify + 旧 checker 迁移） | ✅ 已收口（同上）                              |
| Phase 3 专业目录接入 MVP                               | 执行 Phase 2                               | ✅ 已收口（`36ad58a` + `6b1157f` + `edc5b11`） |
| Phase 4 统一 CLI 命令面                                | 执行 Phase 3                               | ❌ 未启动 → 下一阶段                           |
| Phase 5 智能体调度 + admin 整合                        | 执行 Phase 4                               | ❌ 未启动 → 等 Phase 3 收口                    |
| Phase 6 文档/真相源索引收口                            | 长期维护                                   | ⚠ 进行中（docs-only 收口本轮同步）             |

> 设计层 Phase ≠ 执行层 Phase。状态查询一律以本表 + 6/17 执行板为准。

---

## 1. 当前准确定位

项目当前准确定位为：

- 已完成: 人工服务运营增强系统（闲鱼 / 微信 / 学校渠道）
- 已完成: 管理后台、订单、分享、渠道同步、AI 审核基础校验、CI/CD、性能与安全加固
- 已完成/已验证:
  - `Phase2 major_validation` 已接入 `AuditEngine`
  - `gaokao-cli audit run --json` 当前只承认两类真实检查：省份规则 + 专业目录状态
  - 规则/专业目录/CLI 三层都已具备可回归验证入口
- 当前仍在推进:
  - 已完成且已本地验证: `mock` / `alipay_sim` / `alipay` 三层支付代码链与 notify/return 路由；退款状态闭环、portal token secret 分离、payment webhook fail-closed、删除/匿名化扩围、分享 allowlist、channel_sync DB 隔离与 DAO 真相收敛
  - 未完成且仍阻塞线上验收: 真实支付宝商户凭据、公网 notify_url、备案域名、真实支付 acceptance

一句话：

> 当前项目定位：人工服务运营增强系统；用户端 Web 自助闭环仅为本地 MVP/目标态，尚未达到可对外承诺的完整 SaaS 水位。当前版本已经完成 v2.1 的后台运营链路与 AI 审核增强闭环，但不是完整 Web 自助 SaaS。

---

## 2. 已完成模块

- T1 AI审核服务
- T2 反扎堆检测
- T3 数据溯源
- T4 订单管理
- T5 集成测试与发布
- T6 管理后台
- T7 分享功能
- T8 渠道集成
- T9 错误处理
- T10 CI/CD
- T11 性能与安全

覆盖率门槛证据：
覆盖率门槛证据：

- overall = 92.46%
- core = 100.00%
- 满足：整体≥80%、核心≥100%

- 本地与 CI 的硬门禁统一收敛到 `scripts/check_coverage_gate.py`
- `dev-verify.sh` 与 GitHub CI 都执行同一组硬阈值检查
- `codecov.yml` 当前保持同值展示口径，但不是执行单源，也不是阻断门禁

三仓同步状态：

- gitea/main 已同步
- origin/main 已同步
- tksea/main 已同步
- tag v2.1 已推送

---

## 3. 尚未完成 / 不应误报为已完成

### T12 用户端 Web 自助 MVP

当前仅能说：

- 已启动 / 实施中
- 还不能说“已完成”

未完成主链路包括：

- 真实支付接入与回调验签的线上 acceptance
- `info_submitted -> serving` 自动处理主链 +本地自动桥接 `info_submitted -> serving` 已落地；仍缺真实 worker/生成服务/线上调度收口
- 站内通知发送器、真实邮件通知发送器与调度已落地；仍缺生产告警链与独立通知审计页
- 前台删除工单流程与更完整的产品化交互

因此：

- Web 自助购买场景 = **本地 MVP 主链已大部分落地，但线上闭环未完成**
- 完整教育 SaaS 化 = 未完成

---

## 4. 已修正的历史评审问题

以下问题在 2026-06-13 之后已被修正，不应继续按“当前未解决”表述：

1. PRD P2 / P3 功能编号冲突
2. ROADMAP 中已落地功能仍保持未勾选
3. TECH_ARCHITECTURE 仍标“设计中”
4. FINAL_COMPLETION_REPORT 仍写“条件完成”
5. 依赖清单未显式声明 Jinja2 / WeasyPrint / cairocffi / ruff / mypy
6. GitHub origin 凭据导致发布链阻塞

这些应被视为：

- 已修正的历史问题
- 不应再作为当前阻塞项重复引用

---

## 5. 仍然有效的评审问题

以下问题仍成立，应继续作为后续版本约束：

### P0 / P1 真实缺口

- 用户端 Web 自助支付闭环缺失
- 生产通知链已有底层 validated/delivered 状态机、portal 通知审计页、后台独立通知审计页、运维告警审计页与 watchdog alert sink；已支持 SMTP/IM webhook sink 代码接入，但仍缺线上真实通道配置后的生产联调
- 前台入口已支持基础资料填写、最多 5 个附件上传与 5 步向导（基础信息 / 偏好与目标 / 已有方案与附件 / 协议确认 / 提交确认）；仍缺更完整文件类型策略与更细粒度错误提示
- 2026-06-16 前端专项审计结论：用户端首页 / 定价页 / 结账页存在明显 AI 模板痕迹、开发术语外露与商业转化不足；后台 `/dashboard` 仍偏开发者自检页。当前执行板见 `docs/FRONTEND_UI_EXECUTION_BOARD_2026-06-16.md`
- 2026-06-16 第二轮本地整改已完成：首页、定价页、结账页、portal 向导页 / 状态页、后台 `/dashboard` 已完成首轮产品化与去技术暴露重构；剩余前端工作聚焦 design token 基线与更强回归门禁
- 2026-06-16 第三轮本地整改已完成：`admin/static/portal-ui.css` 已建立为共享样式基线，关键用户页面已接入 shared CSS，并补齐页面级回归断言；前端整改范围已本地收口，剩余仅为 Git 交付或后续更深层视觉迭代
- 业务数据备份 / 恢复 / 密钥托管已有本地基线与验证，但异机备份和生产接入仍不足
- 隐私政策 / 服务协议 / 监护人同意 / 数据保留与删除流程仍缺前台/客服自助工单与正式法务版本

> 重要更新（2026-06-15）：
> 上述 5 项是 v2.1 当前阶段以外的真实缺口。
> 上一轮 2026-06-14 严格复审里的 P1 整改项已全部完成：
>
> - P1-1 支付回调双写裂缝已修复
> - P1-5 退款域模型闭环已修复
> - P1-2 删除/匿名化已覆盖 orders 主表 + payments.callback_payload + order_intakes.payload_json
> - P1-7 验证链口径统一（CI / dev-verify / codecov / gate script 同一阈值）

### P2 工程改进

- crowd_db 高置信数据应区分湖南与其他省份
- 架构图仍需进一步拆分 Current / Target 视觉表达
- legacy 邮件脚本应继续弱化为非主链能力

### 仍然有效的 P1 / P2 整改项

完整清单见 `docs/P0_P1_P2_REMEDIATION_PLAN_2026-06-14.md`：

- P1-3 真实支付回调校验
- P1-8 备份恢复演练 / 目标机告警接入
- 隐私政策 / 服务协议 / 删除工单正式入口

已完成并不再列为整改项：

- P2-1 公共下单孤儿订单
- P2-2 channel_sync 单一 DAO 真相
- P2-3 delivery 通知状态语义收口（`sent` 已移除）
- P2-4 portal token / JWT secret 分离（已通过 P2-4 单元测试 + prod fail-closed）
- P2-5 payment webhook secret fail-closed（已通过 P2-5 单元测试 + prod fail-closed）
- X-02 支付域设计
- X-03 Delivery 交付服务设计
- X-04 合规基线文档
- X-05 备份恢复与密钥托管方案
- X-06 本地一键验证脚本
- X-08 crowd_db 数据完整度等级化

---

## 6. 对外表述边界

允许对外说：

- 已具备人工服务运营后台能力
- 已具备 AI 审核基础校验、数据溯源、分享、渠道同步能力
- `audit run` 当前只承认省份规则 + 专业目录状态校验，不应对外表述为“已包含反扎堆/综合评分闭环”
- 已完成 v2.1 当前计划闭环

不应对外说：

- 已完成完整 Web 自助 SaaS
- 已完成系统内支付闭环
- 已完成用户端完整交付闭环
- 27 省 crowd_db 均为高置信强推荐数据

---

## 7. 推荐阅读顺序

1. docs/CURRENT_STATE.md
2. docs/archive/2026-06-historical-snapshots/FINAL_COMPLETION_REPORT_2026-06-13.md
3. product/PRD.md
4. product/ROADMAP.md
5. docs/IMPLEMENTATION_PLAN_v2.md
6. reports/PRODUCT_PLANNING_TECH_ALIGNMENT_REVIEW_2026-06-13.md（作为历史评审参考）
