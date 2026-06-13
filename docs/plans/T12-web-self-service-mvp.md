# T12 用户端 Web 自助闭环 MVP 实施计划

> **For Hermes:** 后续实现阶段使用 `subagent-driven-development` 按任务逐项执行；每项都要跑真实测试与门禁，不允许只停在页面稿或接口草图。

**Goal:** 把当前“后台 + 人工服务增强链路”扩展为一个可被真实用户使用的 Web 自助 MVP，完成“访问站点 → 选择服务 → 下单支付 → 填资料 → 处理生成 → 站内查看/下载交付”的最小闭环。

**Architecture:** 延续现有 Python/FastAPI + SQLite + 静态 HTML 的轻量架构，不引入重前端框架；前台用户链路复用现有订单、分享、报告、审核能力，在边界处新增用户身份、支付单、资料表单、订单状态页和交付页。支付按“抽象支付网关 + Webhook/回调验签 + 对账/退款占位”设计，先做可上线的单提供方接入，同时保留人工兜底。

**Tech Stack:** FastAPI、Jinja2/静态 HTML、SQLite、现有 `admin/` / `data/orders/` / `data/share/` / `skills/gaokao-audit/`、支付提供方 SDK/HTTP API（后续实现时选定微信支付或支付宝之一）。

---

## 0. 规划边界与真相

### 当前真相

已完成：

- 后台管理、订单基础、分享、渠道同步、AI 审核、覆盖率门禁
- 适合人工服务运营场景（闲鱼/微信/学校）

未完成：

- 用户端 Web 自助下单
- 系统内支付闭环
- 资料填写与协议同意
- 用户订单页 / 站内交付页
- 自动邮件/PDF交付链

### 本次 T12 的目标范围（MVP）

T12 只做 **用户端 Web 自助 MVP**，不做完整 SaaS：

1. 落地页 / 套餐页
2. 下单页
3. 支付创建 + 回调确认
4. 资料填写页（1分钟/3分钟/完整表单至少统一到单一入口）
5. 用户订单状态页
6. 报告查看/下载页
7. 异常与人工兜底页

### 本次不纳入范围

- 多租户
- 真正的用户中心复杂账户体系
- App / 小程序
- 多支付渠道并发接入
- 大规模消息中心
- CRM 深度自动化

---

## 1. 目标用户链路（最终验收主链）

### 场景 B：用户端 Web 自助闭环

```text
访问 Web 首页
  → 选择服务版本（49/99/199 等）
  → 创建订单
  → 完成支付
  → 填写资料 / 上传方案（审核型）
  → 系统处理（AI审核 / 方案生成 / 人工介入）
  → 用户查看订单状态
  → 查看在线报告 / 下载 PDF
  → 售后/退款/补充资料（MVP 做最小兜底）
```

### MVP 验收标准

必须具备：

- 用户无需通过微信/闲鱼人工接力即可在站内走完主链
- 支付成功后订单状态能自动推进
- 资料提交后后台能接单处理
- 用户能看到明确状态：待支付 / 已支付待填写 / 处理中 / 可查看 / 已完成 / 退款中 / 已退款
- 报告交付至少支持：站内查看 + PDF 下载（二选一不够）

---

## 2. 核心设计决策

### 决策 A：Web-first，仍保持轻前端

- 前台继续采用服务端渲染或静态 HTML + 少量 JS
- 不上 React/Vue 作为第一步
- 优先保证闭环，不先做“看起来像 SaaS”的重 UI

### 决策 B：支付必须是真闭环，不接受“假支付页”冒充完成

MVP 至少需要：

- 创建支付单
- 回调验签
- 幂等更新订单支付状态
- 金额校验
- 重复回调安全
- 失败支付可重试

### 决策 C：资料流统一到订单上下文

- 不再把“问卷/审核输入/补资料”散落在脚本层
- 所有前台输入都挂到 `order_id`
- 后续后台、审核、报告、交付都围绕订单聚合

### 决策 D：人工兜底是降级路径，不是主链

允许：

- 支付异常 → 人工核单
- 资料异常 → 人工补录
- 报告生成异常 → 人工重试

