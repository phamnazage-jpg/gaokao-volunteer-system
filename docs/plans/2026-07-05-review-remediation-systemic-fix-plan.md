# 2026-07-05 Review 系统性修复方案

> 生成时间：2026-07-05T21:33:52+08:00  
> 输入报告：`reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md`  
> 目标：先定义“完全修复”的系统方案和验收门槛，再拆成可执行任务清单。  
> 当前结论：本方案完成后，项目才能从 `REQUEST_CHANGES` 进入“本地质量门禁完成”；线上真实支付/域名/真实流量仍需独立 acceptance。

---

## 0. 完全修复定义

Review 报告中的问题不能逐条打补丁后就宣称完成，必须同时满足以下 6 个闭环：

1. **文档真相闭环**：README、CURRENT_STATE、今日 Review、active remediation、execution board 形成单一入口；旧报告标为历史快照。
2. **Admin 鉴权闭环**：React Admin 真实调用 `/api/auth/login`，apiClient 自动注入 Bearer，`?t=` 管理 JWT fallback 被移除或收紧为一次性 code，不再依赖 localStorage 伪登录。
3. **支付/Portal 安全闭环**：`payment-return` 不再凭裸 `payment_id` 换 Portal token；公共错误脱敏；公共下单有频控/幂等/垃圾单治理；Portal token 可撤销或缩短风险窗口。
4. **数据与文件安全闭环**：附件上传做 magic bytes/MIME 校验；Alipay notify 有 body size guard；物理删除有独立审计。
5. **工程门禁闭环**：mypy 9 errors 清零；SQLite schema 迁移有版本表；Poster Docker 可复现构建；compose healthcheck 与端口一致。
6. **前端/CI 验收闭环**：Admin 全导航 e2e、真实登录 e2e、Playwright、LHCI、Chromatic/视觉基线、100-case smoke gate 语义全部明确并有 fresh evidence。

---

## 1. 修复总架构

### 1.1 Truth Stack

新增/维护三层真相链：

- `docs/CURRENT_STATE.md`：只保留当前真实状态与入口优先级，不再混入旧 HEAD/旧工作区状态。
- `docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`：只列 Review 中仍有效的问题，按 P0/P1/P2 分级。
- `docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`：逐项可执行任务、文件路径、验证命令、依赖、完成标准。

旧报告处理：

- `reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md` 是本轮输入真相。
- 6/19、6/20、6/24 旧 review / closeout 只作历史参考，顶部加“历史快照”指针。

### 1.2 Auth Architecture

目标结构：

- 后端 `POST /api/auth/login` 签发 JWT。
- 前端 `AdminLoginPage` 调真实登录 API。
- 新增/调整 `authStore`：保存 access token、用户、过期时间；logout 清理。
- `apiClient` 通过 token provider 统一注入 `Authorization: Bearer <token>`。
- `RequireAuth` 不再只相信 `localStorage.role`，首次进入后台时调用 `/api/auth/me` 或校验 token expiry。
- 移除 `admin/auth.py:get_current_user()` 的 `?t=` fallback；如页面跳转必须带凭证，另建短期一次性 `admin_login_code` 交换机制。

验收：

- 未登录访问 `/admin` → `/admin/login`。
- 错误密码/过期 token → 401/403 友好错误。
- 登录成功后所有 admin API 带 Bearer。
- `GET /api/auth/me?t=<jwt>` 不再通过。
- e2e 不再直接写 `gaokao-user-store` 伪造 admin。

### 1.3 Payment / Portal Security Architecture

目标结构：

- `payment-return` 使用 `return_nonce` 或支付平台同步签名校验，不再接受裸 `payment_id` 直接换 token。
- `PaymentService.create_checkout()` 生成并持久化 `return_nonce`，绑定 payment/order/过期时间/一次性消费状态。
- Portal token 增加 `jti` / version，并在订单或 token 表中支持单 token 撤销。
- 公共错误响应只返回业务错误码与用户友好文案；内部错误只进日志。
- `/api/public/orders` 加 IP + phone hash + User-Agent 频控、幂等键、未支付垃圾单清理策略。

