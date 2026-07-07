# 2026-07-07 项目全面系统性 Review 报告

> 审查对象：`/home/long/project/gaokao-volunteer-system`  
> 生成时间：2026-07-07T11:58:22  
> 审查方式：读取当前代码/文档/历史真相源 + 执行当前后端、前端、E2E、Docker 门禁 + 静态安全/占位扫描。  
> 重要边界：本报告是本地代码库与本地门禁 review，不等同于线上真实支付、真实域名、真实用户流量验收。

---

## 0. 结论

**结论：REQUEST_CHANGES / 当前不能宣称生产级完成。**

当前代码较 2026-07-05 报告已有明显推进：Python 单测与 ruff 基本面很好，Docker poster 构建可复现，前端 typecheck/lint/build 通过；但本轮 fresh gates 仍暴露出新的阻断项：

| 层级 | 当前结论 | 证据 |
|---|---|---|
| 后端/Python 回归 | **FAIL** | `scripts/dev-verify.sh`：1383 passed / 3 skipped，但最终 mypy 3 errors，exit=1 |
| 前端 type/lint/build | **PASS** | `pnpm typecheck` / `pnpm lint` / `pnpm build` 均成功 |
| 前端单元测试 | **FAIL** | `pnpm test`：328 passed / 1 failed，i18n hardcoded Chinese gate 失败 |
| Playwright E2E | **FAIL / 环境+真实用例混合失败** | chromium/mobile 有 poster/share 按钮 disabled 超时；webkit/firefox 浏览器缺失；52 passed / 68 failed |
| Docker poster | **PASS** | `docker build -f Dockerfile.poster -t gaokao-poster-cli:review-20260707 .` 成功 |
| 线上真实验收 | **待执行** | README/CURRENT_STATE 明确线上真实支付/域名/真实流量 acceptance 未完成 |

综合判断：**本地部分门禁通过，但整体本地质量门禁未闭环；生产 readiness 仍未达标。**

---

## 1. 当前项目真相源与范围判断

### 1.1 当前定位

README 当前说明项目是“面向人工服务运营的高考志愿填报系统”，管理后台、订单/分享/渠道同步、AI 审核链路已成形；用户端 Web 自助闭环仍在推进中。README 还明确：当前状态是本地代码与前端门禁已具备，线上真实支付/域名/真实流量 acceptance 仍未完成。

### 1.2 当前 active board 状态存在二次漂移

`docs/CURRENT_STATE.md` 与 `docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md` 都声称 Phase 0~5 已全部完成，且旧记录写有 dev-verify / frontend gate PASS。但本轮 fresh gates 证明当前 HEAD 已重新出现：

- 后端 `dev-verify` 因 mypy 失败，不能算 Phase 5 全量本地 gate 完成。
- 前端 `pnpm test` 因 i18n hardcoded Chinese gate 失败，不能算前端本地门禁全绿。
- Playwright 全项目 e2e 因浏览器环境缺失和真实用例失败，不能算 E2E gate 完成。

这说明：**文档当前状态句已经落后于当前工作区/当前 HEAD 的真实验证结果，需要重新同步。**

---

## 2. Gate 结果

### 2.1 Git / 工作区状态

```text
## main
?? data/share/short_links.db-shm
?? data/share/short_links.db-wal
43fc6b24950dfee525bb43e9e230cee49bd1d7cf
43fc6b2 fix(frontend): remove visible demo placeholders
25c33ea fix(frontend): complete backend integration contracts
4cbd2d7 test(frontend): align runtime accessibility smoke
f6e2402 chore(repo): remove stale frontend artifacts
223177f docs(ops): production readiness doctor + checklist update + env example
```

风险：当前工作区出现 `data/share/short_links.db-shm` / `data/share/short_links.db-wal` 未跟踪文件，属于测试/运行副产物。它们不应混入 review 报告或后续提交边界。

### 2.2 Python / 后端门禁

命令：

```bash
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

结果：**FAIL**。

关键输出摘要：

```text
1383 passed, 3 skipped, 3 warnings in 155.27s
Coverage XML written to file coverage.xml
Required test coverage of 80% reached. Total coverage: 90.18%
coverage gate summary: overall=83.53%, core=100.00%
ruff: All checks passed!
mypy: Found 3 errors in 1 file (checked 268 source files)
admin/tests/test_sprint3_api_contract.py:133: Unsupported operand types for <= ("int" and "object")
admin/tests/test_sprint3_api_contract.py:141: Argument 1 to "len" has incompatible type "object"; expected "Sized"
admin/tests/test_sprint3_api_contract.py:162: Argument 1 to "len" has incompatible type "object"; expected "Sized"
```

判断：这不是运行功能失败，而是测试辅助函数类型收窄不足导致 mypy gate 失败；但项目自己把 mypy 放在总门禁中，因此必须按 blocker 处理。

### 2.3 前端基础门禁

命令：

```bash
node --version
pnpm --version
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

结果：**部分通过 / 单测失败**。

- Node：`v22.22.0`
- pnpm：`10.33.0`
- `pnpm typecheck`：PASS，含 codegen contract gate：generated OpenAPI types/schemas are non-stub
- `pnpm lint`：PASS
- `pnpm build`：PASS，total gzip 394.72 KB，bundle budget PASS
- `pnpm test`：FAIL，`src/quality/i18nMessagesCoverage.test.ts` 发现 `pages/admin/DashboardPage.tsx` 仍有硬编码中文

失败摘要：

```text
FAIL src/quality/i18nMessagesCoverage.test.ts
expected [ 'pages/admin/DashboardPage.tsx' ] to deeply equal []
Test Files 1 failed | 84 passed
Tests 1 failed | 328 passed
```

### 2.4 Playwright E2E

命令：

```bash
pnpm --filter @gaokao/web test:e2e
```

结果：**FAIL**。

失败分两类：

1. **环境缺失类**：webkit/firefox 浏览器 executable 缺失，Playwright 提示需要 `pnpm exec playwright install`。
2. **真实用例失败类**：chromium/mobile-chrome 中 poster/share 场景按钮 disabled，导致点击 `生成海报` / `创建分享链接（30天有效）` 超时。