不允许：

- 用户主流程必须先加微信才能继续
- 依赖人工收款才能让系统工作

---

## 3. 目标状态机（建议）

### 订单主状态

建议新增或统一到以下状态：

- `pending_payment`
- `paid`
- `info_required`
- `info_submitted`
- `processing`
- `report_ready`
- `completed`
- `refund_pending`
- `refunded`
- `cancelled`
- `payment_failed`

### 支付子状态

- `unpaid`
- `paying`
- `paid`
- `failed`
- `refunding`
- `refunded`

### 处理子状态

- `not_started`
- `waiting_info`
- `queued`
- `running`
- `manual_review`
- `done`
- `failed`

---

## 4. 目录与文件落点建议

### 既有文件重点复用

- `admin/app.py`
- `admin/routes/ui.py`
- `admin/share_page.py`
- `data/orders/models.py`
- `data/orders/schema.py`
- `data/orders/dao.py`
- `data/orders/state_machine.py`
- `data/share/short_link.py`
- `skills/gaokao-audit/scripts/audit_service.py`
- `skills/gaokao-college-advisor/scripts/gaokao_visual_report.py`

### 建议新增文件

前台 Web：

- `web/landing.py` 或 `admin/routes/web_public.py`
- `web/templates/landing.html`
- `web/templates/pricing.html`
- `web/templates/order_checkout.html`
- `web/templates/order_info_form.html`
- `web/templates/order_status.html`
- `web/templates/report_view.html`

支付域：

- `data/payments/models.py`
- `data/payments/dao.py`
- `data/payments/service.py`
- `data/payments/providers/base.py`
- `data/payments/providers/<provider>.py`
- `data/payments/webhook.py`
- `data/payments/tests/...`

用户访问态：

- `data/customer_portal/session.py`
- `data/customer_portal/token.py`
- `data/customer_portal/tests/...`

整合层：

- `data/orders/public_flow.py`
- `data/orders/tests/test_public_flow.py`

---

## 5. 分阶段实施任务（T12.1 - T12.12）

## T12.1 文档真相与入口基线校准

**Objective:** 明确对外口径，新增 T12 为正式主线，不再把 Web 自助描述留在“未来/模糊计划”。

**Files:**

- Modify: `product/PRD.md`
- Modify: `product/ROADMAP.md`
- Modify: `docs/BUSINESS_SCENE.md`
- Modify: `docs/IMPLEMENTATION_PLAN_v2.md`
- Create: `docs/plans/T12-web-self-service-mvp.md`

**完成标准:**

- PRD/ROADMAP/BUSINESS_SCENE 里 Web 自助链路状态一致
- T12 成为正式 Epic
- 明确 MVP 范围与非目标

**验证:**

- `rg -n "Web 自助|T12|支付|订单状态|资料填写" product docs`

---

## T12.2 公共前台入口与套餐页

**Objective:** 提供公开可访问的 landing/pricing 页面，建立用户前台入口。

**Files:**

- Create: `admin/routes/web_public.py` 或 `web/landing.py`
- Create: `web/templates/landing.html`
- Create: `web/templates/pricing.html`
- Test: `admin/tests/test_web_public.py`

**完成标准:**

- 用户能在站内看到服务版本与价格
- 套餐信息不再只存在文档里
- 页面能跳到创建订单流程

**验证:**

- `pytest -q admin/tests/test_web_public.py`

---

## T12.3 公开下单接口与公开订单模型补齐

**Objective:** 在现有订单体系上补齐“用户自助创建订单”能力。

**Files:**

- Modify: `data/orders/models.py`
- Modify: `data/orders/schema.py`
- Modify: `data/orders/dao.py`
- Create: `data/orders/public_flow.py`
- Test: `data/orders/tests/test_public_flow.py`

**完成标准:**

- 支持匿名/轻身份创建订单
- 订单记录套餐、金额、来源、用户联系方式、状态
- 保持后台手工订单与前台自助订单兼容

**验证:**

- `pytest -q data/orders/tests/test_public_flow.py`

---

## T12.4 支付域抽象与支付单表