验收：

- 已支付 payment_id 无签名/无 nonce 不能换 Portal token。
- 错误响应不包含 env var、path、provider 内部 detail。
- 高频下单触发 429 或幂等返回。
- 单个 Portal token 可撤销，撤销后访问 401/403。

### 1.4 File / Webhook / Deletion Safety

目标结构：

- 附件上传：扩展名 + MIME + magic bytes 三重校验。
- 文本附件：UTF-8 解码和大小限制。
- Alipay notify：Content-Length 超限直接 413，body 读取前 guard。
- 订单物理删除：写 `order_deletion_audits` 或独立 deletion audit JSONL；任何物理删除必须包含 actor/reason。

### 1.5 Schema / Docker / CI Architecture

目标结构：

- `schema_migrations` 表记录版本、名称、applied_at、checksum。
- orders/payments/notifications 的 ad-hoc ALTER 逐步迁到版本化迁移函数。
- `Dockerfile.poster` 清理代理环境并固定可用 Debian package；CI 和本地都能构建。
- `docker-compose.yml` healthcheck 使用容器内真实监听端口或变量一致端口。
- `scripts/dev-verify.sh` 将业务主链路 smoke 状态单独输出；release 子集失败时不得只 warning。

### 1.6 Frontend / Visual / E2E Gates

目标结构：

- Admin nav e2e 自动遍历 `adminNavItems`，确保所有链接不是 NotFound。
- 真实登录 e2e：通过后端 API 获取 token，而非 localStorage seed。
- Playwright 全矩阵 fresh evidence：chromium/webkit/firefox/mobile-chrome。
- LHCI 显式 preview start command/port/ready pattern。
- Chromatic token 缺失时明确跳过或非阻塞；若为 release gate，必须要求 secret 存在。
- 真实浏览器/视觉验收对关键用户页与后台页做 browser_vision 或等价截图基线。

---

## 2. 非目标

- 不在本轮方案中申请或接入真实支付商户密钥。
- 不把线上真实 acceptance 伪装成本地完成。
- 不重写整个前端，只修 Review 指向的闭环缺口。
- 不把所有历史文档删除；只降级为历史快照并加当前真相指针。
- 不扩大到高考数据质量新一轮完善，除非它阻塞本 Review 问题。

---

## 3. 分阶段修复策略

### Phase 0：真相源收敛（必须先做）

目的：先消除执行入口漂移，避免后续按旧 board 修错目标。

交付：

- 更新 `docs/CURRENT_STATE.md`。
- 新建/更新 `docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md`。
- 新建/更新 `docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md`。
- README 顶部真相源指向改到 2026-07-05 这套文档。
- 旧 closeout/review 顶部加历史快照提示。

退出标准：

- `grep -n "dbb8fb7\|当前工作区未提交修改" docs/CURRENT_STATE.md` 无过时结果。
- README 当前真相源指向 2026-07-05 active docs。
- Review 报告、remediation、execution board 三者互相指向。

### Phase 1：Admin 真实鉴权与导航闭环

目的：解决用户可见后台断链和伪登录根问题。

交付：

- 后端移除或收紧 `?t=` JWT fallback。
- 前端真实登录、token store、apiClient Bearer 注入。
- `RequireAuth` 调 `/api/auth/me` 或校验 token 过期。
- 补 `/admin/review` 路由或移除导航。
- e2e 覆盖真实登录、token 过期、全 admin nav。

退出标准：

- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` 通过。
- `pnpm --filter @gaokao/web test:e2e` 至少 chromium/mobile-chrome 通过。
- 后端 auth tests 通过，`?t=` 负向测试通过。

### Phase 2：支付 / Portal / 公共接口安全闭环

目的：封堵裸 payment_id 换 token、错误泄漏、公开下单刷单、Portal token 不可撤销。

交付：

- `return_nonce` / 签名校验机制。
- Portal token `jti`/version/revocation。
- 公共错误响应脱敏。
- `/api/public/orders` 限流 + 幂等 + 垃圾单清理。
- 对应安全回归测试。

退出标准：

- 已支付 payment_id 无 nonce/signature 无法换 token。
- 公共错误响应不含内部路径/env/provider detail。
- 高频下单测试触发频控或幂等。
- 撤销 Portal token 后访问失败。

### Phase 3：上传 / webhook / 删除审计 / schema migration

目的：补齐数据安全和持久化演进基础设施。

交付：

- 附件 magic bytes/MIME 校验。
- Alipay notify body limit。
- 删除审计强制 actor/reason。
- `schema_migrations` 与旧库升级测试。

退出标准：

- 伪装扩展名上传被拒绝。
- 超大 notify body 返回 413。
- 物理删除写 deletion audit。
- 旧 schema DB 升级到最新 schema 测试通过。

### Phase 4：类型门禁 / Docker / Compose / CI gate

目的：让本地和 CI 质量门禁可复现。

交付：

- 修 mypy 9 errors。
- `types-qrcode` 或 mypy 精准配置。
- `Dockerfile.poster` 可复现构建。
- compose healthcheck 端口一致。
- dev-verify 输出主链路 smoke 状态。
- LHCI/Chromatic 配置收敛。

退出标准：

- `bash scripts/dev-verify.sh` 通过。
- `docker build -f Dockerfile.poster ...` 通过。
- compose healthcheck 在非默认端口也正确。
- LHCI/Chromatic 语义在 CI 中不再漂移。

### Phase 5：最终回归与上线前证据包

目的：证明“本地生产级门禁完成”，并明确线上 acceptance 仍需真实环境。

交付：

- 全量 pytest/ruff/mypy。
- 前端 typecheck/lint/test/build/e2e。
- 关键页面浏览器视觉验收。
- 100-case smoke 必过子集。
- 更新 Review 报告状态与 CURRENT_STATE。

退出标准：

- 本地质量门禁：PASS。
- 前端本地 + e2e +视觉：PASS。
- Docker/compose：PASS。
- 文档真相：PASS。
- 线上真实支付/域名/真实流量：明确仍为“待线上 acceptance”，不混淆。

---

## 4. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| Admin auth 改动影响现有 e2e | 测试大面积改写 | 先建 auth adapter，再逐步替换 e2e seed |
| 移除 `?t=` 影响后台 Web 跳转 | 旧链接失效 | 短期保留一次性 code 交换，不保留 JWT URL |
| Portal token 可撤销需要存储 | schema 增加复杂度 | 与 schema_migrations 同阶段落地 |
| 限流在 TestClient 中难测 | 测试不稳定 | 使用可注入 clock / in-memory limiter 测试实现 |
| Docker 构建受网络影响 | 本地复现不稳定 | 清理代理环境 + CI runner 复验 + 可配置 apt mirror |
| LHCI/Chromatic 外部服务不稳定 | CI 假失败 | 区分 hard gate 与 advisory gate；secret 缺失时显式 skip |

---

## 5. 最终完成判定

只有以下全部满足，才能把 Review Remediation 标为“本地验证完成”：

```bash
bash scripts/dev-verify.sh
pnpm typecheck
pnpm lint
pnpm test
pnpm build
pnpm --filter @gaokao/web test:e2e
pytest targeted security regression tests
ruff check .
mypy .
docker build -f Dockerfile.poster -t gaokao-poster-cli:review .
```

并且：

- README/CURRENT_STATE/ACTIVE_REMEDIATION/ACTIVE_EXECUTION_BOARD 指向一致。
- Review 报告中所有 P0/P1 当前范围问题状态已更新。
- 线上真实支付、真实域名、真实流量仍单独标注为“待线上 acceptance”。
