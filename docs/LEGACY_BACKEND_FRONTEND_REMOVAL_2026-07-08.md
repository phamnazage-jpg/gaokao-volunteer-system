# LEGACY_BACKEND_FRONTEND_REMOVAL_2026-07-08

## Decision

The backend-rendered public HTML frontend was removed to prevent users/operators from opening stale pages such as `http://127.0.0.1:19260/` and mistaking them for the latest React/Vite conversational frontend.

## Current frontend truth

- Latest user-facing frontend: `apps/web` React/Vite app.
- Local dev frontend should run on a non-Gitea port such as `http://127.0.0.1:3001/` when local Gitea occupies `3000`.
- FastAPI remains the API backend.

## Removed backend-rendered GET routes

- `/` (line 270, approx 7 lines)
- `/pricing` (line 277, approx 5 lines)
- `/checkout/{service_version}` (line 282, approx 5 lines)
- `/portal/{token}/payment-success` (line 287, approx 9 lines)
- `/pay/mock/{payment_id}` (line 411, approx 9 lines)
- `/pay/alipay-sim/{payment_id}` (line 429, approx 11 lines)
- `/portal/payment-return` (line 449, approx 20 lines)
- `/review/start` (line 469, approx 30 lines)
- `/portal/{token}/cwb` (line 499, approx 24 lines)
- `/portal/{token}/full-plan` (line 523, approx 28 lines)
- `/portal/{token}/info` (line 551, approx 22 lines)
- `/portal/{token}/deletion-request` (line 813, approx 8 lines)
- `/portal/{token}/notifications` (line 838, approx 13 lines)
- `/portal/{token}/status` (line 1057, approx 9 lines)
- `/portal/{token}/report` (line 1066, approx 11 lines)
- `/portal/{token}/report.pdf` (line 1077, approx 19 lines)
- `/privacy` (line 1668, approx 23 lines)
- `/service-terms` (line 1691, approx 23 lines)
- `/policy-center` (line 1963, approx 26 lines)
- `/same-score-reference` (line 1989, approx 60 lines)
- `/deletion-policy` (line 2049, approx 13 lines)
- `/my-orders` (line 2062, approx 70 lines)
- `/my-reports` (line 2132, approx 69 lines)
- `/data-query` (line 2201, approx 41 lines)
- `/score-line-query` (line 2242, approx 57 lines)
- `/rank-estimator` (line 2299, approx 61 lines)
- `/majors-query` (line 2360, approx 59 lines)
- `/schools-query` (line 2419, approx 46 lines)
- `/compare-reports` (line 2465, approx 108 lines)

## Preserved backend surfaces

- `/health`
- `/api/*` admin/public APIs
- POST payment/webhook endpoints
- POST portal data/action APIs and helper functions used by JSON/API routes

## Verification

- `admin/tests/test_legacy_public_pages_removed.py` asserts old GET pages return 404 while health and public-order API remain registered.
- Focused API tests and `scripts/dev-verify.sh` must pass before commit.

## Legacy renderer helpers removed

- `_render_alipay_sim_payment_page`
- `_render_basic_page`
- `_render_checkout_page`
- `_render_cwb_placeholder_page`
- `_render_deletion_request_page`
- `_render_delivery_next_steps`
- `_render_footer_links`
- `_render_full_plan_placeholder_page`
- `_render_global_nav`
- `_render_global_toast_script`
- `_render_info_page`
- `_render_landing_page`
- `_render_legal_doc_page`
- `_render_mock_payment_page`
- `_render_notification_audit_page`
- `_render_payment_success_page`
- `_render_placeholder_shell`
- `_render_pricing_page`
- `_render_report_page`
- `_render_report_shell`
- `_render_review_start_page`
- `_render_share_link_script`
- `_render_share_status_panel`
- `_render_simulated_payment_html`
- `_render_simulated_payment_page`
- `_render_status_page`
