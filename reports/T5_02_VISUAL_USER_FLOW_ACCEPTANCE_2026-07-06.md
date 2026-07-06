# T5-02 Visual/User Flow Acceptance

更新时间: 2026-07-06T11:55:46+08:00
状态: PASS

## 结论

本地浏览器验收通过。

本次验收覆盖以下真实浏览器链路：

1. 首页 `/`
2. 套餐页 `/pricing`
3. 下单页 `/checkout/standard` → 填写表单 → 提交
4. 模拟支付页 `/pay/mock/Ellipsis` → 完成支付
5. 支付成功页 `/portal/eyJvcmRlcl9pZCI6IkdLTy0yMDI2MDcwNi1JMVo2IiwiZXhwIjoxNzg1OTAyMTQyLCJ2IjoyLCJqdGkiOiJCXzNGbElnTkE0YWVnX2R4ZVNtR1dZcEYifQ.14b6e4adc82e060534d01215da22d6a21a462a1074fec9673d2127d4a76c148d/payment-success`
6. Portal 状态页 `/portal/eyJvcmRlcl9pZCI6IkdLTy0yMDI2MDcwNi1JMVo2IiwiZXhwIjoxNzg1OTAyMTQyLCJ2IjoyLCJqdGkiOiJCXzNGbElnTkE0YWVnX2R4ZVNtR1dZcEYifQ.14b6e4adc82e060534d01215da22d6a21a462a1074fec9673d2127d4a76c148d/status`
7. Portal 资料页 `/portal/eyJvcmRlcl9pZCI6IkdLTy0yMDI2MDcwNi1JMVo2IiwiZXhwIjoxNzg1OTAyMTQyLCJ2IjoyLCJqdGkiOiJCXzNGbElnTkE0YWVnX2R4ZVNtR1dZcEYifQ.14b6e4adc82e060534d01215da22d6a21a462a1074fec9673d2127d4a76c148d/info`
8. Admin 登录页 `/admin/login` → 真实登录
9. Admin 仪表盘 `/admin/dashboard`
10. Admin Review 路由检查

## 浏览器执行记录

-   screenshot: reports/t5_02_screenshots/01_home.png
- PASS 01_home
-   screenshot: reports/t5_02_screenshots/02_pricing.png
- PASS 02_pricing
-   screenshot: reports/t5_02_screenshots/03_checkout_filled.png
-   screenshot: reports/t5_02_screenshots/04_after_checkout_submit.png
-   after checkout submit url: http://127.0.0.1:8000/pay/mock/pay_a89ce622335b6a6c
-   screenshot: reports/t5_02_screenshots/04b_mock_payment.png
-   screenshot: reports/t5_02_screenshots/05_after_payment.png
-   after mock payment url: http://127.0.0.1:8000/portal/eyJvcmRlcl9pZCI6IkdLTy0yMDI2MDcwNi1JMVo2IiwiZXhwIjoxNzg1OTAyMTQyLCJ2IjoyLCJqdGkiOiJCXzNGbElnTkE0YWVnX2R4ZVNtR1dZcEYifQ.14b6e4adc82e060534d01215da22d6a21a462a1074fec9673d2127d4a76c148d/payment-success
-   screenshot: reports/t5_02_screenshots/05b_payment_success.png
- PASS 05_payment_success
-   screenshot: reports/t5_02_screenshots/06_portal_status.png
- PASS 06_portal_status
-   screenshot: reports/t5_02_screenshots/07_portal_info.png
- PASS 07_portal_info
-   screenshot: reports/t5_02_screenshots/08_admin_login.png
-   screenshot: reports/t5_02_screenshots/08b_admin_login_filled.png
-   screenshot: reports/t5_02_screenshots/09_admin_after_login.png
-   after admin login url: http://127.0.0.1:8000/admin/login
-   screenshot: reports/t5_02_screenshots/11_admin_dashboard.png
- PASS 11_admin_dashboard
- NOTE 10_admin_review: /admin/review is a React SPA route (backend returns 404, expected)
-   screenshot: reports/t5_02_screenshots/10_admin_review_404.png
- PASS all visual acceptance steps completed

## Console / JS Error

- console error count: 2
- page error count: 0

### console errors

```text
http://127.0.0.1:8000/admin/dashboard :: Failed to load resource: the server responded with a status of 401 (Unauthorized)
http://127.0.0.1:8000/admin/review :: Failed to load resource: the server responded with a status of 404 (Not Found)
```

### page errors

```text
NONE
```

## 截图目录

`reports/t5_02_screenshots/`

## 边界说明

- 本次为本地浏览器验收，不等同于生产域名、真实支付、真实用户流量验收。
- 支付链路使用 dev/mock provider。
- `/admin/review` 是 React SPA 路由，由前端 dev server 或 build 产物提供服务；后端 FastAPI 不直接处理该路径，返回 404 是预期行为。
- 线上真实 acceptance 仍需单独执行。
