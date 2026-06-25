# Test Client Coverage Status

> 结论：主链路页面与协议已完成真实 `TestClient` 覆盖；前台关键测试文件中的 `RouteClient` 已清零。

关联文档：

- `reports/STRICT_SYSTEM_REVIEW_2026-06-23.md`：严格系统复审，已确认此前阻断级主链路问题已修复。
- `docs/CURRENT_STATE.md` §0.8：当前真相源中的正式口径。

## 已真实覆盖的主链路

- 首页公开入口：`/`
- 定价页 / 付费页：`/pricing`、`/checkout/*`
- 复核入口：`/review/start`
- 复核分流：`POST /review/action`（真实 form + 303 redirect）
- 冲稳保页面：`/portal/{token}/cwb`
- 完整规划页：`/portal/{token}/full-plan`
- 资料页：`/portal/{token}/info`
- 状态页：`/portal/{token}/status`
- 报告页：`/portal/{token}/report`、`/portal/{token}/report.pdf`
- 支付成功页：`/portal/{token}/payment-success`
- 公开建单：`POST /api/public/orders`
- 关键支付完成：`POST /pay/mock/{payment_id}/complete`

## 前台关键测试文件清零状态

- `admin/tests/test_web_public.py` → `route_client.` 计数 `0`
- `admin/tests/test_web_public_content_pages.py` → `0`
- `admin/tests/test_web_public_review_flow.py` → `0`
- `admin/tests/test_web_public_portal_info.py` → `0`
- `admin/tests/test_order_status_page.py` → `0`

## 当前 `RouteClient` 剩余定位

- 仍保留在仓库里，作为轻量辅助夹具存在
- 但前台关键测试文件已不再使用它
- 后续若继续看到 `RouteClient`，应默认把它视为非前台主链路测试或历史遗留点，而不是当前用户端主证据

## 现状判断

- 主链路可达性、重定向、表单协议、公开建单成功链路：已由真实 `client` 证明。
- 前台关键测试文件中的 `RouteClient` 已清零，主链路正确性不再依赖直接路由调用。
- 先前的 `starlette.testclient` → `httpx2` 弃用 warning 已通过补齐测试依赖清除。

## 最近验证

- `./.venv/bin/python -m pytest -q admin/tests/test_web_public.py admin/tests/test_web_public_review_flow.py admin/tests/test_web_public_portal_info.py` → `54 passed`
- `./.venv/bin/python -m pytest -q admin/tests/test_web_public_content_pages.py admin/tests/test_web_public.py` → `26 passed`
- `./.venv/bin/python -m pytest -q admin/tests/test_web_public.py -k 'encryption_key_missing or provider_unavailable or prod_hides_simulated_payment_entrypoints'` → `3 passed`
- `./.venv/bin/python -m pytest -q admin/tests/test_order_status_page.py admin/tests/test_web_public.py admin/tests/test_web_public_content_pages.py admin/tests/test_web_public_review_flow.py admin/tests/test_web_public_portal_info.py data/orders/tests/test_schema.py` → `89 passed`
- `./.venv/bin/python -m pytest -q admin/tests/test_order_status_page.py admin/tests/test_web_public.py admin/tests/test_web_public_content_pages.py admin/tests/test_web_public_review_flow.py admin/tests/test_web_public_portal_info.py admin/tests/test_order_deletion.py admin/tests/test_routes_cases.py admin/tests/test_routes_stats_dashboard.py admin/tests/test_admin_ui_pages.py admin/tests/test_order_info_form.py data/orders/tests/test_schema.py data/orders/tests/test_public_flow.py tests/test_backup_restore_service_level.py` → `149 passed`