关键结论：不能把 E2E 失败全部归因于浏览器未安装。chromium/mobile 已启动的场景里也有真实交互状态失败。

### 2.5 Docker poster 构建

命令：

```bash
docker build -f Dockerfile.poster -t gaokao-poster-cli:review-20260707 .
```

结果：**PASS**。

```text
Successfully tagged localhost/gaokao-poster-cli:review-20260707
f965cabbd8480c264d74b07f980c0bd80be5db739fc497903cddbda181ae67a4
```

---

## 3. HIGH Findings

### H1 · 当前 active truth 文档与 fresh gate 结果不一致

**证据：** `docs/CURRENT_STATE.md` 顶部称“本地验证完成（Phase 0~5 全部通过）”，但本轮 fresh run 显示：

- `scripts/dev-verify.sh` exit=1（mypy 3 errors）
- `pnpm test` exit=1（i18n hardcoded Chinese gate 失败）
- `pnpm --filter @gaokao/web test:e2e` exit=1（68 failed）

**影响：** 后续执行会继续误判项目已经本地验证完成，属于文档真相漂移。  
**建议：** 更新 `docs/CURRENT_STATE.md`、active remediation、active execution board，把当前状态降级为“本地门禁回归中 / 线上 acceptance 待执行”。

### H2 · Python 总门禁被 mypy 阻断

**证据：** `admin/tests/test_sprint3_api_contract.py` 的 helper 使用 `dict[str, object]` 后直接做数值比较和 `len()`：

```text
## DashboardPage hardcoded Chinese lines apps/web/src/pages/admin/DashboardPage.tsx
44:     pending: '待处理',
45:     paid: '已支付',
46:     serving: '服务中',
47:     delivered: '已交付',
48:     completed: '已完成',
49:     refunded: '已退款',
## Sprint3 mypy object len/comparison anchors admin/tests/test_sprint3_api_contract.py
133:             assert item[numeric_key] >= 0
141:     assert body["total"] >= len(body["items"])
162:     assert body["total"] >= len(body["items"])
## Docker compose mock payment default docker-compose.yml
24:       GAOKAO_PAYMENT_PROVIDER: ${GAOKAO_PAYMENT_PROVIDER:-mock}
```

**影响：** CI 使用 `scripts/dev-verify.sh` 时会失败；当前不能宣称 Python gate complete。  
**建议：** 在断言前用局部变量 + `isinstance(..., int/list)` 做类型收窄，或引入 TypedDict / cast；修复后复跑 `python -m mypy .` 与 `bash scripts/dev-verify.sh`。

### H3 · 前端 i18n 迁移门禁失败，Dashboard 仍有硬编码中文

**证据：** `apps/web/src/pages/admin/DashboardPage.tsx` 中 `statusLabel()` 仍直接写中文状态：`待处理 / 已支付 / 服务中 / 已交付 / 已完成 / 已退款`；前端质量测试明确失败。

**影响：** 多语言质量基线破裂；Sprint 7 已迁移页面不再满足 i18n 合规标准。  
**建议：** 将状态 label 迁入 `messages`，用 `intl.formatMessage` 或状态枚举映射 message id；补测试锁住无硬编码中文。

### H4 · Playwright E2E 存在真实交互失败，不只是浏览器环境问题

**证据：** webkit/firefox 大量失败是浏览器 executable 缺失；但 chromium/mobile-chrome 中 poster/share 用例也失败，按钮保持 disabled：

- `生成海报` 按钮 disabled，点击等待超时。
- `创建分享链接（30天有效）` 按钮 disabled，点击等待超时。

**影响：** 关键分享/海报用户流在当前 e2e 环境下不可证明可用。  
**建议：** 先安装缺失 Playwright 浏览器，再单独重跑 chromium/mobile poster/share 用例；如果仍 disabled，检查表单必填状态、mock 数据预置、按钮 enable 条件与移动端 viewport 下的状态初始化。

### H5 · README 启动示例仍使用内联 secret 生成方式，存在本环境已知脱敏污染风险

**证据：** README 行 149 示例：

