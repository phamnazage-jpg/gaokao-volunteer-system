<!-- 历史快照提示：本文件保留为历史审计材料，不再代表当前项目状态。 -->
> ⚠️ **历史快照（非当前真相源）**：本文件仅保留当时审查/收口结论。当前状态与执行顺序以 `docs/CURRENT_STATE.md`、`docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`、`docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`、`docs/plans/2026-07-05-review-remediation-systemic-fix-plan.md` 和 `reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md` 为准。

---

# 高考项目严格系统 Review 报告（最新汇总版）

- 审查日期：2026-06-24
- 审查范围：`/home/long/project/gaokao-volunteer-system`
- 审查方式：源码静态审查 + 路由/权限边界核验 + 真实 `TestClient` 回归 + 最小行为复现
- 审查口径：按生产可用性、主链路正确性、数据完整性、测试可信度的最严格标准

## 执行摘要

当前仓库状态下，前台主链路、后台高风险安全边界、恢复演练口径、后台录单契约，以及此前多轮补充发现的问题，均已修复并重新验证。

本轮最终交叉核验确认：

1. 前台主链路可真实访问并走通：下单、支付、资料补充、复核分流、CWB、完整规划、报告、PDF 下载均可回归验证。
2. 前台关键测试文件中的 `RouteClient` 已清零；关键页面与关键 POST 协议现由真实 `TestClient` 证明。
3. 删除/匿名化服务已加 trusted-root 校验；不再信任 DB 中的任意文件路径执行 `unlink()`。
4. `viewer` 角色对 `cases` / `stats` 的权限边界已重新收口到 admin-only。
5. `backup_restore_smoke.py` 已升级为真实 `create_app()` + `TestClient` 服务级恢复验证，且 backup workflow 的 snapshot/secrets 契约已经与 smoke 对齐。
6. 后台录单页与 `/api/orders` 的 `consent` 契约已重新对齐；后台录单默认落 `draft` intake，避免伪装成 Portal `submitted`。
7. review 分流后的 `cwb` / `full-plan` 已去掉占位口径，公开入口对不支持省份的边界已显式收口，Portal 资料页已统一为“五步资料向导”。
8. 后台详情 API 现已显式暴露结构化 `intake` 载荷，报告页 CTA 已与 `review_followup_action=step1` 一致映射到 `/portal/{token}/info`。
9. 后台 UI 页面 `/dashboard`、`/admin/dashboard`、`/admin/orders/new` 已纳入 admin 鉴权边界；`payment_return_page` 仅在 payment.status=`paid` 时签发 portal token。
10. 公开上传附件响应已移除 `storage_path`，`stats` 的 `/tmp/debug_stats.txt` 遗留调试写盘已移除。

当前已观测 warning：无。

`starlette.testclient` → `httpx2` 的弃用 warning 已通过补齐测试依赖 `httpx2>=2.0.0` 消除。

## 当前状态结论

- 生产可用性：通过
- 主链路正确性：通过
- 数据完整性：通过
- 测试可信度：通过（前台主链已完成真实 `TestClient` 覆盖收口）
- 安全边界：通过

> 结论：按本报告采用的最严格审查口径，当前版本可视为通过本轮严格审查，可进入上线前最后准备阶段。

## 关键已修复项

### A. 前台主链路与真实协议

- 首页 `/` 已恢复真实注册。
- `/review/action` 已改为真实浏览器表单协议：`POST form -> 303 redirect`。
- `admin/tests/test_order_status_page.py` 中已补：
  - 首页真实注册校验
  - review form 正向提交
  - review form 缺字段/错误 literal/json body 错误路径
  - review → CWB / full-plan 真实跳转

### B. 前台关键测试文件 `RouteClient` 清零

以下文件中的 `route_client.` 调用已清零：
- `admin/tests/test_web_public.py`
- `admin/tests/test_web_public_content_pages.py`
- `admin/tests/test_web_public_review_flow.py`
- `admin/tests/test_web_public_portal_info.py`
- `admin/tests/test_order_status_page.py`

说明：`RouteClient` 仍保留在仓库作为轻量辅助夹具，但已不再承担前台主链路正确性的核心证据责任。

### C. 删除/匿名化越界删文件

- `data/orders/deletion_service.py`
  - portal 附件删除受限于 `settings.portal_upload_dir`
  - 交付物删除受限于 `_trusted_report_roots(settings)`
- 不可信路径现在会被跳过，不再执行 `unlink()`。
- 受信路径的正常删除行为保持绿色。

### D. viewer 权限边界漂移

- `admin/routes/cases.py`：admin-only
- `admin/routes/stats.py`：admin-only
- 与 `orders` 模块权限基线重新一致。

### E. backup / restore smoke 与 snapshot 契约

