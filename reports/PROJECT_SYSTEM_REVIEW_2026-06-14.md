# gaokao-volunteer-system 系统性 Review 报告（2026-06-14）

> 历史快照（2026-06-14）。当前真相源请优先阅读：`docs/CURRENT_STATE.md` → `docs/ACTIVE_EXECUTION_BOARD_2026-06-13.md` → `docs/ACTIVE_REMEDIATION_2026-06-13.md` → `docs/P0_P1_P2_REMEDIATION_PLAN_2026-06-14.md`。

**评审对象**: `/home/long/project/gaokao-volunteer-system`
**评审方式**: 当前文档真相核对 + 关键源码结构审查 + 安全/测试/运维专项审查 + 本地门禁复核
**评审标准**: 严格标准；以"真实业务闭环、数据安全、验证可信度、可运维性"为主轴
**当前真相源**: `docs/CURRENT_STATE.md`

---

## 1. 结论

**结论**：项目已经具备较完整的“运营后台 + 订单 + 支付抽象 + portal + 分享 + 渠道同步 + 交付事件”骨架，核心订单状态机与 DAO 边界也明显优于很多同规模项目；但按严格标准看，**系统仍未达到“关键链路一致性可靠、支付/删除/交付语义闭环、质量门禁可信、灾备与部署可验证”的稳态**。

**总体评级**：**有明显工程基础，但不建议把当前版本描述为“已完成的、可放心放量的商业闭环系统”**。

**最重要判断**：

1. **订单/支付/退款/交付**仍有多处语义裂缝，主系统真相源不统一。
2. **隐私删除/匿名化**与文档承诺不一致，存在误报“已匿名化/已删除”的合规风险。
3. **CI / 本地 / coverage gate / Docker / 备份恢复**没有形成一致、可复现、可证明的验证链。
4. **支付回调与分享公开面**仍有显著安全收敛空间。

本次未发现必须立即停机级别的 **P0** 远程利用证据，但存在多项 **P1**，足以阻止“系统已成熟闭环”的结论。

---

## 2. 评审范围

### 2.1 文档与约束

- `README.md`
- `docs/CURRENT_STATE.md`
- `docs/LEGAL_PRIVACY_BASELINE.md`
- `docs/DATA_RETENTION_AND_DELETION.md`
- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `docs/DELIVERY_SERVICE_DESIGN.md`
- `docker-compose.yml`
- `Dockerfile`
- `.github/workflows/ci.yml`
- `codecov.yml`
- `pytest.ini`
- `scripts/dev-verify.sh`
- `scripts/backup_verify.sh`
- `scripts/check_coverage_gate.py`

### 2.2 核心代码链路

- `admin/app.py`
- `admin/auth.py`
- `admin/config.py`
- `admin/password.py`
- `admin/db.py`
- `admin/routes/auth.py`
- `admin/routes/orders.py`
- `admin/routes/web_public.py`
- `data/orders/dao.py`
- `data/orders/state_machine.py`
- `data/orders/public_flow.py`
- `data/orders/deletion_service.py`
- `data/orders/intake_store.py`
- `data/orders/crypto.py`
- `data/orders/masking.py`
- `data/payments/service.py`
- `data/payments/dao.py`
- `data/payments/providers/alipay.py`
- `data/payments/providers/alipay_sim.py`
- `data/channel_sync/webhook_server.py`
- `data/share/permission.py`
- `data/customer_portal/token.py`
- `data/notifications/dispatcher.py`

### 2.3 测试与验证样本

- `admin/tests/test_web_public_alipay_sim_e2e.py`
- `admin/tests/test_order_status_page.py`
- `admin/tests/test_routes_orders.py`
- `data/payments/tests/test_webhook.py`
- `tests/test_delivery_dispatcher.py`
- `tests/test_retention_cleanup.py`
- `tests/test_t5_performance.py`

---

## 3. 严重级别定义

- **P0**: 已存在可直接导致系统失控/严重数据泄漏/资金错误且缺乏现实缓解
- **P1**: 高优先级问题；会破坏主链路一致性、支付/隐私/恢复可信度，阻止成熟上线结论
- **P2**: 中优先级问题；不会立即击穿主链，但会持续积累运维、测试或安全债务
- **P3**: 正向亮点或低优先改进项

---

## 4. 关键问题清单

## 4.1 P1 问题

### P1-1 支付回调存在双写裂缝：payment 已记 paid，但 order 可能未推进

**证据**

- `data/payments/service.py::PaymentService.handle_webhook()` 先更新 `payments.status=paid`
- `data/payments/dao.py::PaymentDAO.update_status()` 内部立即 `commit`
- 随后才在新的 `OrdersDAO` 上下文里把订单从 `pending` 推到 `paid`

