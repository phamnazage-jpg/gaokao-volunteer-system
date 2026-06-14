# gaokao-volunteer-system 系统性评审报告（历史快照）

> 该文档保留 2026-06-13 当时的评审分析，但不应直接作为当前执行门禁。当前真相源请优先阅读：`docs/CURRENT_STATE.md` → `docs/ACTIVE_EXECUTION_BOARD_2026-06-13.md` → `docs/ACTIVE_REMEDIATION_2026-06-13.md`。

**评审日期**: 2026-06-13  
**评审对象**: `/home/long/project/gaokao-volunteer-system`  
**评审方法**: 文档交叉核对 + 关键代码抽样 + 工程门禁实跑 + 两阶段 review（规格对齐 / 代码质量）

---

## 1. 一句话结论

> 项目已经从“纯规划/纯 skill 仓库”演进为“运营后台 + 订单/分享/渠道同步 + AI 审核链路”的可运行系统，但**文档真相严重漂移、用户端 Web 自助闭环仍未落地、CI/类型/安全门禁未形成可信闭环**。当前更准确的项目标签是：**内部运营与人工服务增强系统已成形，面向用户的完整产品化交付仍未完成**。

---

## 2. 本次新鲜证据

### 2.1 工程门禁

```bash
git status --short
python3 -m pytest -q
python3 -m ruff check . --exclude .worktrees
python3 -m mypy .
python3 -m bandit -r admin data skills scripts -x .worktrees,tests,admin/tests,data/channel_sync/tests,data/orders/tests,data/share/tests,data/crowd_db/tests,skills/gaokao-audit/tests,scripts/legacy
pytest --cov=admin --cov=data --cov=skills --cov=scripts --cov-report=term-missing -q
pytest -q admin/tests
```

### 2.2 当前结果

- `git status --short`：**大量未提交修改/新增文件**，当前真实状态主要存在于 working tree，而不是稳定交付基线
- `python3 -m pytest -q`：**459 passed, 2 warnings**
- `python3 -m ruff check . --exclude .worktrees`：**All checks passed**
- `python3 -m mypy .`：**97 errors / 19 files**
- `python3 -m bandit ...`：原始输出噪声很高；聚焦后仍有若干真实问题
- `pytest --cov=admin --cov=data --cov=skills --cov=scripts --cov-report=term-missing -q`：**TOTAL 61%**
- `pytest -q admin/tests`：**115 passed**

### 2.3 CI 干净环境复核事实

- `.github/workflows/ci.yml` 只安装 `requirements-dev.txt`
- `requirements-dev.txt` **不包含** `fastapi / uvicorn / PyJWT / cryptography / pydantic`
- 因此 CI 对 `admin/*` 的 clean env 可复现性并不成立
- 这意味着“本地 pytest 通过”≠“CI 对完整产品可复现”

---

## 3. 当前真相源排序

当前建议按以下顺序理解项目状态：

1. **代码与实跑结果**（最高优先级）
   - `admin/`
   - `data/orders/`
   - `data/share/`
   - `data/channel_sync/`
   - `skills/gaokao-audit/`
   - 当前 pytest / ruff / mypy / bandit / coverage 输出
2. **README + CHANGELOG（部分可信）**
3. **IMPLEMENTATION_PLAN_v2 / CHANNEL_INTEGRATION（部分过时，需结合代码）**
4. **PRODUCT_TECH_REVIEW_2026-06-12 / AUDIT_REPORT_2026-06-11 / REMEDIATION_TASK_BOARD_2026-06-11（历史快照，不能直接继承为当前结论）**

---

## 4. Stage 1：规格/规划对齐审查

### 4.1 已对齐的主线

| 领域                                                  | 当前状态     | 证据                                                                          |
| ----------------------------------------------------- | ------------ | ----------------------------------------------------------------------------- |
| 场景A：闲鱼/微信/学校 → 管理端录单 → 顾问交付         | **基本对齐** | `docs/BUSINESS_SCENE.md` + `admin/routes/orders.py` + `data/channel_sync/*`   |
| 管理后台（认证/用户/订单/案例/仪表盘）                | **已落地**   | `admin/app.py`、`admin/routes/*`、`README.md`                                 |
| AI 审核主链（解析/规则检查/扎堆/报告/CLI）            | **已落地**   | `skills/gaokao-audit/scripts/*.py`                                            |
| 分享能力（短链/权限/公开分享）                        | **已落地**   | `data/share/short_link.py`、`data/share/permission.py`、`admin/share_page.py` |
| 渠道同步（闲鱼 webhook/poller、微信/企微最小 client） | **已落地**   | `data/channel_sync/*`                                                         |
| crowd_db 溯源与风险展示                               | **已落地**   | `data/crowd_db/*`、`scripts/gaokao-data-trace`                                |

