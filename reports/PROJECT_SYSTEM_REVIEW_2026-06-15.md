<!-- 历史快照提示：本文件保留为历史审计材料，不再代表当前项目状态。 -->
> ⚠️ **历史快照（非当前真相源）**：本文件仅保留当时审查/收口结论。当前状态与执行顺序以 `docs/CURRENT_STATE.md`、`docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`、`docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`、`docs/plans/2026-07-05-review-remediation-systemic-fix-plan.md` 和 `reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md` 为准。

---

# gaokao-volunteer-system 系统性复审报告（2026-06-15）

**评审对象**: `/home/long/project/gaokao-volunteer-system`  
**复审基线**: `docs/CURRENT_STATE.md`（最后更新 2026-06-15）  
**评审方式**: 当前真相源复核 + 核心源码抽检 + 子系统专项复审 + 本地验证命令复核  
**评审标准**: 严格标准；重点看“真实闭环、数据安全、验证可信度、生产可运维性”  
**历史参照**: `reports/PROJECT_SYSTEM_REVIEW_2026-06-14.md`

---

## 1. 复审结论

**结论**：相较 2026-06-14，上轮多项高优先级工程问题已经真实收口，尤其是：

- 支付 webhook 双写裂缝已关闭
- 退款主链闭环已关闭
- webhook DB 按 `db_path` 隔离已关闭
- 删除/匿名化按当前声明范围已扩围
- 分享 allowlist 已落地
- portal token secret / payment webhook secret 的 prod fail-closed 已落地
- CI / dev-verify / coverage gate 的**本地硬门禁**已统一
- 备份恢复已从文件级升级到**本地服务级 restore smoke**

但按严格标准，项目**仍然不能被表述为“完整商业闭环系统”或“支付/灾备/合规都已完成生产验收”**。当前仍存在两类关键未闭环问题：

1. **真实生产闭环未完成**：真实支付宝 acceptance、公网 notify、生产 SMTP/IM、目标机备份恢复、异机灾备。
2. **新增或遗留的语义/暴露面风险**：portal 通知审计页暴露原始 payload、portal 上传附件未纳入删除/匿名化、`refund_pending` 死状态残留、通知底座仍保留 `sent` 旧语义。

**总体评级**：**工程基础明显增强，当前更接近“本地可验证的 v2.1 运营增强系统 + T12 在途”，但仍不应宣称生产级 Web 自助闭环已完成。**

---

## 2. 本次复审回答的核心问题

### 2.1 已确认关闭的旧问题

- P1-1 支付双写裂缝
- P1-4 webhook DB 连接污染
- P1-5 退款闭环
- P1-2 删除/匿名化扩围（按 CURRENT_STATE 声称范围）
- P1-6 分享 allowlist
- P2-1 孤儿订单
- P2-2 channel_sync DAO 真相收敛（实现层面）
- P2-4 portal token secret 分离
- P2-5 payment webhook secret fail-closed
- P1-7 覆盖率硬门禁本地统一
- P1-8 本地 restore smoke 升级为服务级验证

### 2.2 仍未关闭的旧问题

- P1-3 真实支付宝回调业务校验 / acceptance
- 生产备份恢复闭环
- 生产 SMTP / IM / 告警联调
- 前台正式隐私/删除/工单闭环

### 2.3 本次新增发现

- portal 通知审计页向持 token 用户暴露原始 payload，含邮箱与服务器绝对路径
- portal 上传附件未纳入删除/匿名化文件清理
- `refund_pending` 已退化为死状态，模型口径继续分裂
- 通知底座仍保留 `sent` 状态，P2-3 仅在 dispatcher / portal 主链层完成
- `CURRENT_STATE` 对 codecov 的“单一真相源”表述偏强；实质是数值对齐，不是执行单源
- Docker / Compose 仍是开发态模板，不能代表生产部署闭环
- 测试/脚本对子进程 PATH 有隐式依赖；直接 `.venv/bin/python -m pytest` 与激活 venv 后的 `python3`/`locust` 行为不同

