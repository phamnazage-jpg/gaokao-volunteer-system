# SYSTEM_REVIEW_REMEDIATION_PLAN_2026-06-14

生成时间: 2026-06-14
来源报告: `reports/PROJECT_SYSTEM_REVIEW_2026-06-14.md`
适用范围: 仅保留“当前真实有效且需要处理”的问题
真相源: `docs/CURRENT_STATE.md`

---

## 1. 当前门禁结论

结论: 条件通过 / 需要整改后再宣称“成熟商业闭环系统”

说明:

- 对“人工服务运营增强系统 v2.1 已完成”这一表述：仍成立
- 对“可放心放量的完整商业闭环系统”这一表述：当前不成立
- 本次整改计划只保留 2026-06-14 复审中**仍然有效**的问题，不再重复 2026-06-13 已修复项

禁止错误表述:

- ❌ “支付闭环已完全成熟”
- ❌ “删除/匿名化已完整满足合规”
- ❌ “验证链已经完全可信”
- ❌ “灾备已经完成恢复演练”

允许表述:

- ✅ “v2.1 已完成后台运营链路与 AI 审核增强闭环”
- ✅ “支付/删除/交付/恢复仍有高优先级整改项”

---

## 2. 只保留仍然有效的问题

### P1（必须优先修）

1. 支付回调双写裂缝
2. 删除/匿名化与文档承诺不一致
3. 支付回调校验过弱
4. webhook server 全局 DB 连接污染风险
5. 退款域模型未闭环
6. 分享 edit/admin 默认全透传风险
7. 覆盖率/CI/codecov/dev-verify 门禁口径冲突
8. 备份恢复不是服务级恢复演练

### P2（应在下一轮收敛）

9. 公共下单先写订单再建支付，失败留孤儿订单
10. channel_sync 仍走被替代的 dao_extension
11. delivery dispatcher 把“文件存在”标记为 sent
12. portal token 与后台 JWT 共用同一根 secret
13. payment webhook secret 有开发默认值且未 fail-closed
14. 历史快照文档仍需统一标注，避免再次漂移

---

## 3. 最短整改路径（按风险收益排序）

### 第一阶段：先修“真相一致性”

目标:

- 保证订单/支付/退款/交付的业务真相不分裂

进度:

- ✅ P1-1 支付回调双写裂缝已修复（Payment 与 Order 状态推进收敛到同一事务）
- ✅ P1-5 退款域模型闭环已修复（payment.status 一步收敛到 `refunded`，并把订单推进到 refunded 终态；幂等请求会自愈）

顺序:

1. P2-1 公共下单孤儿订单
2. P2-3 delivery `sent` 语义修正

### 第二阶段：再修“合规与安全边界”

目标:

- 减少真实合规风险和公开面风险

顺序: 5. P1-2 删除/匿名化不完整 6. P1-3 支付回调校验过弱 7. P1-6 分享 edit/admin 全透传风险 8. P2-4 portal token / JWT secret 分离 9. P2-5 payment webhook secret fail-closed

### 第三阶段：最后修“验证链可信度”

目标:

- 保证后续再 review 不会因门禁口径不一致而反复漂移

顺序: 10. P1-7 覆盖率/CI/codecov/dev-verify 统一 11. P1-8 备份恢复服务级演练 12. P2-2 channel_sync 单一 DAO 真相 13. P2-14 历史快照统一头注

---

## 4. 详细整改任务板

### P1-1 支付回调双写裂缝

严重度: P1
Owner: engineer
状态: pending

问题:

- `PaymentService.handle_webhook()` 先提交 payment，再在另一上下文推进 order
- 一旦第二步失败，会留下 `payments.status=paid` 但 `orders.status!=paid`

目标:

- 支付成功与订单推进必须成为单一业务事务，至少形成可补偿的强一致流程

交付物:

- `docs/plans/P1-1-payment-consistency.md`
- 代码修复：`data/payments/service.py`, `data/payments/dao.py`, `data/orders/dao.py`
- 新测试：`data/payments/tests/test_webhook_consistency.py`

完成标准:

- 回调处理不再跨两个独立 commit 真相源
- 如果 order 推进失败，payment 不能被误判为最终 paid
- 或者必须记录明确补偿状态（如 `payment_pending_reconcile`）

验证:

- 构造 payment 成功 / order 失败场景，验证系统不会留下分裂状态

---

### P1-2 删除/匿名化不完整

严重度: P1
Owner: engineer + PM
状态: pending

问题:

- 订单主表去标识化不等于完整匿名化
- `order_intakes.payload_json` / `payments.callback_payload` / 报告文件未同步清理

目标:

- 删除/匿名化逻辑与文档承诺一致

交付物:

- `docs/plans/P1-2-deletion-anonymization-closure.md`
- 代码修复：`data/orders/deletion_service.py`, `data/orders/intake_store.py`, `data/payments/dao.py`
- 文档修订：`docs/DATA_RETENTION_AND_DELETION.md`

完成标准:

- 主表、资料提交、支付回调、报告文件、通知痕迹都纳入处理策略
- 文档明确“删除/匿名化”的真实语义，不再误报

验证:

- 构造一条完整订单，执行删除/匿名化后核查所有关联存储

---

### P1-3 支付回调校验过弱

严重度: P1
Owner: engineer
状态: pending

