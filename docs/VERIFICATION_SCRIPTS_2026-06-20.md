# 6/20 v2.1.4: 性能 + 集成 + 用户模拟 + 部署运维 4 维度验证脚本

## 4 个新脚本

| 脚本                         | 覆盖                                                                    | 关键结果                                                    |
| ---------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------- |
| scripts/perf_benchmark.py    | 性能 (baseline 200 + 10 并发 50 任务)                                   | p95=3.01ms 单请求, p95=10.68ms / 1250 rps 并发, 100% 成功率 |
| scripts/integration_test.py  | 集成 (health + login + create + get + ops-alerts + retention dry/apply) | 7/7 PASS                                                    |
| scripts/user_simulation.py   | 用户模拟 (Playwright 5 跳 × 2 视口 = 10 张截图)                         | 10/10 PASS                                                  |
| scripts/deploy_ops_verify.py | 部署运维 (12 项 health/auth/CRUD/ops-alerts/dashboard)                  | 12/12 PASS                                                  |

## 关键发现 (A-2 投产时必读)

**`GAOKAO_ORDERS_FERNET_KEY` 必须在 systemd unit Environment= 显式设置**, 否则
订单写入会抛 `MissingEncryptionKey` 异常. 这是 6/20 集成测试时踩到的真坑
(initially 报 500 E03003, 调试发现是 FERNET_KEY 缺失 → 兜底 except 把真因
吞掉 → 表面看像"数据保存失败").

**响应结构**: admin `/api/orders` 与 `/api/orders/{id}` 都是嵌套
`{"order": {...}}` 包装, portal 路径直接是平铺. 自动化时注意.

**portal_token 路径**: `issue_portal_token(order_id, settings.portal_token_secret)`
在 data/customer_portal/token.py, 不是 admin `/api/orders/{id}` 响应里的字段.

## reports 输出

- reports/perf_2026_06_20.json
- reports/integration_2026_06_20.json
- reports/deploy_ops_2026_06_20.json
- reports/user_simulation_2026_06_20/captures.json + 10 张 PNG
- reports/PRODUCTION_LAUNCH_READINESS_2026-06-20.md (总报告)

## 不依赖

- locust (已知 venv 漂移)
- systemd (开发机可能没装)
- 真实外部凭据 (mock provider + 隔离 DB)

## 待跟进 (不属本轮)

- 真实微信/支付宝支付密钥
- 异机备份恢复演练
- 真实 SMTP/IMAP 邮件告警联调
- 钉钉/企微告警机器人接入
- 2027 高考前 crowd_db data_year 更新 + 高考生源大省数据补录