**风险**

这是典型跨表双写一致性问题。任一时刻如果支付表提交成功、订单推进失败（订单异常、锁冲突、状态先被别处推进、进程中断），系统会留下：

- `payments.status = paid`
- `orders.status != paid`

之后 portal、退款、统计、人工判断都会基于不同真相源工作。

**结论**

这是当前最重要的业务一致性问题之一。

---

### P1-2 删除/匿名化与文档承诺不一致，存在“看起来已删，实际上没删”的合规风险

**证据**

- `docs/DATA_RETENTION_AND_DELETION.md` 要求订单、资料提交、报告文件、通知/支付审计都应清理或匿名化
- `data/orders/deletion_service.py::OrderDeletionService.anonymize_order()` 仅更新 `orders` 主表部分字段
- 未覆盖：
  - `data/orders/intake_store.py` 中 `order_intakes.payload_json`
  - `data/payments/dao.py` 中 `payments.callback_payload`
  - `audit_report` / `pdf_path` 对应文件

**风险**

系统当前容易把“订单主表去标识化”误报成“订单数据已匿名化完成”。对于高考场景中的未成年人/监护人资料，这是明显不够的。

**结论**

当前删除/匿名化能力不足以支撑强隐私合规表述。

---

### P1-3 真实支付宝回调校验过弱，只验签 + 金额，不校验应用/商户/状态边界

**证据**

- `admin/routes/web_public.py` 的 `/api/public/payments/alipay/notify` 直接把表单解析结果交给 `PaymentService.handle_webhook()`
- `data/payments/service.py::handle_webhook()` 只校验：签名、`payment_id`、金额一致
- `data/payments/providers/alipay.py` 仅标准化 `out_trade_no/trade_no/total_amount/trade_status` 并做 RSA 验签
- 未见对 `app_id`、商户标识、允许状态白名单、`notify_id`、`gmt_payment` 等做二次校验

**风险**

系统会把“签名有效且金额匹配”的回调近似当成“业务上确认为成功支付”。这对真实支付系统不够。

**结论**

真实支付回调仍未达到严格上线标准。

---

### P1-4 Webhook server 的数据库连接缓存按模块全局单例保存，且不区分 `db_path`

**证据**

- `data/channel_sync/webhook_server.py` 中 `_DB_CONN` 为模块级单例
- `_get_db(db_path)` 只在 `_DB_CONN is None` 时首次打开连接；后续不同 `db_path` 直接复用旧连接
- `make_server(..., db_path=...)` 虽允许传不同库路径，但连接缓存不会切换

**风险**

同一进程先后启动多个 webhook server / 测试实例 / 不同 DB 场景时，后者可能静默写入前一个库。问题隐蔽，影响审计、幂等和订单入库正确性。

**结论**

这是高风险的状态污染问题。

---

### P1-5 退款域模型未闭环：状态机有 `refunded`，支付服务只把 payment 记到 `refund_pending`

**证据**

- `data/orders/state_machine.py` 支持订单进入 `refunded` 终态
- `data/payments/service.py::request_refund()` 仅把 payment 更新到 `refund_pending`
- 未见生产调用路径把订单主状态同步推进到 `refunded`
- `admin/routes/web_public.py` portal 阶段判断优先看 payment 的退款状态，而不是订单主状态

**风险**

订单域与支付域的退款真相源分裂。之后交付限制、统计、保留期清理、人工判断都可能不一致。

**结论**

退款闭环目前不完整。

---

### P1-6 公开分享 `edit/admin` 权限是 allow-by-default，未来新增字段极易外泄

**证据**

- `data/share/permission.py` 中 `edit/admin` 的 `visible_fields=None`
- `render_report_payload()` 在该模式下除 denylist 外默认全部透传
- `_ALWAYS_HIDDEN_FIELDS` 仅覆盖少数内部字段，不覆盖未来可能新增的手机号、身份证、顾问备注等

**风险**

一旦报告 payload 新增敏感字段，公开分享链接可能自动带出这些信息，而不需要任何显式审批。

**结论**

分享策略对未来演进不够安全。

---

### P1-7 覆盖率门禁口径互相冲突，验证链本身不可信

**证据**

- `.github/workflows/ci.yml`：`--cov-fail-under=60`
- `scripts/dev-verify.sh`：`--cov-fail-under=80`
- `scripts/check_coverage_gate.py`：`overall=80%`、`core=100%`
- `codecov.yml`：也声明整体 80%、核心 100%

**风险**

同一改动可能出现：

- CI 通过
- 本地失败
- codecov 标准不同
- gate 脚本又给出另一套结论

这种门禁不稳定，会持续削弱团队对测试结论的信任。