---

## 3. 评审范围

### 3.1 文档

- `docs/CURRENT_STATE.md`
- `docs/P0_P1_P2_REMEDIATION_PLAN_2026-06-14.md`
- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `docs/PRODUCTION_DEPLOYMENT_CHECKLIST_2026-06-15.md`
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- `codecov.yml`
- `.github/workflows/ci.yml`
- `docker-compose.yml`
- `Dockerfile`

### 3.2 代码主链

- `data/payments/service.py`
- `data/payments/providers/alipay.py`
- `data/channel_sync/webhook_server.py`
- `data/orders/deletion_service.py`
- `data/share/permission.py`
- `data/notifications/dispatcher.py`
- `data/notifications/email_service.py`
- `admin/config.py`
- `admin/routes/web_public.py`
- `data/customer_portal/token.py`

### 3.3 关键测试样本

- `admin/tests/test_p2_4_p2_5_secrets.py`
- `admin/tests/test_order_deletion.py`
- `admin/tests/test_web_public.py`
- `admin/tests/test_payment_alipay_notify.py`
- `admin/tests/test_notification_audit_page.py`
- `data/payments/tests/test_webhook.py`
- `data/payments/tests/test_service.py`
- `data/payments/tests/test_refund_flow.py`
- `data/channel_sync/tests/test_webhook_server_db_scoping.py`
- `data/channel_sync/tests/test_single_dao_truth.py`
- `tests/test_backup_restore_service_level.py`
- `tests/test_coverage_gate_core.py`
- `tests/test_ops_alerts.py`
- `tests/test_delivery_notification.py`
- `tests/test_retention_cleanup.py`
- `tests/test_delivery_dispatcher.py`

---

## 4. 严重级别定义

- **P0**: 可直接导致系统失控/严重泄露/资金错误，且无现实缓解
- **P1**: 阻止生产闭环或存在显著数据/支付/隐私风险
- **P2**: 语义漂移、工程债务、生产边界不清或中等级暴露面
- **P3**: 已修复旧问题 / 正向发现 / 低优先改进项

---

## 5. 关键发现

## 5.1 P1：仍然成立的问题

### P1-1 真实支付宝回调校验与 acceptance 仍未闭环

**证据**

- `docs/CURRENT_STATE.md:25,79,142-145` 继续将真实支付 acceptance / P1-3 列为未完成阻塞项。
- `data/payments/service.py:189-215` 当前已校验：签名、`payment_id`、成功状态白名单、金额、`app_id`、`notify_id` 非空、`provider_trade_no` 非空。
- `data/payments/providers/alipay.py:97-110` 的标准化字段中仍没有 merchant/seller 维度。
- `docs/P0_P1_P2_REMEDIATION_PLAN_2026-06-14.md:223-234` 明确要求 `app_id / merchant / notify_id / 状态白名单 / 金额 / payment_id` 全校验。
- `admin/tests/test_payment_alipay_notify.py:30-136` 使用临时 RSA keypair 与 `https://example.com/...` 回调地址，仅证明本地闭环，不是商户实联。

**判断**

相较上轮，这一项已**部分修复**，但仍是当前最重要的生产阻塞项之一。当前代码不支持把“本地可测”升级表述成“真实支付闭环已完成”。

**风险**

- 真实商户/真实 notify 链尚无线上验收
- 缺 merchant/seller 绑定维度
- `notify_id` 只做非空校验，不是远端真实性证明

**结论**

正式报告必须继续把该项列为 **P1 未关闭**。

---

### P1-2 Portal 通知审计页向持 token 用户暴露原始通知 payload

**证据**

- `admin/routes/web_public.py:1148-1189` 的 `_render_notification_audit_page()` 直接渲染 `event.payload_json`。
- `data/orders/dao.py:583-595` 在交付事件中把 `audit_report` / `pdf_path` 写入 payload。
- `tests/test_delivery_notification.py:124-129` 明确断言 email event payload 中包含 `parent@example.com`。
- `admin/tests/test_notification_audit_page.py:47-85` 仅验证页面能显示事件，不校验敏感字段被裁剪。