```bash
export GAOKAO_JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

在本类终端/agent 环境中，内联 secret 可能被替换为字面 `***`，导致服务启动但 `/health` 的 settings_valid 失败。  
**影响：** 新操作者按 README 启动可能得到降级运行态，后续验收误判。  
**建议：** README 改为写入 `/tmp/gaokao.env` 或 `.env.local` 后 `source`，并在启动后强制 `curl /health` 验证 `settings_valid=true`。

---

## 4. MEDIUM Findings

### M1 · E2E 环境前置条件未闭环

Playwright 提示 firefox/webkit executable 缺失，说明本地 e2e 前置环境仍未完全沉淀。建议在 `docs/FRONTEND_GATE_RUNBOOK_2026-07-05.md` 或 `package.json` 增加明确的 `pnpm exec playwright install --with-deps` 准备步骤，并把“浏览器缺失”与“用例真实失败”在报告中分开。

### M2 · Vite dev proxy 在 E2E 中大量 ECONNREFUSED

E2E 输出多次出现 `connect ECONNREFUSED 127.0.0.1:8000`。部分测试依赖 mock 可继续通过，但这表明“前端 e2e”没有稳定绑定真实后端或明确 mock server 边界。建议把真实后端 E2E 与 MSW/mock E2E 拆开命名，避免把 mock 环境误报为真实集成验收。

### M3 · `admin/routes/web_public.py` 单文件过大，维护风险高

当前 `admin/routes/web_public.py` 约 300 KB，路由清单显示同一文件包含 public home/pricing/checkout/payment/portal/report/privacy/data-query 等大量页面和业务逻辑。覆盖率也低于多数核心模块（78%）。

建议分阶段拆分：

- public pages renderer
- payment routes
- portal routes
- policy/content pages
- data query pages
- shared UI shell/CSS helper

### M4 · Python 警告仍有未清项

`dev-verify` 输出：

- `admin/routes/web_public.py:2665 DeprecationWarning: invalid escape sequence '\s'`
- `tests/test_smtp_sender.py` 使用 `asyncore/smtpd`，Python 3.12 将移除

建议至少处理 `invalid escape sequence`；SMTP stub 可迁移到 `aiosmtpd` 或在明确 Python target 下局部过滤并记录。

### M5 · docker-compose 默认 payment provider 仍是 mock

`docker-compose.yml` 存在 `GAOKAO_PAYMENT_PROVIDER: ${GAOKAO_PAYMENT_PROVIDER:-mock}`。这对本地可接受，但生产部署模板不能默认 mock。建议生产 compose/template 改为无默认值并 fail-fast，或明确拆分 `docker-compose.local.yml` 与 `docker-compose.prod.yml`。

---

## 5. LOW / Hygiene Findings

### L1 · 测试运行生成未跟踪 SQLite WAL/SHM 文件

当前 `git status` 显示：

```text
?? data/share/short_links.db-shm
?? data/share/short_links.db-wal
```

建议加入 `.gitignore` 或调整测试 DB 到 `/tmp`，避免提交污染。

### L2 · 旧 artifact / worktree 噪音仍较多

仓库中仍有 `.worktrees/`、`.turbo/cache/`、大量历史截图/报告。虽然部分可作为历史证据，但 review / lint / 搜索时容易污染当前判断。建议明确归档策略，并确保 gate 默认排除 `.worktrees` 与旧截图。

---

## 6. 安全审查摘要

| 项 | 结论 | 说明 |
|---|---|---|
| 明文密钥扫描 | 未发现真实生产密钥 | 命中均为测试 secret / fixture |
| Admin 鉴权 | 需复核但比 7/5 报告已有推进 | 当前报告需基于 fresh e2e 继续验证真实登录链路 |
| Payment/Portal | 代码层已修复迹象，但线上未验 | 真实支付、真实回调、真实域名仍待 acceptance |
| 公共错误 | 需抽样复验 | 7/5 问题已列入整改，但本轮未完整攻击面回放 |
| 上传/Webhook | 需抽样复验 | 相关测试可能已覆盖，但生产 body limit / magic bytes 应加入发布 gate |

---

## 7. 产品 / 前端 / UX 审查摘要

当前 React 前端基础 build 与 typecheck/lint 通过，说明工程基础较稳；但以下问题阻断“生产级前端完成”结论：

1. i18n gate 失败，Dashboard 仍有中文硬编码。
2. E2E 中 poster/share 按钮 disabled，关键分享链路不可证明可用。
3. E2E 大量依赖 mock 或 Vite proxy failover；真实后端联调边界不清。
4. 本轮没有重新执行真实浏览器视觉验收；因此不能沿用旧截图报告宣称当前视觉已达标。

建议将前端验收拆成三层：

- **基础工程门禁**：typecheck/lint/unit/build
- **真实交互门禁**：chromium + mobile-chrome 的关键流 e2e 必过
- **视觉/用户流门禁**：启动真实后端 + 浏览器访问核心路径 + 截图/vision 复验

---

## 8. 发布 readiness 判断

**当前不可上线。**

| 维度 | 状态 | 原因 |
|---|---|---|
| Code-complete | 条件通过 | 多数功能存在，但 mypy/i18n/e2e 回归失败 |
| Gate-complete | 未通过 | 后端 dev-verify、前端 test、Playwright e2e 均未全绿 |
| Ops-ready | 条件通过 | Docker poster PASS，但 README secret 启动方式、compose mock 默认、E2E 环境前置仍需修 |
| Real-environment-ready | 待执行 | 真实支付、域名、真实流量 acceptance 未做 |

---

## 9. 建议整改顺序

### P0 — 必须先修

1. 修复 `admin/tests/test_sprint3_api_contract.py` mypy 3 errors，复跑 `bash scripts/dev-verify.sh`。
2. 修复 `DashboardPage.tsx` i18n 硬编码中文，复跑 `pnpm test`。
3. 安装/固定 Playwright 浏览器环境，单独复跑 `pnpm --filter @gaokao/web test:e2e --project=chromium` 与 mobile 关键失败用例。
4. 修复 poster/share disabled 状态失败，确保关键分享链路 e2e 可点击、可完成。
5. 更新 `docs/CURRENT_STATE.md` / active board，把当前状态从“本地验证完成”降级为 fresh gate truth。

### P1 — 本周内修

1. README secret 启动示例改为 env file + `/health` settings_valid 验证。
2. 处理 `web_public.py` invalid escape warning。
3. 明确 compose local/prod payment provider 默认值边界。
4. 将 `data/share/*.db-shm` / `*.db-wal` 测试副产物纳入 ignore 或迁到 `/tmp`。
5. 将 E2E mock vs real-backend 的执行口径写入 runbook。

### P2 — 结构治理

1. 拆分 `admin/routes/web_public.py`。
2. 清理/归档旧截图与 `.worktrees` 噪音。
3. 对 public payment / portal / upload / delete / notify 做安全负向场景矩阵复验。

---

## 10. 完成状态分级

状态：**系统性 Review 文档已完成；项目本身为“本地门禁未闭环，线上真实验收待执行”。**

实现闭环: ✅
- 证据: 已读取项目代码、文档、active board、历史 review，并生成本报告：`/home/long/project/gaokao-volunteer-system/reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md`

证据闭环: ✅
- 证据: fresh gates 已执行：`dev-verify`、`pnpm typecheck/lint/test/build`、`pnpm test:e2e`、`docker build`

文档闭环: ✅
- 证据: 本 review 报告已落盘：`/home/long/project/gaokao-volunteer-system/reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md`

防复发闭环: ⚠️
- 证据: 已明确防复发动作，但尚未执行代码/文档整改；需在后续修复任务中关闭 mypy/i18n/e2e/docs truth drift。

剩余缺口:
- 项目未达到整体生产级完成。
- 真实线上支付/域名/真实流量 acceptance 未执行。
- 当前 fresh gates 存在 P0 阻断项。


---

## 11. 2026-07-07 二次严格 Review 补充发现（fresh evidence）

> 补充时间：2026-07-07T12:05:32  
> 补充原则：不沿用旧 PASS；重新读取当前代码、当前报告、当前工作区，并补跑真实 TestClient/OpenAPI、前端 targeted e2e、静态安全扫描、文档真相扫描。

### 11.1 二次复核新增 Gate 证据

| Gate | 结果 | 证据摘要 |
|---|---|---|
| 今日报告落盘检查 | PASS | `wc -l` 显示报告存在且有内容；报告包含 REQUEST_CHANGES / H1 / P0 修复顺序 |
| 当前工作区 | DIRTY | 仍有 `data/share/short_links.db-shm` / `data/share/short_links.db-wal` 未跟踪 |
| TestClient HTTP/OpenAPI 探针 | PARTIAL | `/health`、`/openapi.json`、公开页可访问；部分受保护/非法 token 路径按预期 401/404；OpenAPI path count 已生成 |
| targeted chromium e2e | FAIL | poster/share targeted e2e 仍失败；不是仅由 firefox/webkit 缺失导致 |
| 安全/危险 API 静态扫描 | REVIEW_NEEDED | 命中 CSV 导出、SQL execute、subprocess/shell 相关位置，需逐项白名单/修复 |
| 文档真相扫描 | FAIL | CURRENT_STATE/active board 仍存在 Phase 0~5 全部完成叙述，与 fresh gates 冲突 |

### 11.2 新增 HIGH Findings

#### H6 · 今日报告初版已发现 REQUEST_CHANGES，但 active truth 文档仍未同步降级

**证据：** 二次扫描 `docs/CURRENT_STATE.md` / active remediation / active execution board / README 中仍可检索到 “本地验证完成 / Phase 0~5 全部完成 / dev-verify PASS” 等语义；但本轮和上一轮 fresh gates 都证明当前并非全绿。

摘录：

```text
docs/CURRENT_STATE.md:6:状态词: `本地验证完成（Phase 0~5 全部通过）/ 线上真实 acceptance 仍待执行`
docs/CURRENT_STATE.md:11:- Review Remediation Phase 0~5 已全部完成并三远端同步：
docs/CURRENT_STATE.md:16:  - Phase 4 (T4-01~T4-04): mypy 0 errors、Poster Docker 可复现构建、compose healthcheck 端口一致、LHCI/Chromatic/smoke gate 语义
docs/CURRENT_STATE.md:19:  - dev-verify: 1373 passed, 3 skipped, 0 failed
docs/CURRENT_STATE.md:21:  - mypy: 0 errors in 268 source files
docs/CURRENT_STATE.md:34:- 仍不能宣称生产级完成；线上真实支付/域名/真实用户流量 acceptance 仍未执行。
docs/CURRENT_STATE.md:49:- 禁止声称线上真实支付/域名/真实用户流量 acceptance 已完成。
docs/CURRENT_STATE.md:72:- 验证: 6 个 retention 测试 + 205 个直接相关子集全过，ruff + mypy 通过
docs/CURRENT_STATE.md:87:- 验证: 25 个 admin orders + alias 测试全过；ruff + mypy 通过；端到端 smoke 通过
docs/CURRENT_STATE.md:99:- 验证: 4 个 health/config 测试全过；dev-verify 全量通过
docs/CURRENT_STATE.md:176:- 验证: dev-verify all checks passed（1175 passed）
docs/CURRENT_STATE.md:184:- 验证: dev-verify all checks passed
docs/CURRENT_STATE.md:207:- 验证: 1179 passed, dev-verify all checks passed
docs/CURRENT_STATE.md:270:- `dev-verify.sh` 与 GitHub CI 都执行同一组硬阈值检查
docs/CURRENT_STATE.md:313:5. 依赖清单未显式声明 Jinja2 / WeasyPrint / cairocffi / ruff / mypy
docs/CURRENT_STATE.md:330:- 生产通知链已有底层 validated/delivered 状态机、portal 通知审计页、后台独立通知审计页、运维告警审计页与 watchdog alert sink；已支持 SMTP/IM webhook sink 代码接入，但仍缺线上真实通道配置后的生产联调
docs/CURRENT_STATE.md:345:> - P1-7 验证链口径统一（CI / dev-verify / codecov / gate script 同一阈值）
docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md:6:> 状态：Phase 0~5 全部已完成。最后更新：2026-07-06T12:02:53+08:00
docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md:19:| P0-05 | Python mypy 9 errors | 总门禁失败 | Phase 4 | `bash scripts/dev-verify.sh` 不再因 mypy 失败 |
docs/ACTIVE_REMEDIATION_2026-07-05_REVIEW.md:55:- 线上真实支付/域名/真实流量 acceptance 完成。
docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md:5:> 状态：Phase 0~5 全部完成。最后更新：2026-07-06T12:02:53+08:00
docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md:146:### T4-01 修 mypy 9 errors
docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md:149:- 验证：`.venv/bin/python -m mypy .`
docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md:163:- 文件：`.github/workflows/web-ci.yml`, `apps/web/lighthouserc.cjs`, `scripts/dev-verify.sh`
docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md:173:bash scripts/dev-verify.sh
docs/ACTIVE_EXECUTION_BOARD_2026-07-05_REVIEW_REMEDIATION.md:176:pnpm test
README.md:20:> 当前状态：本地代码与前端门禁已具备；2026-07-05 Review 发现的 P0/P1 问题正在按 Phase 0~5 系统修复；线上真实支付/域名/真实流量 acceptance 仍未完成。
README.md:162:仓库已提供 `scripts/dev-verify.sh`，用于统一执行：
README.md:168:- 运行 `ruff` / `mypy`
README.md:172:bash scripts/dev-verify.sh
README.md:175:GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
README.md:187:pnpm test
README.md:191:注意：以上只代表前端本地基础门禁；Playwright e2e / LHCI / Chromatic / 真实浏览器视觉验收仍需按 Phase 1~5 单独闭环。
```

**影响：** 当前报告已经成为新的事实输入，但项目入口仍会误导后续执行者。  
**建议：** 立即把 `docs/CURRENT_STATE.md` 顶部状态改为：`本地门禁回归中 / REQUEST_CHANGES / 线上真实 acceptance 待执行`，并指向本报告。

#### H7 · targeted Chromium e2e 证实 poster/share 失败是业务交互状态问题，不是单纯浏览器缺失

**证据：** 二次复跑 targeted e2e：

```bash
pnpm --filter @gaokao/web exec playwright test e2e/poster-generate-download.spec.ts e2e/share-link-failure-fallback.spec.ts --project=chromium --reporter=line
```

结果 exit=1。输出摘要：

```text
Running 4 tests using 4 workers

[1/4] [chromium] › e2e/poster-generate-download.spec.ts:10:3 › Poster Generate + Download (V10 Sprint 4 · T-B-23.8) › poster page renders 3 templates + generates poster
[2/4] [chromium] › e2e/poster-generate-download.spec.ts:75:3 › Poster Generate + Download (V10 Sprint 4 · T-B-23.8) › poster async job shows progress before preview
[3/4] [chromium] › e2e/share-link-failure-fallback.spec.ts:7:3 › Share Link failure fallback (V10 Sprint 4 · T-B-41) › share dialog shows retryable fallback when create endpoint fails
[4/4] [chromium] › e2e/poster-generate-download.spec.ts:134:3 › Poster Generate + Download (V10 Sprint 4 · T-B-23.8) › poster shows no preview when generation fails (Zod 校验失败)
  1) [chromium] › e2e/poster-generate-download.spec.ts:10:3 › Poster Generate + Download (V10 Sprint 4 · T-B-23.8) › poster page renders 3 templates + generates poster 

    Test timeout of 30000ms exceeded.

    Error: locator.click: Test timeout of 30000ms exceeded.
    Call log:
      - waiting for getByRole('button', { name: /生成海报/ })
        - locator resolved to <button disabled type="button" class="mt-6 flex min-h-[48px] w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50">…</button>
      - attempting click action
        2 × waiting for element to be visible, enabled and stable
          - element is not enabled
        - retrying click action
        - waiting 20ms
        2 × waiting for element to be visible, enabled and stable
          - element is not enabled
        - retrying click action
          - waiting 100ms
        60 × waiting for element to be visible, enabled and stable
           - element is not enabled
         - retrying click action
           - waiting 500ms


      61 |
      62 |     // 生成
    > 63 |     await page.getByRole('button', { name: /生成海报/ }).click();
         |                                                      ^
      64 |
      65 |     // 海报预览（src 是 url() 校验过的合法 URL）
      66 |     const posterPreviewImage = page.getByRole('img', { name: /海报预览|Poster preview/ });
        at /home/long/project/gaokao-volunteer-system/apps/web/e2e/poster-generate-download.spec.ts:63:54

    attachment #1: screenshot (image/png) ──────────────────────────────────────────────────────────
    test-results/poster-generate-download-P-89494--templates-generates-poster-chromium/test-failed-1.png
    ────────────────────────────────────────────────────────────────────────────────────────────────

    attachment #2: video (video/webm) ──────────────────────────────────────────────────────────────
    test-results/poster-generate-download-P-89494--templates-generates-poster-chromium/video.webm
    ────────────────────────────────────────────────────────────────────────────────────────────────

    Error Context: test-results/poster-generate-download-P-89494--templates-generates-poster-chromium/error-context.md


  2) [chromium] › e2e/poster-generate-download.spec.ts:75:3 › Poster Generate + Download (V10 Sprint 4 · T-B-23.8) › poster async job shows progress before preview 

    Test timeout of 30000ms exceeded.

    Error: locator.click: Test timeout of 30000ms exceeded.
    Call log:
      - waiting for getByRole('button', { name: /生成海报/ })
        - locator resolved to <button disabled type="button" class="mt-6 flex min-h-[48px] w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50">…</button>
      - attempting click action
        2 × waiting for element to be visible, enabled and stable
          - element is not enabled
        - retrying click action
        - waiting 20ms
        2 × waiting for element to be visible, enabled and stable
          - element is not enabled
        - retrying click action
          - waiting 100ms
        60 × waiting for element to be visible, enabled and stable
           - element is not enabled
         - retrying click action
           - waiting 500ms


      124 |
      125 |     await page.goto('/poster');
    > 126 |     await page.getByRole('button', { name: /生成海报/ }).click();
          |                                                      ^
      127 |
      128 |     await expect(page.getByRole('progressbar', { name: /海报生成进度|Poster generation progress/ })).toHaveAttribute('aria-valuenow', '40');
      129 |     await expect(page.getByRole('img', { name: /海报预览|Poster preview/ })).toHaveAttribute('src', 'https://example.com/poster-async.png', {
        at /home/long/project/gaokao-volunteer-system/apps/web/e2e/poster-generate-download.spec.ts:126:54

    attachment #1: screenshot (image/png) ──────────────────────────────────────────────────────────
    test-results/poster-generate-download-P-96fd8-ows-progress-before-preview-chromium/test-failed-1.png
    ────────────────────────────────────────────────────────────────────────────────────────────────

    attachment #2: 
```

**影响：** 关键分享/海报链路不能被声明为前端 e2e 完成。此前把大规模 E2E FAIL 主要归因于 firefox/webkit 缺失是不完整的；Chromium 单项目也应先收敛。  
**建议：** 优先修 poster/share 表单 enable 条件、测试夹具预置数据、移动端视口下的必填字段可见性，再复跑 chromium targeted e2e。

#### H8 · README 启动命令仍与已知 secret 脱敏陷阱冲突，属于运维真相风险

**证据：** README 仍包含内联生成 secret 的启动方式；这类命令在当前执行环境中容易被脱敏为字面 `***`，造成服务看似启动但 `/health.settings_valid=false`。

**影响：** 新操作者按 README 启动会得到污染运行态，进而污染 browser/E2E/health 验收。  
**建议：** README 改为 `.env.local` 或 `/tmp/gaokao.env` 生成并 source；启动后强制检查 `/health` 返回 `settings_valid=true`。

#### H9 · CSV 导出边界需补 spreadsheet formula injection 审计

**证据：** 二次扫描发现 CSV/导出相关位置，当前 review 不能证明所有用户可控字段都经过 `= + - @` 前缀中和：

```text
## admin/routes/orders.py
13: import csv
300: def _csv_safe_value(value: Any) -> Any:
308:     return {field: _csv_safe_value(masked.get(field)) for field in _EXPORT_FIELDS}
516: def export_orders_csv(
527:     writer = csv.DictWriter(output, fieldnames=list(_EXPORT_FIELDS))
530:         writer.writerow(cast(Any, _export_row(order)))
532:     filename = "orders_export.csv"
535:         media_type="text/csv; charset=utf-8",
## admin/tests/test_routes_orders.py
13: import csv
554: def test_export_orders_csv_returns_masked_rows(client, auth_headers, settings):
570:     assert resp.headers["content-type"].startswith("text/csv")
573:     rows = list(csv.DictReader(StringIO(resp.text)))
581: def test_export_orders_csv_neutralizes_formula_injection_values(
596:     rows = list(csv.DictReader(StringIO(resp.text)))
## data/orders/cli.py
6: import csv
328:         writer = csv.writer(fh)
329:         writer.writerow(_EXPORT_HEADERS)
331:             writer.writerow([row[header] for header in _EXPORT_HEADERS])
335:         "format": "csv",
## data/orders/tests/test_cli.py
8: import csv
306: def test_export_command_writes_minimal_csv_report(tmp_db_path: Path) -> None:
323:     export_path = tmp_db_path.parent / "orders-report.csv"
337:     assert payload["format"] == "csv"
343:         rows = list(csv.DictReader(fh))
## locustfile.py
16:       --headless -u 10 -r 2 -t 1m --csv reports/perf/t11_1
## scripts/score_range_fullchain_100_e2e.py
5: import csv
31: BATCH_CSV = Path("/tmp/score_range_fullchain_100_batches.csv")
70: def write_batch_plan(plan: dict[str, Any], *, json_path: Path, csv_path: Path) -> None:
74:     with csv_path.open("w", newline="", encoding="utf-8") as fh:
75:         writer = csv.DictWriter(
92:             writer.writerow({
423:     parser.add_argument("--batch-csv", type=Path, default=BATCH_CSV)
433:     write_batch_plan(plan, json_path=args.batch_json, csv_path=args.batch_csv)
487:         "batch_plan_csv": _rel_or_abs(args.batch_csv),
## tests/test_t5_performance.py
3: import csv
144:         "--csv",
156:     stats_path = report_prefix.with_name(report_prefix.name + "_stats.csv")
158:         rows = list(csv.DictReader(handle))
```

**影响：** 如果订单姓名、备注、external_id、来源字段等进入 CSV 并由 Excel/WPS 打开，存在公式注入风险。  
**建议：** 在所有 CSV export 边界引入统一 `csv_safe()`，并新增 dangerous prefix 回归测试。

#### H10 · E2E 大量 Vite proxy ECONNREFUSED 暗示 mock E2E 与真实后端 E2E 边界未清晰分层

**证据：** 上一轮全量 E2E 出现多次 `connect ECONNREFUSED 127.0.0.1:8000`，但部分用例仍通过；二次配置读取显示当前 e2e 既有 mock 行为又有真实 API proxy 迹象。

**影响：** 容易把“前端 mock 环境可跑”误报成“前后端真实集成可跑”。  
**建议：** 拆分命令：`test:e2e:mock` 与 `test:e2e:real-backend`；真实后端模式必须先启动 FastAPI 并验证 `/health.settings_valid=true`。

### 11.3 新增 MEDIUM Findings

#### M6 · `admin/routes/web_public.py` 的 invalid escape warning 应升级为可修复质量问题

上一轮 dev-verify 在 pytest 阶段多次输出：`admin/routes/web_public.py:2665 DeprecationWarning: invalid escape sequence '\s'`。这通常来自 f-string/HTML/regex 混写，短期不阻断测试，但长期会在 Python 版本升级或 warning-as-error gate 中变成失败。

建议：定位该字符串，改为 raw string、双反斜杠或拆出 CSS/JS，避免 Python 字符串 escape 污染。

#### M7 · SQL/subprocess/dangerous API 扫描命中项需要白名单化审计

二次扫描命中如下位置：

```text
## admin/routes/web_public.py
1281:   el.innerHTML = '<div class="state-loading__spinner"></div><p class="state-loading__text">' + (msg || '加载中…') + '</p>';
2921:                 globalHint.innerHTML = allErrs.join('；');
## admin/static/dashboard.js
60:   node.innerHTML = `<div class="chart-empty"><span class="label">${label || "等待加载数据"}</span></div>`;
## admin/static/vendor/echarts.min.js
1: (()=>{function h(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}function m(arr){return arr.reduce((x,y)=>Math.max(x,Number(y)||0),0)||1}function line(el,o
## admin/tests/test_order_status_page.py
127:     proc = subprocess.run(
## admin/tests/test_web_public_portal_info.py
61:     assert "confirm-summary').innerHTML" not in body
## apps/web/src/components/shared/SafeMarkdown.test.tsx
14:     expect(container.innerHTML).not.toMatch(/<script/i);
25:     expect(container.innerHTML).not.toMatch(/onerror/i);
## data/channel_sync/tests/test_monitor.py
39: def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
40:     return subprocess.run(
## data/cli_compat_backup.py
27:     completed = subprocess.run(
## data/crowd_db/tests/test_trace_cli.py
18: def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
19:     return subprocess.run(
## data/notifications/email_service.py
266:             row[2] for row in conn.execute(f"PRAGMA index_info({index_name!r})").fetchall()
## data/orders/tests/test_cli.py
32: ) -> subprocess.CompletedProcess[str]:
36:     return subprocess.run(
## data/payments/dao.py
41:         row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
44:         conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
## scripts/deploy_ops_verify.py
60: def _start_admin() -> subprocess.Popen:
86:     proc = subprocess.Popen(
103:         stderr=subprocess.STDOUT,
117: def _stop_admin(proc: subprocess.Popen) -> None:
121:     except subprocess.TimeoutExpired:
## scripts/integration_test.py
74:     proc = subprocess.Popen(
91:         stderr=subprocess.STDOUT,
109:     except subprocess.TimeoutExpired:
## scripts/perf_benchmark.py
56: def _start_admin() -> subprocess.Popen:
82:     proc = subprocess.Popen(
99:         stderr=subprocess.STDOUT,
114: def _stop_admin(proc: subprocess.Popen) -> None:
118:     except subprocess.TimeoutExpired:
## scripts/score_range_fullchain_100_e2e.py
144: def _start_admin(port: int) -> subprocess.Popen[str]:
184:     proc = subprocess.Popen(
201:         stderr=subprocess.STDOUT,
220: def _stop_admin(proc: subprocess.Popen[str] | None) -> None:
226:     except subprocess.TimeoutExpired:
## scripts/sprint4_real_backend_regression.py
183: def _start_local_backend(port: int, tmp_dir: Path) -> tuple[subprocess.Popen[bytes], str, str]:
188:     proc = subprocess.Popen(
205:         stderr=subprocess.STDOUT,
216: def _stop_process(proc: subprocess.Popen[bytes]) -> None:
220:     except subprocess.TimeoutExpired:
254:     proc: subprocess.Popen[bytes] | None = None
## scripts/user_simulation.py
77:     proc = subprocess.Popen(
94:         stderr=subprocess.STDOUT,
237:         except subprocess.TimeoutExpired:
## skills/gaokao-audit/tests/test_audit_cli.py
89:     result = subprocess.run(
## skills/gaokao-audit/tests/test_validate_template.py
20:     result = subprocess.run(
## tests/test_audit_cli_major_validation_phase2.py
105:     result = subprocess.run(
153:     result = subprocess.run(
200:     result = subprocess.run(
## tests/test_audit_engine_contract.py
62:     proc = subprocess.run(
## tests/test_backup_restore_service_level.py
91:     proc = subprocess.run(
127:         proc = subprocess.run(
165:     proc = subprocess.run(
189:     proc = subprocess.run(
## tests/test_backup_workflow.py
40:         row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
109:     proc = subprocess.run(
221:         proc = subprocess.run(
251:     proc = subprocess.run(
277:     proc = subprocess.run(
## tests/test_cli_doctor_phase3.py
14: def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
15:     return subprocess.run(
## tests/test_delivery_dispatcher.py
264:     proc = subprocess.run(
291:     proc = subprocess.run(
321:     proc = subprocess.run(
## tests/test_dev_verify_entrypoint.py
22:     proc = subprocess.run(
37:     proc = subprocess.run(
52:     proc = subprocess.run(
75:     subprocess.run(
91:     proc = subprocess.run(
109:     subprocess.run(
141:     proc = subprocess.run(
163:     proc = subprocess.run(
179:     subprocess.run(
207:     proc = subprocess.run(
## tests/test_legacy_checker_truth_wrapper.py
37:     proc = subprocess.run(
62:     proc = subprocess.run(
85:     proc = subprocess.run(
104:     proc = subprocess.run(
## tests/test_majors_cli_phase2.py
75: def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
76:     return subprocess.run(
## tests/test_majors_school_cli_phase2.py
73: def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
74:
```

这不等于确认漏洞，但当前报告应把它列为“需白名单/逐项解释”的安全审计项。尤其关注：

- SQLite `execute(f"...")` 是否只拼接受控表名/列名；
- `subprocess` 是否有 `shell=True` 或用户输入拼接；
- 前端是否存在 `innerHTML` / markdown HTML 渲染边界。

#### M8 · OpenAPI 有生成产物，但需补合同完整度矩阵

二次 TestClient 探针显示 `/openapi.json` 可访问且 OpenAPI paths 存在。摘要：

```text
BusinessError code=E01202 status=401
HTTPException status=401 mapped to BusinessError
BusinessError code=E01202 status=401
BusinessError code=E01202 status=401
## PROBES
[
  {
    "method": "GET",
    "path": "/health",
    "status": 200,
    "body": "{\"status\":\"ok\",\"checks\":{\"db_writable\":true,\"disk_writable\":true,\"settings_valid\":true}}"
  },
  {
    "method": "GET",
    "path": "/openapi.json",
    "status": 200,
    "body": "{\"openapi\":\"3.1.0\",\"info\":{\"title\":\"高考志愿填报管理后台 API\",\"description\":\"管理后台 MVP API。\\n\\n**认证流程**: `POST /api/auth/login` → 获取 Bearer JWT →\\n请求头 `Authorization: Bearer *** 访问受保护路由。\\n\\n**详细字段**: 订单完整字段见 `data/orders/models.py:"
  },
  {
    "method": "GET",
    "path": "/",
    "status": 200,
    "body": "<!doctype html> <html lang=\"zh-CN\">   <head>     <meta charset=\"utf-8\" />     <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />     <title>高考志愿填报智能规划服务</title>     <link rel=\"stylesheet\" href=\"/stati"
  },
  {
    "method": "GET",
    "path": "/pricing",
    "status": 200,
    "body": "<!doctype html> <html lang=\"zh-CN\">   <head>     <meta charset=\"utf-8\" />     <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />     <title>服务套餐 - 高考志愿填报智能规划服务</title>     <link rel=\"stylesheet\" href="
  },
  {
    "method": "GET",
    "path": "/checkout/standard",
    "status": 200,
    "body": "<!doctype html> <html lang=\"zh-CN\">   <head>     <meta charset=\"utf-8\" />     <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />     <title>下单 - 99元 完整志愿方案</title>     <link rel=\"stylesheet\" href=\"/st"
  },
  {
    "method": "GET",
    "path": "/privacy",
    "status": 200,
    "body": "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' /><title>隐私政策</title><link rel='stylesheet' href='/static/portal-ui.css' /><style>body{f"
  },
  {
    "method": "GET",
    "path": "/service-terms",
    "status": 200,
    "body": "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' /><title>服务说明与使用条款</title><link rel='stylesheet' href='/static/portal-ui.css' /><style>b"
  },
  {
    "method": "GET",
    "path": "/admin/login",
    "status": 200,
    "body": "<!doctype html> <html lang=\"zh-CN\"> <head> <meta charset=\"utf-8\" /> <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /> <title>管理后台登录</title> <link rel=\"stylesheet\" href=\"/static/portal-ui.css\" /> <sty"
  },
  {
    "method": "GET",
    "path": "/admin/dashboard",
    "status": 401,
    "body": "{\"code\":\"E01202\",\"message\":\"登录凭证无效\",\"suggestion\":\"请重新登录。如反复出现,请清除浏览器 Cookie 后重试。\",\"severity\":\"warn\",\"retryable\":false,\"detail\":{\"reason\":\"missing bearer token\"}}"
  },
  {
    "method": "GET",
    "path": "/portal/not-a-real-token/status",
    "status": 401,
    "body": "{\"code\":\"E05099\",\"message\":\"服务暂时无法处理请求\",\"suggestion\":\"请稍后重试,或联系技术支持并提供错误码以便排查。\",\"severity\":\"error\",\"retryable\":true,\"detail\":{\"http_status\":401,\"reason\":\"invalid portal token format\"}}"
  },
  {
    "method": "GET",
    "path": "/api/meta",
    "status": 401,
    "body": "{\"code\":\"E01202\",\"message\":\"登录凭证无效\",\"suggestion\":\"请重新登录。如反复出现,请清除浏览器 Cookie 后重试。\",\"severity\":\"warn\",\"retryable\":false,\"detail\":{\"reason\":\"missing bearer token\"}}"
  },
  {
    "method": "GET",
    "path": "/api/admin/stats/dashboard",
    "status": 401,
    "body": "{\"code\":\"E01202\",\"message\":\"登录凭证无效\",\"suggestion\":\"请重新登录。如反复出现,请清除浏览器 Cookie 后重试。\",\"severity\":\"warn\",\"retryable\":false,\"detail\":{\"reason\":\"missing bearer token\"}}"
  }
]
## OPENAPI_STATUS 200
OPENAPI_PATH_COUNT 66
OPENAPI_HAS /api/auth/login True
OPENAPI_HAS /api/admin/stats/dashboard True
OPENAPI_HAS /api/public/orders True
OPENAPI_HAS /api/public/payments/alipay/notify False
OPENAPI_HAS /portal/{token}/cwb True
OPENAPI_HAS /portal/{token}/full-plan True
```

但当前 review 仍未逐项对照：后端路由 → OpenAPI → React api-generated types/schemas → 前端调用。建议后续补一张 contract quartet 矩阵，重点覆盖 admin stats、public orders、payment notify、portal CWB/full-plan、LLM enhance。

#### M9 · domain data quality 需要与 LLM prompt 承诺继续做覆盖率验收

二次数据探针摘要：

```text
## data/crowd_db/special_programs.json
keys ['program_schools', 'programs']
programs 16
program_schools 16
## data/rules/special_programs_rules.json
keys ['last_verified', 'rules', 'version']
rules 44
quality_summary_import OK
```

当前报告只能确认相关数据文件/loader 可见，不能证明 prompt 中承诺的所有特殊项目、院校、分数带、规则都足量、可追溯、不过期。建议把“prompt 提到的路径 ↔ 数据 program_type ↔ rules ↔ loader 查询结果”做成发布前 gate。

### 11.4 更新后的 P0/P1 顺序

在原 P0 基础上，二次 review 后建议调整为：

1. **P0-1：修 mypy 3 errors**，使 `scripts/dev-verify.sh` 回到 0 exit。
2. **P0-2：修 Dashboard i18n hardcoded Chinese**，使 `pnpm test` 回到全绿。
3. **P0-3：修 poster/share targeted Chromium E2E**，不要等全浏览器安装后才处理真实交互失败。
4. **P0-4：同步 CURRENT_STATE / active board 到 fresh REQUEST_CHANGES truth**，避免后续继续按“Phase 0~5 已完成”推进。
5. **P0-5：拆分 mock E2E 与 real-backend E2E 命令**，并补真实后端启动/health 前置。
6. **P1-1：CSV formula injection 白名单/修复**。
7. **P1-2：处理 `web_public.py` invalid escape warning**。
8. **P1-3：README secret 启动方式改为 env file 模式**。
9. **P1-4：清理/ignore SQLite WAL/SHM 测试副产物**。
10. **P1-5：补 OpenAPI/backend/frontend contract quartet 矩阵**。

### 11.5 二次 Review 收敛结论

**目标**: 对 `/home/long/project/gaokao-volunteer-system` 再做一轮严格、全面、真实的系统性 review，并补充今天报告。  
**验证轮数**: 2/3。

**收敛状态**:

- [x] 已收敛：项目当前结论仍为 REQUEST_CHANGES，不可上线。
- [x] 已收敛：新增问题已补充到今天 review 报告。
- [ ] 未收敛项：尚未执行整改；真实线上 acceptance 仍待执行。

**最终证据**:

- fresh gates 显示后端 mypy、前端 unit、Playwright e2e 均未闭环。
- targeted chromium e2e 进一步证明 poster/share 是真实交互失败，不只是浏览器缺失。
- TestClient/OpenAPI 探针证明基础服务可导入并响应，但合同矩阵仍需补齐。
- 当前 active truth 文档仍需按 fresh report 降级同步。
