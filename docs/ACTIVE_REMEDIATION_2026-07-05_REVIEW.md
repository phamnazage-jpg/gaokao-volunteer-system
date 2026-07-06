# ACTIVE_REMEDIATION_2026-07-05_REVIEW

> 生成时间：2026-07-05T21:33:52+08:00  
> 来源：`reports/REVIEW_REPORT_2026-07-05_COMPREHENSIVE_PROJECT_REVIEW.md`  
> 配套方案：`docs/plans/2026-07-05-review-remediation-systemic-fix-plan.md`  
> 状态：Phase 0~4 全部已完成；Phase 5 视觉验收和文档回写进行中。
> 更新时间：2026-07-06T08:30:07+08:00

---

## P0 当前必须修复

| ID | 问题 | 影响 | 归属阶段 | 验收标准 |
|---|---|---|---|---|
| P0-01 | README / CURRENT_STATE / active board 真相源漂移 | 后续执行会按旧状态误判 | Phase 0 | 真相入口一致，旧报告标历史快照 |
| P0-02 | Admin mock 登录 + apiClient 无 Bearer + `?t=` JWT fallback | 后台真实鉴权不成立，token 泄漏 | Phase 1 | 真实登录、Bearer 注入、`?t=` 负向测试通过 |
| P0-03 | `/admin/review` 导航断链 | 后台用户路径断裂 | Phase 1 | 路由存在或导航移除，全 nav e2e 通过 |
| P0-04 | `payment-return` 裸 payment_id 换 Portal token | 支付回跳可被 token 兑换滥用 | Phase 2 | 无签名/nonce 的 payment_id 不能换 token |
| P0-05 | Python mypy 9 errors | 总门禁失败 | Phase 4 | `bash scripts/dev-verify.sh` 不再因 mypy 失败 |

## P1 高优先级

| ID | 问题 | 影响 | 归属阶段 | 验收标准 |
|---|---|---|---|---|
| P1-01 | 公共错误 detail 透传内部错误 | 信息泄漏 | Phase 2 | prod 下公共错误不含 env/path/provider detail |
| P1-02 | 公开下单缺限流/幂等/垃圾单治理 | 批量垃圾订单/写放大 | Phase 2 | 高频下单触发 429 或幂等，清理任务可用 |
| P1-03 | Portal token 不可撤销 / TTL 长 | 链接泄漏风险 | Phase 2 | 单 token 可撤销，敏感操作可二次校验 |
| P1-04 | 附件仅扩展名校验 | 恶意文件风险 | Phase 3 | magic bytes/MIME 负向测试通过 |
| P1-05 | Alipay notify 无 body limit | DoS 风险 | Phase 3 | 超限 413 测试通过 |
| P1-06 | 物理删除缺审计 | 审计断裂 | Phase 3 | 删除写 audit 且要求 actor/reason |
| P1-07 | SQLite schema 无版本迁移 | 生产升级不可控 | Phase 3 | schema_migrations + 旧库升级测试 |
| P1-08 | Poster Docker 构建失败 | 海报交付发布风险 | Phase 4 | 本地/CI Docker build 通过 |
| P1-09 | compose healthcheck 固定 8000 | 非默认端口假失败 | Phase 4 | 非默认端口 healthcheck 通过 |

## P2 治理与长期防复发

| ID | 问题 | 归属阶段 | 验收标准 |
|---|---|---|---|
| P2-01 | Chromatic token / Storybook / 视觉基线未闭环 | Phase 4/5 | secret 缺失语义明确，视觉 baseline 有 fresh evidence |
| P2-02 | LHCI 端口/启动口径漂移 | Phase 4/5 | preview start/ready/port 显式一致 |
| P2-03 | 100-case smoke non-blocking 语义过弱 | Phase 4/5 | release 必过子集明确 |
| P2-04 | Node/pnpm/turbo 本地环境前置条件未沉淀 | Phase 0/4 | README/runbook 有明确命令 |
| P2-05 | 旧截图/旧 review 容易误导 | Phase 0 | 历史快照标识和当前指针存在 |

---

## 禁止提前声称

在全部 P0/P1 current-scope 项未修复前，禁止声称：

- 项目生产级完成。
- Admin 真实鉴权闭环。
- 支付/Portal 安全闭环。
- CI/LHCI/Chromatic 完整验收闭环。
- 线上真实支付/域名/真实流量 acceptance 完成。