**结论**

当前质量门禁存在制度级不一致。

---

### P1-8 备份恢复只做到“复制文件 + 打印表名”，还不是恢复演练

**证据**

- `docs/BACKUP_AND_RECOVERY_PLAN.md` 自认仅是“最小恢复基线”，并明确尚无自动化恢复验证
- `scripts/backup_verify.sh` 只复制 DB / 文件，然后验证 SQLite 文件可打开、文件可枚举
- 未见 CI 或自动化测试真正执行“恢复后启动应用并验证 portal / 订单 / 报告”

**风险**

当前只能证明“文件能拷贝”，不能证明“系统能恢复并可用”。这对任何需要对外交付或数据保留承诺的系统都不够。

**结论**

灾备能力目前停留在文档与文件级验证，不是服务级验证。

---

## 4.2 P2 问题

### P2-1 公共下单先写订单、后建支付，失败时会遗留孤儿 `pending` 订单

**证据**

- `admin/routes/web_public.py::create_public_order_endpoint()` 先 `create_public_order()`，再 `PaymentService.create_checkout()`
- `data/orders/public_flow.py` 直接先把订单写入库
- `data/payments/service.py::create_checkout()` 再独立创建 payment

**风险**

支付初始化失败时，用户请求失败，但库里已经有订单，且没有补偿动作。

---

### P2-2 渠道同步仍在走已声明被替代的 `dao_extension`，存在双实现漂移风险

**证据**

- `data/orders/dao.py` 已提供 `OrdersDAO.upsert_by_external_id()`
- `data/channel_sync/webhook_server.py` 与 `data/channel_sync/poller.py` 仍直接使用 `data.channel_sync.dao_extension.upsert_by_external_id`

**风险**

同一业务规则同时存在两套实现，后续修改很容易只修一套。

---

### P2-3 交付执行器把“文件存在”直接标记为 `sent`，语义过度乐观

**证据**

- `data/notifications/dispatcher.py::dispatch_ready_events()` 校验文件存在后直接 `mark_sent`
- `docs/DELIVERY_SERVICE_DESIGN.md` 又明确说明“邮件/渠道真实发送执行器”尚未完成

**风险**

`sent` 更像“已投递成功”，但当前实际含义只是“本地文件通过检查”。这会误导运营状态与告警语义。

---

### P2-4 Portal token 与后台 JWT 共用同一根 secret

**证据**

- `admin/routes/web_public.py` 创建和校验 portal token 时使用 `settings.jwt_secret`
- `data/customer_portal/token.py` 是独立 HMAC token 格式
- `admin/auth.py` 后台 JWT 也使用同一 secret

**风险**

轮换、隔离、泄露影响面都被耦合，不符合边界最小化原则。

---

### P2-5 payment webhook secret 仍有固定开发默认值，启动阶段也没有 prod fail-closed 校验

**证据**

- `admin/config.py` 默认 `GAOKAO_PAYMENT_WEBHOOK_SECRET=dev-mock-payment-secret`
- `data/payments/service.py::for_db()` 也带同样默认值
- `admin/app.py` 启动只校验 JWT secret 与默认管理员密码，没有校验 payment webhook secret

**风险**

在 mock / alipay_sim 场景中，如果配置漂移到公网环境，伪造回调成本会明显降低。

---

### P2-6 pytest 把 `data/` 直接纳入测试发现根，测试边界偏混杂

**证据**

- `pytest.ini`: `testpaths = admin/tests tests data`
- CI 也直接跑 `pytest admin/tests tests data`

**风险**

业务代码目录与测试入口绑定过紧，不利于区分 unit / integration / e2e / script verification 的语义。

---

### P2-7 部署链只有单容器存活探测，没有业务冒烟、恢复验证、监控告警闭环

**证据**

- `docker-compose.yml` 仅定义一个服务、一个数据卷、一个 `/health` healthcheck
- `Dockerfile` 仅安装运行依赖并直接启动 `admin.app`
- 文档里有监控设计，但未见对应自动化验证或可运行集成

**风险**

当前最多只能说明“进程活着”，不能说明“关键业务链在部署后可用”。

---

## 4.3 P3 亮点

### P3-1 OrdersDAO 把状态机、时间戳、历史记录、交付触发收敛到一条主写路径

**证据**

- `data/orders/dao.py::transition_status()` 单事务处理：状态校验、状态更新、history、时间戳
- `delivered` 且交付物齐备时会顺带落 `delivery_notifications`

**评价**

这是当前仓库最稳的边界之一。它明显优于把状态历史散落在各个 route/service 中维护。

---

### P3-2 FastAPI app 装配较整洁，配置校验与 schema 初始化集中在启动期