**Objective:** 新增支付单与支付服务抽象，不把支付字段直接硬塞进订单表。

**Files:**

- Create: `data/payments/models.py`
- Create: `data/payments/dao.py`
- Create: `data/payments/service.py`
- Create: `data/payments/providers/base.py`
- Test: `data/payments/tests/test_service.py`

**完成标准:**

- 一个订单可关联支付单
- 支付单含 provider、amount、currency、status、provider_trade_no、callback_payload
- 支持幂等查询与更新

**验证:**

- `pytest -q data/payments/tests/test_service.py`

---

## T12.5 单支付提供方接入（微信或支付宝二选一）

**Objective:** 先打通一个真实支付提供方，形成真正的 MVP 支付闭环。

**Files:**

- Create: `data/payments/providers/wechat_pay.py` 或 `alipay.py`
- Modify: `data/payments/service.py`
- Test: `data/payments/tests/test_provider_<name>.py`

**完成标准:**

- 可创建支付单
- 可得到支付跳转/二维码/收银台参数
- 不在代码中硬编码秘钥

**验证:**

- 提供 mock/provider sandbox 测试
- 本地/测试环境最小 smoke test

---

## T12.6 支付回调、验签、幂等、金额校验

**Objective:** 保证支付成功不是伪状态推进。

**Files:**

- Create: `data/payments/webhook.py`
- Modify: `admin/app.py` 或支付路由注册点
- Test: `data/payments/tests/test_webhook.py`

**完成标准:**

- 重复回调只处理一次
- 金额不一致拒绝入账
- 订单不存在拒绝更新
- 已退款/已取消订单回调行为明确

**验证:**

- `pytest -q data/payments/tests/test_webhook.py`

---

## T12.7 资料填写统一入口

**Objective:** 让支付成功后的用户在站内提交信息，而不是跳去脚本/对话收集。

**Files:**

- Create: `web/templates/order_info_form.html`
- Modify: `scripts/gaokao-quick-3min.py`（仅抽离可复用 schema/字段定义，避免页面直接依赖 CLI）
- Create: `data/orders/intake_schema.py`
- Test: `admin/tests/test_order_info_form.py`

**完成标准:**

- 至少支持 3 分钟版标准资料收集
- 支持草稿保存 / 重提
- 提交后订单进入 `info_submitted`

**验证:**

- `pytest -q admin/tests/test_order_info_form.py`

---

## T12.8 后台接单与处理队列衔接

**Objective:** 前台订单进入后台处理主链。

**Files:**

- Modify: `admin/routes/orders.py`
- Modify: `data/orders/state_machine.py`
- Modify: `skills/gaokao-audit/scripts/audit_service.py`（如需接单入口）
- Test: `admin/tests/test_routes_orders.py`
- Test: `data/orders/tests/test_state_machine.py`

**完成标准:**

- 后台可看到来自前台的订单
- 可推进到 processing / report_ready
- 状态机不允许非法跳转

**验证:**

- `pytest -q admin/tests/test_routes_orders.py data/orders/tests/test_state_machine.py`

---

## T12.9 站内订单状态页与交付页

**Objective:** 用户能在站内看到订单进度并获取结果。

**Files:**

- Create: `web/templates/order_status.html`
- Create: `web/templates/report_view.html`
- Modify: `admin/share_page.py` / `data/share/short_link.py`
- Test: `admin/tests/test_share_ui.py`
- Test: `admin/tests/test_order_status_page.py`

**完成标准:**

- 订单状态页可显示支付/资料/处理/交付状态
- 报告页可查看 HTML 或下载 PDF
- 权限隔离正确

**验证:**

- `pytest -q admin/tests/test_order_status_page.py admin/tests/test_share_ui.py`

---

## T12.10 交付通知（邮件或站内通知二选一为主，另一种可占位）

**Objective:** 报告 ready 后，用户能被通知，不再靠人工口头提醒。

**Files:**

- Create: `data/notifications/email_service.py`（或站内通知实现）
- Modify: `data/orders/public_flow.py`
- Test: `tests/test_delivery_notification.py`

**完成标准:**

