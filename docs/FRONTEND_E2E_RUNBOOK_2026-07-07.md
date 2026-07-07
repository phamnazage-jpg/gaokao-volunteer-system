# FRONTEND_E2E_RUNBOOK_2026-07-07

## 目的

明确区分前端 mock E2E 与 real-backend E2E，避免把 Vite/MSW/mock 结果误报为真实前后端集成验收。

## Mock E2E

```bash
pnpm --filter @gaokao/web test:e2e:mock
```

- 默认模式。
- API 由 Playwright `page.route()` mock。
- 适合验证前端状态、可访问性、交互和错误恢复。
- 不得用它证明真实 FastAPI 后端联通。

## Real-backend E2E

```bash
# 1. 使用 env file，避免内联 secret 被脱敏为 ***
set -a; source /tmp/gaokao.env; set +a
python -m admin.app --port 8000

# 2. 另一个终端验证后端健康
curl -fsS http://127.0.0.1:8000/health

# 3. 运行真实后端 smoke
pnpm --filter @gaokao/web test:e2e:real-backend -- --project=chromium e2e/real-backend-smoke.spec.ts
```

验收口径：
- `/health` 必须可访问，且 `settings_valid=true`。
- real-backend smoke 通过只能证明最小真实后端联通，不等同于全业务线上 acceptance。

## 当前约束

- 真实支付、真实域名、真实用户流量 acceptance 不在本地 E2E 范围。
- 若 E2E 输出 `ECONNREFUSED 127.0.0.1:8000`，必须标记为 real-backend precondition missing，不能报告为 mock E2E PASS。