### 4.2 关键漂移

#### A. 最严重范围错位：用户端 Web 自助产品未形成闭环

文档定义的场景B是：

- 用户访问 Web
- 站内先付费
- 付费后填写资料
- 自动/人工生成方案
- 站内查看 + 邮件 PDF 交付

当前代码现实：

- 仓库中**没有** `package.json`、`*.tsx`、用户端前台 Web 应用
- 只有：
  - 管理后台 FastAPI
  - 公开分享页
  - 管理端仪表盘页面 `admin/static/dashboard.html`
- **未见用户注册/下单/支付/资料填写/邮件交付闭环**

结论：

- 当前系统更像“运营后台 + 人工服务增强链路”
- 不是“文档中描述的双流程完整产品”

#### B. PRD / ROADMAP / README / IMPLEMENTATION_PLAN_v2 状态互相冲突

- `PRD.md` 仍把 F016-F020（分享/管理后台/反扎堆/数据溯源/AI审核）标成“规划中”
- `ROADMAP.md` 仍把多项已实现能力放在后续阶段
- `IMPLEMENTATION_PLAN_v2.md` 顶层总览大量任务仍是 `📋`，但局部又写“已实现”
- `README.md` 写入了较新能力，但目录树和整体叙事仍偏旧

结论：

- 当前没有单一文档可以单独代表真实现状
- **文档真相层已经失效**

#### C. 旧报告已过时

| 文档                                        | 当前判断                           |
| ------------------------------------------- | ---------------------------------- |
| `docs/AUDIT_REPORT_2026-06-11.md`           | **严重过时**                       |
| `docs/REMEDIATION_TASK_BOARD_2026-06-11.md` | **严重过时**                       |
| `reports/PRODUCT_TECH_REVIEW_2026-06-12.md` | **部分仍有效，但若直接继承会失真** |

仍有效的旧判断：

- Web 自助闭环缺失
- 文档状态漂移
- 覆盖率/CI 硬门槛未闭环

已失真的旧判断：

- “AI 审核编排层未形成”
- “pytest 环境不可运行”
- “测试规模极低”

---

## 5. Stage 2：代码质量 / 工程门禁审查

### 5.1 总体判断

| 维度      | 状态 | 结论                            |
| --------- | ---- | ------------------------------- |
| pytest    | ✅   | 功能回归层当前可通过            |
| ruff      | ✅   | 代码风格/显性低级错误当前可通过 |
| mypy      | ❌   | 类型门禁不可用                  |
| bandit    | ⚠️   | 噪声很大，但存在真实问题        |
| coverage  | ⚠️   | 总覆盖率仅 61%，结构性短板明显  |
| CI 完整性 | ❌   | 不是可信质量门禁                |

### 5.2 真实高风险问题

#### H1. Webhook 来源 IP 信任边界错误

- `data/channel_sync/webhook_server.py` 定义了 `_trust_x_forwarded_for()`
- 但 `_client_ip()` 实际**始终优先信任** `X-Forwarded-For`
- 结果：
  - 限流可被伪造头绕过
  - 审计 `remote_addr` 可被污染

这是**真实安全问题**，不是 bandit 噪声。

#### H2. 默认管理员弱口令 + 登录无节流

- `admin/config.py` 默认：`GAOKAO_ADMIN_USER=admin`, `GAOKAO_ADMIN_PASS=admin123`
- 空库会 bootstrap 管理员
- 登录接口未见失败次数限制 / 限流 / 锁定

虽然 prod 对 JWT secret 有强校验，但**admin 密码强度没有同级保护**。

#### H3. CI 无法代表完整产品可构建/可测试

- `.github/workflows/ci.yml` 只装 `requirements-dev.txt`
- 未安装 admin 运行依赖
- clean env 下 `admin/tests` 不可保证可运行

### 5.3 中风险问题

#### M1. 类型系统失控

`mypy .` 失败 97 个错误，集中在：

- `data/share/short_link.py`
- `data/cases/dao.py`
- `skills/gaokao-audit/*`
- `scripts/*`
- tests/legacy 噪声

含义不是“仓库不能跑”，而是：

- 类型门禁当前没有工程可信度
- 也无法直接接入 CI 做阻断

#### M2. 覆盖率不达计划标准

新鲜证据：

- TOTAL: **61%**
- admin 核心模块覆盖率明显偏低：
  - `admin/routes/orders.py` 57%
  - `admin/routes/ui.py` 55%
  - `admin/users.py` 38%
  - `admin/share_page.py` 14%
  - `admin/errors/exceptions.py` 33%
  - `admin/logging_utils.py` 23%
