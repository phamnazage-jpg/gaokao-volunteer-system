# GAOKAO 本地浏览器 E2E 覆盖矩阵（2026-06-16）

> 范围：用户端 Web 自助 MVP 全部浏览器可达页面 + 后台审计/管理页。
> 环境：本地 FastAPI 8011 / 临时 SQLite / alipay_sim 支付 / dev 默认密钥。
> 验证方式：真实浏览器 + curl/Python 真实 HTTP。

## 0. 顶层结论

| 项目                                              | 状态                                                                |
| ------------------------------------------------- | ------------------------------------------------------------------- |
| 公开落地页 / 政策页 / 下单页                      | ✅ 浏览器 HTTP 200                                                  |
| 公开下单 → 模拟支付 → portal status               | ✅ 浏览器真实走通                                                   |
| portal 5-step 资料填写 → 提交 → status 推进       | ✅ 浏览器真实走通，摘要前后端一致                                   |
| portal report.html / report.pdf 下载              | ✅ 浏览器/HTTP 200，PDF 头正确                                      |
| portal 删除申请提交                               | ✅ HTTP 200，admin 审计页可看到                                     |
| admin 登录 + dashboard + 删除审计页 + 通知审计页 + 运维告警页 | ✅ 浏览器+HTTP 全部 200，命中真实数据                     |
| 后台 API 兼容别名 `/api/admin/{orders,cases,stats}`          | ✅ 已补齐兼容别名，旧路径与新路径并存                       |
| 真实支付宝（alipay）acceptance                    | ⛔ 阻塞：缺商户凭据 / 备案域名 / 公网 notify_url                    |

## 1. 覆盖矩阵

### 1.1 公共侧（无需登录）

| 路径                 | 真实浏览器 | HTTP | 备注                   |
| -------------------- | ---------- | ---- | ---------------------- |
| `/` (landing)        | ✅         | 200  | 历史报告 + 本次复核    |
| `/pricing`           | ✅         | 200  |                        |
| `/privacy`           | ✅         | 200  |                        |
| `/service-terms`     | ✅         | 200  |                        |
| `/deletion-policy`   | ✅         | 200  |                        |
| `/checkout/standard` | ✅         | 200  | 本次真实填单并完成支付 |
| `/checkout/audit`    | ✅         | 200  |                        |
| `/checkout/premium`  | ✅         | 200  |                        |

### 1.2 支付 + portal（无需登录，凭 portal token）

| 路径                                          | 真实浏览器 | HTTP         | 备注                                                |
| --------------------------------------------- | ---------- | ------------ | --------------------------------------------------- |
| `/pay/alipay-sim/{payment_id}`                | ✅         | 200          | 模拟收银台页打开                                    |
| `POST /pay/alipay-sim/{payment_id}/complete`  | ✅         | 303 → status | 模拟支付成功跳转                                    |
| `GET /portal/{token}/status`                  | ✅         | 200          | 状态推进 `paid` → `serving` → `delivered`           |
| `GET /portal/{token}/info`                    | ✅         | 200          | 5-step 表单 + 真实 Step 5 摘要                      |
| `POST /portal/{token}/info` (submit)          | ✅         | 200          | 返回 `intake_status=submitted, stage=processing`    |
| `GET /portal/{token}/report`                  | ✅         | 200          | HTML 报告内容与上传一致                             |
| `GET /portal/{token}/report.pdf`              | ✅         | 200          | `Content-Type: application/pdf`、头 `%PDF-1.4`      |
| `GET /portal/{token}/notifications`           | ⏸️         | n/a          | 本轮未直接点开；API 侧 admin/通知审计已显示对应通知 |
| `GET /portal/{token}/deletion-request` (页面) | ⏸️         | 200          | 本轮通过 API 提交并验证 admin 端可见                |
| `POST /portal/{token}/deletion-request`       | ✅         | 200          | 返回 `request_logged=true`                          |

### 1.3 后台 API