**风险**

任何持有 portal token 的用户都可在 `/portal/{token}/notifications` 查看：

- 客户邮箱
- 交付物服务器绝对路径
- 原始通知 payload 细节

这扩大了暴露面，也泄露了服务器目录结构。

**结论**

这是本次复审最重要的**新增 P1**。

---

### P1-3 Portal 上传附件未纳入删除/匿名化文件清理

**证据**

- `admin/routes/web_public.py:286-303` `_store_portal_attachment()` 把附件写入 `portal_upload_dir/order_id/...`，并把 `storage_path` 写入 intake payload。
- `data/orders/deletion_service.py:49-69, 71-126, 157-166` 删除时仅删除 `audit_report` 与 `pdf_path`；匿名化仅清空 `payload_json`，不删除附件目录。
- `admin/tests/test_order_info_upload.py` 证明上传后的 `storage_path` 会真实落盘。

**风险**

数据库层面看似“已删除/已匿名化”，但磁盘上可能仍保留：

- 身份证/成绩单等高敏附件
- 其他 AI 方案或家庭信息材料

这会把“声明层已清理”与“真实文件仍在”重新撕裂开。

**结论**

这是隐私删除链上的**新增 P1**。

---

### P1-4 生产备份恢复仍未验收；当前只能证明本地 restore smoke 成立

**证据**

- `docs/BACKUP_AND_RECOVERY_PLAN.md:145-159,194-199` 明确承认：异机/异地备份、目标主机 timer、失败告警链、密钥轮换记录仍未闭环。
- `docs/PRODUCTION_DEPLOYMENT_CHECKLIST_2026-06-15.md:275-295` 把目标机 `backup_verify.sh --from-backup ...` 仍列为上线前待勾选项。
- `ops/systemd/gaokao-backup*.service|timer` 与 `ops/cron/gaokao-backup.crontab.example` 仅是样例，没有目标主机执行证据。

**风险**

当前仓库可以证明“本地可演练”，不能证明：

- 目标主机已持续生成可恢复快照
- 异机恢复已验证
- 密钥与配置已能回收

**结论**

这项应继续保留为 **P1 生产闭环缺口**。

---

### P1-5 备份定时任务没有失败告警闭环

**证据**

- `ops/systemd/gaokao-backup.service` / `gaokao-backup-verify.service` 仅有 `ExecStart`，未见 `OnFailure=`。
- `ops/cron/gaokao-backup.crontab.example` 只把输出写日志，不接 SMTP/IM/监控。
- `docs/BACKUP_AND_RECOVERY_PLAN.md:186-196` 流程图写到“告警”，但 `154-159` 又明确承认备份失败告警链未接入。

**风险**

备份或 restore smoke 失败时，当前样例部署只会留下日志，不会主动通知值班。

**结论**

这是备份链路上的 **P1 运维缺口**。

---

## 5.2 P2：新增风险 / 未完全收口的问题

### P2-1 `refund_pending` 已退化为死状态，模型口径继续分裂

**证据**

- `data/payments/dao.py` schema 仍允许 `refund_pending`
- `admin/routes/web_public.py:45-55` 仍渲染 `refund_pending`
- `data/payments/service.py:261-300` 实际退款入口已直接把 payment 更新为 `refunded`，无任何路径写入 `refund_pending`
- `data/payments/tests/test_refund_flow.py` / `test_service.py` 也已按直接 `refunded` 锁定

**风险**

这是死状态，不再是主链 bug，但会继续污染 UI、报表、维护者心智模型。

---

### P2-2 `sent` 旧语义仍残留在通知底座

**证据**

- `data/notifications/dispatcher.py` 已把 `station` 改为 `validated`，`email` 才进入 `delivered`
- 但 `data/notifications/email_service.py:29` 的 `DELIVERY_EVENT_STATUSES` 仍含 `sent`
- `mark_sent()` 仍可直接写入 `sent`，见 `data/notifications/email_service.py:131-151`
- `tests/test_delivery_notification.py` 仍把 `sent` 视作合法状态路径