- skills 审核链路也有薄弱点：
  - `checker_integration.py` 63%
  - `report_generator.py` 67%

说明：

- `channel_sync`、`orders`、`crowd_db` 测试成熟度较高
- `admin`、`report_generator`、集成胶水层明显偏弱

#### M3. CSV 导出公式注入风险

`admin/routes/orders.py` 直接导出用户可控文本字段到 CSV，未做 Excel 公式注入防护。

#### M4. 异常吞噬导致审计可观测性下降

`data/channel_sync/webhook_server.py` 多处 `except Exception: pass`，虽然提高了兜底可用性，但也会削弱取证与排障能力。

### 5.4 低风险与噪声

#### L1. Bandit B608 大量动态 SQL 报警，多数是 false positive

例如：

- `data/orders/dao.py`
- `data/cases/dao.py`
- `data/share/short_link.py`
- `admin/stats.py`

这些位置多数是：

- 拼接**白名单列名/固定 where 片段**
- 值仍通过参数绑定传入

需要人工甄别，**不能直接按 SQL 注入漏洞上报**。

#### L2. 开发占位 JWT secret 是 intentional false positive

- `admin/config.py` 的 `_DEV_JWT_SECRET` 在 prod 启动时会被阻止
- 它本身不是生产漏洞，但会污染 bandit 输出

---

## 6. 模块真实状态表

| 模块                   | 真实状态                             | 说明                                                      |
| ---------------------- | ------------------------------------ | --------------------------------------------------------- |
| `admin/`               | **Partial / 可运行但质量门禁不闭环** | 后台功能已明显成形；CI 依赖、类型、覆盖率仍薄弱           |
| `data/orders/`         | **Done-ish / 质量较好**              | DAO、状态机、加密、CLI、测试都比较成熟                    |
| `data/channel_sync/`   | **Done-ish / 质量较好**              | webhook/poller/adapter/monitor 已成形，存在 XFF 安全缺口  |
| `data/share/`          | **Partial / 能用但有安全与类型债**   | 功能全，但密码哈希策略偏弱，类型门禁差                    |
| `data/cases/`          | **Partial**                          | CRUD 有了，但类型安全与工程化不足                         |
| `data/crowd_db/`       | **Done-ish / 数据能力较强**          | loader/trace/risk/report 成熟，但骨架省份仍有低置信度数据 |
| `skills/gaokao-audit/` | **Partial to Good**                  | 主链已落地，集成胶水层覆盖率与类型质量不足                |
| 用户端 Web 产品        | **Not started / Missing main chain** | 只有管理端与分享页，没有用户端自助闭环                    |

---

## 7. 当前最准确的项目标签

### 不准确标签

- “完整产品”
- “双流程（人工 + Web 自助）已完成”
- “工程门禁完善、可稳定交付”

### 更准确标签

> **高考志愿填报运营与审核增强系统（已具备后台、订单、分享、渠道同步、AI审核主链），但用户端 Web 自助产品与工程化质量门禁仍未闭环。**

---

## 8. 当前 Gate 结论

### 代码层 Gate

- `pytest`: ✅
- `ruff`: ✅
- `mypy`: ❌
- `bandit`: ⚠️（有噪声，但存在真实中高风险）
- `coverage`: ⚠️（总量与关键模块均未达理想值）

### 产品/范围 Gate

- 场景A（人工服务）: ✅ 基本闭环
- 场景B（用户端 Web 自助）: ❌ 未闭环
- 文档真相: ❌ 漂移严重

### 综合 Gate

**结论: REQUEST_CHANGES / 条件通过，不可宣称整体完成。**

---

## 9. 最短整改路径

1. **先修真相层**
   - 统一 README / PRD / ROADMAP / IMPLEMENTATION_PLAN_v2 状态口径
   - 旧报告降级为历史快照
2. **再补工程门禁**
   - 修 CI 依赖装配
   - 设定 mypy 可执行范围与配置
   - 在 CI 中加入 ruff / mypy / bandit / coverage fail-under
3. **再修真实安全问题**
   - X-Forwarded-For 信任边界
   - 默认 admin 口令与登录节流
   - CSV 公式注入
4. **最后再决定产品方向**
   - 要么收缩对外口径，承认当前是运营系统
   - 要么继续把用户端 Web 自助闭环真正落地

---

## 10. 本报告与旧报告的关系

- 本报告是 **2026-06-13 的新鲜实跑结论**
- `docs/AUDIT_REPORT_2026-06-11.md`、`docs/REMEDIATION_TASK_BOARD_2026-06-11.md`、`reports/PRODUCT_TECH_REVIEW_2026-06-12.md` 仅保留历史参考价值
- 之后若继续推进，应以本报告与新的整改任务板作为当前真相源