| 路径                                             | HTTP | 命中真实数据                                                   |
| ------------------------------------------------ | ---- | -------------------------------------------------------------- |
| `POST /api/auth/login`                           | 200  | 拿到 JWT，5 分钟过期                                           |
| `GET /api/auth/me`                               | 200  | `{id:1, role:admin, last_login_at:...}`                        |
| `GET /api/admin/notifications`                   | 200  | total=2，包含 `report_ready_email`、order_id=GKO-20260615-OVIG |
| `GET /api/admin/notifications/deletion-requests` | 200  | 1 条，含 `张家长/13800138000/浏览器 e2e`                       |
| `GET /api/admin/notifications/ops-alerts`        | 200  | 0 条（正常）                                                   |
| `GET /api/admin/users`                           | 200  | total≥1                                                        |
| `GET /api/admin/users/{user_key}`                | n/a  | 本轮未单点                                                     |
| `GET /api/admin/orders`                          | 200  | 已补兼容别名；与 `/api/orders` 返回同一数据契约               |
| `GET /api/admin/cases`                           | 200  | 已补兼容别名；与 `/api/cases` 返回同一数据契约                |
| `GET /api/admin/stats/dashboard`                 | 200  | 已补兼容别名；返回 `summary/by_status/...`                     |
| `GET /api/admin/stats/orders`                    | 200  | 已补兼容别名；返回 `total_orders/...`                          |
| `GET /health`                                    | 200  |                                                                |

### 1.4 后台页面（`page_router`）

| 路径                       | 真实浏览器 | HTTP | 命中真实数据                                                                |
| -------------------------- | ---------- | ---- | --------------------------------------------------------------------------- |
| `/admin/dashboard`         | ✅         | 200  | 已补后台兼容入口；内容与 `/dashboard` 一致                                      |
| `/admin/deletion-requests` | ✅         | 200  | `<h1>删除申请审计`、总数=1、订单、家长、联系方式、原因                      |
| `/admin/notifications`     | ✅         | 200  | `<h1>通知审计`、order_id、event_type=report_ready_email                     |
| `/admin/ops-alerts`        | ✅         | 200  | `<h1>运维告警审计`                                                          |

### 1.5 真实支付 acceptance（阻塞于外部凭据）

| 项                       | 状态    |
| ------------------------ | ------- |
| 真实 alipay 商户凭据     | ⛔ 缺失 |
| 公网可访问 notify_url    | ⛔ 缺失 |
| 备案域名                 | ⛔ 缺失 |
| 真实 alipay-sim 之外链路 | ⛔ 阻塞 |

## 2. 本轮新增的证据（相对 2026-06-15 报告）

1. **portal/report 与 report.pdf 真实下载**：
   - `curl /portal/.../report` → 200，body 首行 `<h1>志愿方案报告</h1><p>浏览器 e2e 自动验收</p>`
   - `curl /portal/.../report.pdf` → 200，body 前 9 字节 `%PDF-1.4\nlocal-brows`
2. **删除申请 -> admin 审计页整站闭环**：
   - `POST /portal/.../deletion-request` → `{order_id, request_logged:true, next_step}`
   - `/admin/deletion-requests?order_id=GKO-...` → 命中 `张家长 / 13800138000 / 浏览器 e2e`
3. **admin 通知审计页真实可见**：
   - `/admin/notifications` 页面 + `/api/admin/notifications` API 都能看到 `report_ready_email / order_id`
4. **JWT 5 分钟过期门禁生效**（符合 P2-4 安全要求）
5. **后台兼容别名已补齐**：
   - `/admin/dashboard` → 200，页面含 `仪表盘` 与 `/static/dashboard.js`
   - `/api/admin/orders` / `/api/admin/cases` / `/api/admin/stats/{dashboard,orders}` → 200

## 3. 与 2026-06-15 报告的关系

`reports/LOCAL_BROWSER_VALIDATION_2026-06-15.md` 中提到的：

- ✅ 公共页、checkout、alipay_sim、portal status、portal info、deletion-request 页 — 本轮复验全部仍可用
- ⚠️ Step 5 真实浏览器提交 — 本轮已通过 `submitIntake('submit')` 在浏览器中触发，状态从 `paid` 推进到 `serving`（之前是 paid 状态机就停在 paid），前端摘要字段与后端 status 摘要字段完全一致
- 🆕 本轮新增：报告 HTML/PDF 真实下载、admin 三类审计页真实可见、JWT 过期门禁、后台兼容别名与 dashboard 入口补齐

## 4. 当前未覆盖 / 阻塞项

| 项                                                    | 阻断类型 | 关闭路径                                                                              |
| ----------------------------------------------------- | -------- | ------------------------------------------------------------------------------------- |
| 真实 alipay acceptance                                | 外部凭据 | 见 `docs/PAYMENT_PROVIDER_ONBOARDING.md`                                              |
| 后台订单详情页浏览器验收                              | code     | 在 admin 路由列表里选主要页面跑一遍                                                   |
| 公开页 SEO / 移动端布局                               | 范围     | 与当前 E2E 主链路无关                                                                 |