- `report_ready` 时触发通知
- 失败可重试，日志可追踪

**验证:**

- `pytest -q tests/test_delivery_notification.py`

---

## T12.11 售后、退款、异常兜底最小闭环

**Objective:** 给 MVP 补最小售后能力，避免一旦支付出错只能人工拍脑袋处理。

**Files:**

- Modify: `data/payments/service.py`
- Modify: `admin/routes/orders.py`
- Create: `data/payments/tests/test_refund_flow.py`

**完成标准:**

- 可发起退款申请
- 状态可见
- 重复退款 / 已退款保护存在

**验证:**

- `pytest -q data/payments/tests/test_refund_flow.py`

---

## T12.12 端到端验收与上线门禁

**Objective:** 用真实业务链路证明 Web 自助闭环成立。

**Files:**

- Create: `tests/test_t12_web_self_service_e2e.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/TEST_PLAN.md`（如存在）

**完成标准:**

- 至少覆盖一条完整主链：
  - 创建订单
  - 支付成功回调
  - 提交资料
  - 后台处理
  - 报告可查看/下载
- 再覆盖两条异常链：
  - 重复回调
  - 支付成功但报告生成失败

**验证:**

- `pytest -q tests/test_t12_web_self_service_e2e.py`
- `pytest admin/tests tests data --cov=admin --cov=data --cov=skills --cov=scripts --cov-report=term-missing -q`

---

## 6. 测试与门禁要求

### 必跑门禁

```bash
python3 -m pytest -q admin/tests tests data
python3 -m mypy .
python3 -m ruff check . --exclude .worktrees
pytest admin/tests tests data --cov=admin --cov=data --cov=skills --cov=scripts --cov-report=term-missing -q
python3 scripts/check_coverage_gate.py coverage.xml
```

### T12 专项 E2E 必须覆盖

1. 正常支付成功链
2. 重复支付回调链
3. 金额不一致链
4. 用户资料补提链
5. 报告 ready 后查看/下载链
6. 退款申请链

---

## 7. 风险与降级策略

### 风险 1：真实支付接入周期长

降级：

- 先抽象支付域
- 先接一个 provider
- 先走 sandbox / test mode
- 不允许拿“人工转账截图”冒充系统内支付闭环完成

### 风险 2：现有订单模型与前台订单耦合不足

降级：

- 在 `public_flow.py` 做适配层
- 不要立刻重写整个订单系统

### 风险 3：资料表单与现有脚本定义割裂

降级：

- 抽出统一 schema
- CLI / Web 共用同一字段定义

### 风险 4：报告交付链权限泄露

降级：

- 继续复用 `data/share` 权限控制
- 用户态报告访问必须绑定订单令牌或受控短链

---

## 8. 最短闭环路径（推荐执行顺序）

```text
T12.1 文档真相校准
  ↓
T12.2 前台入口
  ↓
T12.3 公开下单
  ↓
T12.4 支付域抽象
  ↓
T12.5 一个真实支付提供方
  ↓
T12.6 回调验签 + 幂等
  ↓
T12.7 资料填写页
  ↓
T12.8 后台接单处理
  ↓
T12.9 订单状态页 / 报告页
  ↓
T12.10 通知交付
  ↓
T12.11 退款与异常兜底
  ↓
T12.12 E2E 验收
```

---

## 9. 计划落地后的执行建议

建议下一步不要直接大面积编码，而是：

1. 先把 `T12.1` 做成文档真相校准 commit
2. 再单独开 `T12.2-T12.3`，把前台入口与公开下单先打通
3. 支付相关单独一条执行链，不与页面改造混在一个 commit 里
4. 每完成一个子阶段都做一次局部 E2E

---

## 10. 当前结论

- 当前项目已经完成 2.1 功能与 T5.5 门禁
- 新 goal 的正确下一步不是继续补后台，而是把 **场景 B：Web 自助闭环** 提升为正式主线 Epic
- 本计划建议把它落为 **T12 用户端 Web 自助 MVP**
- 如按此计划推进，项目对外口径可逐步从“人工服务运营增强系统”演进到“可用的 Web 自助志愿服务产品”