**风险**

主链页面已纠偏，但底座状态空间仍允许旧语义复活。

---

### P2-3 `CURRENT_STATE` 对 codecov 的“单一真相源”表述偏强

**证据**

- `docs/CURRENT_STATE.md:54-57` 声称 `scripts/check_coverage_gate.py` 是单一真相源，CI/dev-verify/codecov 全部指向同一阈值。
- `codecov.yml:13-29` 实际上单独重复维护 target/threshold/patch target。
- `codecov.yml:6,18,45-47` 还显式表明它不是硬阻断门禁。

**风险**

这不是门禁失效问题，而是表述失真问题。更准确的说法应是：

- **CI 与本地硬门禁统一**
- **Codecov 仅与其保持同值显示口径，不是执行单源**

---

### P2-4 Docker / Compose 仍是开发态模板，不应视为生产部署闭环

**证据**

- `docker-compose.yml:9-18` 未编码 checklist 所要求的大量生产变量：`GAOKAO_PORTAL_TOKEN_SECRET`、支付回调、SMTP、告警变量等。
- `docker-compose.yml:10-14` 仍默认 `GAOKAO_ENV=dev` 且带 dev fallback。
- `Dockerfile` 只构建 admin 进程镜像，不包含 dispatcher/watchdog/backup 作业编排。
- `docs/PRODUCTION_DEPLOYMENT_CHECKLIST_2026-06-15.md:27-79` 明确把这些生产变量列为必备。

**风险**

现有 Compose 只能证明“开发环境可跑”，不能证明“生产最小闭环可跑”。

---

### P2-5 测试/脚本对子进程 PATH 有隐式依赖

**证据**

本次实际运行观察到：

```bash
./.venv/bin/python -m pytest admin/tests tests data -q
```

出现 7 个失败，主要为：

- `tests/test_delivery_dispatcher.py`
- `tests/test_retention_cleanup.py`
- `tests/test_t5_performance.py`

失败原因：

- 这些测试用 `subprocess.run(["python3", ...])` 或 `locust`，直接依赖 PATH 上的解释器/可执行文件。
- 未激活 venv 时，`python3` 会落到系统 Python，随后因 `admin.app -> import uvicorn` 失败。

而运行：

```bash
bash scripts/dev-verify.sh --skip-install
```

则 **717 passed**，因为脚本先 `source .venv/bin/activate`，PATH 被修正，子进程 `python3`/`locust` 都能解析到 venv 内可执行文件。

**风险**

这不是业务 bug，但说明验证闭环对“shell 激活 venv”有隐式前提；直接 `.venv/bin/python -m pytest` 还不够 hermetic。

---

## 5.3 P3：已确认关闭的旧问题 / 正向发现

### P3-1 支付双写裂缝已关闭

**证据**

- `data/payments/service.py:217-259` 在同一事务中同时推进 payment 与 order
- `data/payments/tests/test_service.py` 覆盖回滚场景
- 专项验证：`34 passed`

---

### P3-2 退款主链闭环已关闭

**证据**

- `data/payments/service.py:261-300` 在同一事务中推进 payment 与 order 到 `refunded`
- `data/payments/tests/test_refund_flow.py` / `test_service.py` 已锁定

---

### P3-3 webhook DB 隔离已关闭

**证据**

- `data/channel_sync/webhook_server.py:122-167` 改为按 `db_path` 缓存连接
- `data/channel_sync/tests/test_webhook_server_db_scoping.py` 覆盖多路径与并发场景

---

### P3-4 删除/匿名化按当前声明范围已扩围

**证据**

- `data/orders/deletion_service.py:71-125` 已覆盖 orders 主表、`payments.callback_payload`、`order_intakes.payload_json`
- `admin/tests/test_order_deletion.py` 已覆盖关键断言

**边界**