- `scripts/backup_restore_smoke.py` 会 fail fast 要求：
  - `config/.env`
  - `secrets/jwt_secret`
  - `secrets/orders_fernet_key`
  - `secrets/admin_pass`
- `scripts/backup_snapshot.sh` / `tests/test_backup_workflow.py` / `tests/test_backup_restore_service_level.py` 现已统一到同一 secrets 文件命名契约。
- 恢复 smoke 已升级为真实：
  - `create_app()`
  - `TestClient(app)`
  - `/health`
  - `POST /api/public/orders`
  - portal 状态页 / 报告页 / PDF 下载

### F. 后台录单页、详情口径与创建契约 / 提交语义

- `admin/routes/ui.py`
  - 页面新增 `consent_method` / `consent_note`
  - 页面脚本提交 `consent: { consent_method, consent_note }`
- `admin/routes/orders.py`
  - 后台录单默认创建 `draft` intake，不再伪装成 portal `submitted`
  - 订单详情接口现会返回结构化 `order.intake`
- `admin/tests/test_admin_ui_pages.py`
  - 已锁住“页面最小 payload 可通过 `CreateOrderRequest.model_validate(...)`”

### G. 第五轮与最终补充发现问题

1. review 分流后的 `cwb` / `full-plan` 占位口径：已修复
2. 不支持省份入口边界：已修复
3. 资料向导步数漂移：已修复
4. 后台 UI 未鉴权：已修复
5. `payment_id` 越权换取 portal token：已修复
6. 公开上传响应泄露 `storage_path`：已修复
7. `stats` 无条件写 `/tmp/debug_stats.txt`：已修复
8. 报告页 CTA 未覆盖 `step1` followup 映射：已修复

### 当前验证证据

### 1. 主链路与页面/协议组合

```bash
./.venv/bin/python -m pytest -q \
  admin/tests/test_order_status_page.py \
  admin/tests/test_web_public.py \
  admin/tests/test_web_public_content_pages.py \
  admin/tests/test_web_public_review_flow.py \
  admin/tests/test_web_public_portal_info.py \
  admin/tests/test_order_info_form.py \
  data/orders/tests/test_schema.py \
  data/orders/tests/test_public_flow.py
```

结果：通过

### 2. 删除边界 / 权限边界 / 后台 UI / 恢复 smoke / 订单权限 / 元数据一致性

```bash
./.venv/bin/python -m pytest -q \
  admin/tests/test_order_deletion.py \
  admin/tests/test_routes_cases.py \
  admin/tests/test_routes_stats_dashboard.py \
  admin/tests/test_admin_ui_pages.py \
  admin/tests/test_app.py \
  admin/tests/test_admin_alias_routes.py \
  admin/tests/test_order_info_upload.py \
  admin/tests/test_order_status_page.py \
  tests/test_backup_workflow.py \
  tests/test_backup_restore_service_level.py \
  admin/tests/test_routes_orders.py \
  admin/tests/test_routes.py
```

结果：通过

### 3. 当前严格审查汇总回归组合

```bash
./.venv/bin/python -m pytest -q \
  admin/tests/test_order_status_page.py \
  admin/tests/test_web_public.py \
  admin/tests/test_web_public_content_pages.py \
  admin/tests/test_web_public_review_flow.py \
  admin/tests/test_web_public_portal_info.py \
  admin/tests/test_order_deletion.py \
  admin/tests/test_routes_cases.py \
  admin/tests/test_routes_stats_dashboard.py \
  admin/tests/test_admin_ui_pages.py \
  admin/tests/test_app.py \
  admin/tests/test_admin_alias_routes.py \
  admin/tests/test_order_info_form.py \
  admin/tests/test_order_info_upload.py \
  admin/tests/test_routes_orders.py \
  admin/tests/test_routes.py \
  data/orders/tests/test_schema.py \
  data/orders/tests/test_public_flow.py \
  tests/test_backup_workflow.py \
  tests/test_backup_restore_service_level.py
```

结果：`177 passed in 31.44s`

## 风险余量与建议

### 当前非阻断项

- 当前无已观测非阻断 warning；此前的 `starlette.testclient` → `httpx2` 弃用提示已修复

### 上线前建议

1. 对外口径继续保持：
   - 公开省份支持集是当前支持集，不夸大为全国通用能力
   - crowd_db 全国高信任仍按真相源文档分批推进
2. 若要进一步提高发布信心，可加一次：
   - 真机/容器内 smoke
   - 恢复脚本在真实备份快照上的人工演练



## 关联文档

- `reports/STRICT_SYSTEM_REVIEW_2026-06-23.md`：历史滚动审查报告，已保留完整发现/修复轨迹
- `reports/TEST_CLIENT_COVERAGE_2026-06-23.md`：前台真实 `TestClient` 覆盖收口证据
- `docs/CURRENT_STATE.md`：当前真相源