**证据**

- `admin/app.py::create_app()` 结构清晰
- `_validate_and_log_settings()` 对 JWT / 默认管理员密码做环境分级处理
- `_setup_database()` 统一做 schema/bootstrap

**评价**

应用装配层没有明显失控，是后续继续治理的好基础。

---

### P3-3 管理员密码与分享密码使用 PBKDF2 + 随机盐 + 恒时比较

**证据**

- `admin/password.py`
- `data/share/short_link.py`

**评价**

密码存储方案比很多轻量项目更稳，属于正向设计。

---

### P3-4 登录失败统一口径，且已有基础限流

**证据**

- `admin/routes/auth.py` 以 `username@client_ip` 做失败计数与 `retry_after`
- 普通错误统一返回 `AUTH_INVALID_CREDENTIALS`

**评价**

已具备最低限度的暴力破解缓解与账户枚举抑制。

---

## 5. 验证与复核结果

### 5.1 命令复核

在仓库根执行了以下检查：

```bash
python3 -m pytest admin/tests tests data -q
python3 -m ruff check . --exclude .venv,.worktrees
python3 -m mypy .
python3 scripts/check_coverage_gate.py coverage.xml

./.venv/bin/python -m pytest admin/tests tests data -q
./.venv/bin/python -m ruff check . --exclude .venv,.worktrees
./.venv/bin/python -m mypy .
./.venv/bin/python scripts/check_coverage_gate.py coverage.xml
```

### 5.2 观察到的结果

1. **系统 Python 环境**缺少 `pytest / ruff / mypy`，全局命令不可直接复现。
2. **`.venv` 环境下**：
   - `pytest`: **639 passed, 5 failed**
   - 失败主要来自：
     - `tests/test_delivery_dispatcher.py`
     - `tests/test_retention_cleanup.py`
     - `tests/test_t5_performance.py`
3. 失败原因并非随机：
   - 若测试通过 `subprocess.run(["python3", ...])` 启动脚本，脚本会落到系统 Python，随后因 `admin.__init__ -> admin.app -> import uvicorn` 报 `ModuleNotFoundError: uvicorn`
   - `locust` 可执行文件缺失，导致性能测试无法启动
4. `ruff check`：**通过**
5. `mypy`：未见硬错误输出，但存在 **8 条 `annotation-unchecked` 提示**，集中在测试文件
6. `scripts/check_coverage_gate.py coverage.xml`：**失败**，报 `missing core coverage entries`，说明当前 coverage artifact 与 gate 脚本的核心文件映射未对齐。

### 5.3 这组结果说明什么

- 项目不是“完全不可测”，因为大部分测试可在 `.venv` 中通过。
- 但它也**不是稳定可复现的验证闭环**：
  - 脚本子进程环境与测试 runner 环境脱节
  - 性能验证依赖工具未稳定声明/注入
  - coverage gate 与覆盖率产物不一致

这与前述 P1/P2 结论一致：**系统已有工程基础，但门禁可信度仍不够强。**

---

## 6. 优先级建议

## 第一优先级（立即处理）

1. **修复支付 webhook 的双写一致性问题**
2. **补齐删除/匿名化的真实覆盖范围，统一 delete vs anonymize 语义**
3. **补强真实支付宝回调业务校验**
4. **修复 webhook server 的全局 DB 连接污染问题**
5. **统一 coverage / CI / 本地 gate 口径**

## 第二优先级（短期完成）

6. **完成退款主状态闭环**
7. **把分享权限改为 allowlist，而不是 edit/admin 全量透传**
8. **拆分 portal secret 与 admin JWT secret**
9. **为 payment webhook secret 增加生产环境启动门禁**
10. **把渠道同步彻底 cutover 到 `OrdersDAO.upsert_by_external_id()`**

## 第三优先级（中期治理）

11. **把交付状态拆成“已验证可投递”与“真实已发送”**
12. **补真实 restore drill / Docker 业务冒烟 / 监控告警最小闭环**
13. **收紧 pytest 入口，明确 unit/integration/e2e 语义边界**

---

## 7. 最终判断

如果问题是：

> 这个仓库有没有认真做工程？

答案是：**有，而且部分核心边界（尤其 orders DAO / 状态机）做得不错。**

如果问题是：

> 这个系统是否已经达到“关键闭环可信、合规表述稳妥、验证链稳定、运维可托底”的严格标准？

答案是：**还没有。**

更准确的表述应当是：

> 这是一个已经具备明显产品化骨架、但仍处于“关键一致性 / 支付安全 / 删除合规 / 验证闭环 / 灾备落地”强化期的系统。当前适合继续收敛与修复，不适合对外宣称为完全成熟闭环。
