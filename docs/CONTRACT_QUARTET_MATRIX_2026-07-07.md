# CONTRACT_QUARTET_MATRIX_2026-07-07

| Contract | Runtime route | OpenAPI status | Frontend caller/schema | Test evidence | Notes |
|---|---|---|---|---|---|
| auth login | `POST /api/auth/login` | included | `LoginPage` / auth store / api-client bearer | `LoginPage.test.tsx`, `api-client.test.ts` | Admin auth entrypoint. |
| admin dashboard stats | `GET /api/admin/stats/dashboard` | included via admin stats router | `DashboardPage.tsx` + `DashboardStatsSchema` | `DashboardPage.test.tsx` | Requires bearer auth. |
| public order create | `POST /api/public/orders` | included | public backend-rendered checkout flow | `admin/tests/test_web_public.py` | Public paid-flow boundary. |
| alipay notify | `POST /api/public/payments/alipay/notify` | intentionally excluded | no browser caller | `admin/tests/test_payment_alipay_notify.py` | External provider webhook; `include_in_schema=False` by design. |
| portal CWB | `GET /portal/{token}/cwb` | included | `usePortal.ts` / generated schemas | `PortalPage.test.tsx`, web_public tests | Token protected portal surface. |
| portal full-plan | `GET /portal/{token}/full-plan` | included | `usePortal.ts` / generated schemas | `PortalPage.test.tsx`, web_public tests | Token protected portal surface. |
| LLM config | `GET /api/llm/config` | included | `useLLMEnhanceMutation.ts` | `LLMEnhancement.test.tsx` | Production depends on provider config. |
| LLM enhance | `POST /api/llm/{provider}/enhance` | included | `useLLMEnhanceMutation.ts` | `LLMEnhancement.test.tsx` | Provider-specific enhancement flow. |
