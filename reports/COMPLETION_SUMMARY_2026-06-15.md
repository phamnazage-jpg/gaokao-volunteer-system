# 本轮完成项摘要报告（2026-06-15）

## 1. 目标

本轮工作围绕 2026-06-15 系统复审报告中的 P1 / P2 整改项展开，目标是优先收口仓库内可以真实落地并可验证的风险，而不是继续停留在“文档承诺”或“计划状态”。

本轮特别聚焦四类问题：

1. portal 公开面敏感信息暴露
2. 删除 / 匿名化链路中的文件残留
3. 支付与通知域中的残留死语义
4. 隐私 / 删除入口与目标机恢复验收准备不足

## 2. 已完成项

### 2.1 Portal 通知审计页不再暴露原始 payload

已修改：

- `admin/routes/web_public.py`
- `admin/tests/test_notification_audit_page.py`

结果：

- portal 通知页不再直出 `payload_json`
- 不再向持 token 用户暴露邮箱、报告绝对路径、PDF 路径
- 页面仅保留通知摘要字段

### 2.2 删除 / 匿名化链路补齐 portal 上传附件清理

已修改：

- `data/orders/deletion_service.py`
- `admin/tests/test_order_deletion.py`

结果：

- `delete` 会删除 portal 上传附件
- `anonymize` 也会清理 portal 上传附件
- 空附件目录会一起删除
- 数据库 payload 仍会被清空

### 2.3 通知域移除 `sent` 旧语义

已修改：

- `data/notifications/email_service.py`
- `tests/test_delivery_notification.py`

结果：

- `DELIVERY_EVENT_STATUSES` 已移除 `sent`
- `mark_sent()` 已删除
- 测试切换为 `validated / delivered / failed`

### 2.4 支付域移除 `refund_pending` 死状态

已修改：

- `data/payments/dao.py`
- `data/payments/service.py`
- `admin/routes/web_public.py`
- `data/payments/tests/test_refund_flow.py`

结果：

- payment schema 不再包含 `refund_pending`
- portal 状态推导不再依赖 `refund_pending`
- 退款路径统一为真实可达的 `refunded`

### 2.5 支付回调补齐仓库内可落地的商户维度校验

已修改：

- `admin/config.py`
- `data/payments/provider_requirements.py`
- `data/payments/service.py`
- `data/payments/providers/alipay.py`
- `admin/routes/web_public.py`
- `admin/tests/test_payment_alipay_notify.py`
- `data/payments/tests/test_provider_requirements.py`
- `data/payments/tests/test_provider_alipay.py`
- `data/payments/tests/test_webhook.py`

结果：

- 新增 `GAOKAO_PAYMENT_MERCHANT_ID`
- readiness 检查要求 merchant 维度
- webhook 归一化 payload 新增 `merchant_id`
- webhook 处理新增 merchant missing / mismatch 校验

说明：

- 这只完成仓库内能力补齐
- 真实公网 acceptance 仍需外部商户凭据、notify 域名和目标环境

### 2.6 测试子进程调用改为 hermetic

已修改：

- `tests/test_retention_cleanup.py`
- `tests/test_delivery_dispatcher.py`
- `tests/test_t5_performance.py`

结果：

- 子进程 `python3` 调用改为 `sys.executable`
- Locust 调用改为 `python -m locust`
- 直接 `./.venv/bin/python -m pytest ...` 不再因 PATH 分裂失败

### 2.7 隐私 / 删除前台入口与后台审计页已补齐

已修改：

- `admin/routes/web_public.py`
- `admin/routes/notifications.py`
- `admin/config.py`
- `admin/tests/conftest.py`
- `admin/tests/test_web_public.py`
- `admin/tests/test_order_info_form.py`
- `admin/tests/test_notifications_admin.py`

结果：

新增公开页面：

- `/privacy`
- `/service-terms`
- `/deletion-policy`

新增 portal 删除申请最小闭环：

- `GET /portal/{token}/deletion-request`
- `POST /portal/{token}/deletion-request`

新增留痕与后台审计：

- `GAOKAO_DELETION_REQUEST_LOG`
- `GET /api/admin/notifications/deletion-requests`
- `GET /admin/deletion-requests`

### 2.8 目标机恢复验收准备已落成可执行模板

已修改：

- `reports/DR_DRILL_TEMPLATE.md`
- `tests/test_backup_workflow.py`
- `docs/BACKUP_AND_RECOVERY_PLAN.md`

结果：

- 新增 DR drill 模板，可记录目标主机 / 异机恢复结果
- 测试锁定模板必须引用 `backup_verify.sh --from-backup`
- 文档已明确真实演练记录归档位置

### 2.9 文档边界同步收口

已修改：

- `docs/CURRENT_STATE.md`
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `docker-compose.yml`

结果：

- codecov 改为“同值展示口径”，不再误写成执行单源
- `sent` / `refund_pending` 旧口径已移除或修正
- Compose 文件头已明确其仅是开发 / 本地 smoke 模板
- backup 文档不再伪装目标机告警已经完成

## 3. 验证结果

### 3.1 针对性测试

执行过的关键针对性回归包括：

- `admin/tests/test_notification_audit_page.py`
- `admin/tests/test_order_deletion.py`
- `tests/test_delivery_notification.py`
- `data/payments/tests/test_provider_requirements.py`
- `data/payments/tests/test_provider_alipay.py`
- `data/payments/tests/test_webhook.py`
- `admin/tests/test_payment_alipay_notify.py`
- `data/payments/tests/test_refund_flow.py`
- `data/payments/tests/test_service.py`
- `tests/test_retention_cleanup.py`
- `tests/test_delivery_dispatcher.py`
- `tests/test_t5_performance.py`
- `tests/test_backup_workflow.py`
- `admin/tests/test_web_public.py`
- `admin/tests/test_order_info_form.py`
- `admin/tests/test_notifications_admin.py`

其中最后一次定向回归结果：

- `23 passed`

### 3.2 标准验证入口

执行：

```bash
bash scripts/dev-verify.sh --skip-install
```

结果：

- `730 passed`
- `coverage overall = 92.70%`
- `coverage core = 100.00%`
- `ruff` 通过
- `mypy` 无错误

## 4. 本轮未在仓库内伪完成的外部阻塞

以下事项仍依赖仓库外条件，本轮没有伪装为“已完成”：

1. 真实支付宝公网 acceptance
   - 仍需真实商户凭据、公网 `notify_url`、真实域名和线上演练记录
2. 目标机真实 backup / restore 演练
   - 当前只完成模板与准备，不代表目标机已跑过
3. 目标机真实 SMTP / webhook 告警联调
   - 当前仓库只保留真实边界说明，没有伪造不存在的 backup alert service
4. 正式法务文本最终签发
   - 当前仓库已补入口与流程，但不等于外部法务审批流程已经结束

## 5. 结论

本轮工作已经把“可在仓库内真实完成并验证”的整改项全部落地。系统状态从“复审指出的问题已确认存在”推进到“主风险项已逐步切成两类”：

- **仓库内已修复并可回归验证的工程问题**
- **必须依赖外部环境、目标主机或正式业务输入才能闭环的上线前阻塞**

因此，当前仓库可以更准确地表述为：

> 已完成一轮真实工程收敛，仓库内可验证整改项已落地并通过标准验证入口；剩余阻塞集中在真实支付 acceptance、目标机 DR 演练、真实告警联调和正式外部文本签发。