这只能证明“按 CURRENT_STATE 声称范围已修复”，**不等于完整合规闭环**。portal 上传附件仍未清理。

---

### P3-5 分享 allowlist 已收口

**证据**

- `data/share/permission.py:45-47, 85-173` edit/admin 均改为显式 allowlist
- 未知 permission 会 fail-safe 到 `read`
- `data/share/tests/test_permission.py` 已覆盖

---

### P3-6 portal token secret 分离与 payment webhook secret fail-closed 已落地

**证据**

- `admin/config.py` 已引入 `portal_token_secret` 与 prod 校验
- `admin/tests/test_p2_4_p2_5_secrets.py` 覆盖完整

---

### P3-7 覆盖率硬门禁本地统一已成立

**证据**

- `scripts/check_coverage_gate.py`
- `scripts/dev-verify.sh`
- `.github/workflows/ci.yml`
- `tests/test_coverage_gate_core.py`

---

### P3-8 本地 restore smoke 已从文件级升级到服务级

**证据**

- `scripts/backup_verify.sh`
- `scripts/backup_restore_smoke.py`
- `tests/test_backup_restore_service_level.py`
- `tests/test_backup_workflow.py`

---

### P3-9 watchdog → ops alert sink → 后台审计页本地链已存在

**证据**

- `scripts/gaokao-delivery-watchdog.py`
- `data/notifications/ops_alerts.py`
- `admin/routes/notifications.py`
- `tests/test_ops_alerts.py`
- `admin/tests/test_ops_alerts_admin.py`

**边界**

这证明本地底座存在；**不等于真实 SMTP/IM 与宿主机联调完成**。

---

## 6. 命令复核结果

### 6.1 全量直接 pytest（不激活 venv PATH）

执行：

```bash
./.venv/bin/python -m pytest admin/tests tests data -q
```

结果：**7 failed，710 passed**。

主要失败原因：

- `tests/test_delivery_dispatcher.py` / `tests/test_retention_cleanup.py` 中子进程调用 `python3`，落到系统解释器，触发 `ModuleNotFoundError: uvicorn`
- `tests/test_t5_performance.py` 依赖 `locust` 可执行文件在 PATH 中可见

### 6.2 仓库标准验证入口

执行：

```bash
bash scripts/dev-verify.sh --skip-install
```

结果：**通过**，关键输出：

- `717 passed`
- `coverage gate summary: overall=92.59%, core=100.00%`
- `ruff`: 通过
- `mypy`: `Success: no issues found in 187 source files`

### 6.3 解释

- 仓库声明的标准入口 `dev-verify.sh` 当前是可通过的。
- 但验证闭环依赖 `source .venv/bin/activate` 改写 PATH；测试本身仍不够完全自描述。
- 这更像“验证入口已统一，但底层 shell 假设仍存在”。

---

## 7. 最终判断

### 可以确认的事实

1. 上轮多项工程性 P1/P2 已真实修复，不应再按“当前未修复”表述。
2. 当前版本已经明显强于 2026-06-14 的状态，尤其在事务一致性、安全 fail-closed、本地恢复演练方面。
3. 但项目**仍不能**宣称：
   - 真实支付闭环已完成
   - 灾备已完成生产验收
   - 合规删除链已完整闭环
   - 通知/交付语义已完全收敛

### 当前最关键的未闭环项

按风险排序：

1. **真实支付宝回调业务校验 + 线上 acceptance**
2. **portal 通知审计页 payload 直出导致的敏感信息暴露**
3. **portal 上传附件未纳入删除/匿名化文件清理**
4. **生产备份恢复 / 失败告警 / 目标机验收缺失**
5. **`refund_pending` / `sent` 等残留死语义收敛**
6. **Docker / Compose 与生产 checklist 的边界澄清**

### 一句话结论

> 当前仓库已经完成一轮真实有效的工程收敛，属于“本地可验证的 v2.1 运营增强系统 + T12 在途”，但仍不是可以对外宣称“生产级 Web 自助支付/交付/灾备/合规全闭环”的系统。