问题:

- 当前只校验签名 + 金额，不校验 `app_id` / 商户标识 / 允许状态边界等

目标:

- 回调必须达到真实业务校验标准，而不是“签名合法即接受”

交付物:

- `docs/plans/P1-3-payment-webhook-hardening.md`
- 代码修复：`admin/routes/web_public.py`, `data/payments/service.py`, `data/payments/providers/alipay.py`
- 新测试：`data/payments/tests/test_webhook_hardening.py`

完成标准:

- app_id / merchant / notify_id / 状态白名单 / 金额 / payment_id 全校验
- 非法字段或状态必须拒绝

验证:

- 伪造 app_id、错商户、错状态、重复 notify 场景测试全通过

---

### P1-4 webhook server 全局 DB 连接污染

严重度: P1
Owner: engineer
状态: pending

问题:

- `_DB_CONN` 模块级单例不区分 `db_path`
- 不同实例可能写到同一个库

目标:

- 连接必须按 `db_path` 隔离，或改为每 server instance 自持连接

交付物:

- `docs/plans/P1-4-webhook-db-scope.md`
- 代码修复：`data/channel_sync/webhook_server.py`
- 新测试：多 db_path 场景测试

完成标准:

- 不同 `db_path` 的 server 互不污染

验证:

- 启动两个不同库实例，分别写入并验证库隔离

---

### P1-5 退款域模型未闭环

严重度: P1
Owner: engineer
状态: pending

问题:

- payment 到 `refund_pending`，但 order 未形成 `refunded` 统一主状态

目标:

- 退款真相源统一，订单域与支付域不再分裂

交付物:

- `docs/plans/P1-5-refund-state-closure.md`
- 代码修复：`data/payments/service.py`, `data/orders/state_machine.py`, `admin/routes/web_public.py`

完成标准:

- 退款成功时，订单主状态与支付状态一致可追踪

验证:

- portal / 订单详情 / 统计使用同一退款真相

---

### P1-6 分享 edit/admin 默认透传风险

严重度: P1
Owner: engineer
状态: pending

问题:

- `visible_fields=None` 导致未来新增敏感字段可能自动外泄

目标:

- edit/admin 也必须改为 allowlist，而不是 denylist

交付物:

- `docs/plans/P1-6-share-field-allowlist.md`
- 代码修复：`data/share/permission.py`
- 新测试：新增敏感字段不应自动出现在公开 payload

完成标准:

- 所有权限模式都基于显式字段白名单

验证:

- 向 payload 加入新敏感字段，分享页不自动透出

---

### P1-7 验证链口径统一

严重度: P1
Owner: ops + engineer
状态: pending

问题:

- CI / dev-verify / codecov / gate 脚本口径不一致

目标:

- 建立唯一质量门禁口径

交付物:

- `docs/plans/P1-7-gate-unification.md`
- 修复文件：`.github/workflows/ci.yml`, `scripts/dev-verify.sh`, `scripts/check_coverage_gate.py`, `codecov.yml`

完成标准:

- CI、本地、codecov、脚本给出一致结论
- README 中有唯一执行入口

验证:

- 干净环境执行 CI 同款命令，与 dev-verify 结果一致

---

### P1-8 备份恢复演练不足

严重度: P1
Owner: ops
状态: pending

问题:

- 当前只能证明“文件可复制”，不能证明“恢复后系统可用”

目标:

- 从文件级备份升级到服务级恢复演练

交付物:

- `docs/plans/P1-8-backup-restore-drill.md`
- 脚本修订：`scripts/backup_verify.sh`
- 恢复演练记录文档

完成标准:

- 恢复出的 DB + 文件能重新支撑 portal / 订单 / 报告最小服务可用

验证:

- 临时目录恢复后跑最小服务 smoke test

---

## 5. P2 改进项（第二批处理）

### P2-1 公共下单孤儿订单

- 目标：支付初始化失败时不遗留无补偿订单

### P2-2 channel_sync 单一 DAO 真相

- 目标：移除旧 `dao_extension` 直连路径，统一到 OrdersDAO

### P2-3 delivery `sent` 语义过度乐观

- 目标：区分 `validated` / `queued` / `sent` / `delivered`

### P2-4 portal token 与后台 JWT secret 分离

- 目标：最小权限边界，独立轮换

### P2-5 payment webhook secret fail-closed

- 目标：生产环境禁止默认开发 secret 启动

### P2-6 历史快照头注补齐

- 目标：所有旧报告都显式声明“历史快照 + 当前真相源跳转”

---

## 6. 推荐执行顺序

第一批（必须先做）

1. P1-1 支付回调双写裂缝
2. P1-5 退款域模型未闭环
3. P1-2 删除/匿名化不完整
4. P1-7 验证链口径统一

第二批（安全与边界）5. P1-3 支付回调校验过弱 6. P1-4 webhook DB 连接污染 7. P1-6 分享 allowlist 8. P1-8 备份恢复演练

第三批（技术债）9. P2-1 ~ P2-6

---

## 7. 当前最准确的执行口径

> 当前项目已完成 v2.1 的后台运营与 AI 审核增强闭环，但要避免再次虚假完成，后续整改必须只围绕本清单中的真实未解决问题推进；其中最优先的是支付真相一致性、退款闭环、删除/匿名化闭环、以及验证链口径统一。
