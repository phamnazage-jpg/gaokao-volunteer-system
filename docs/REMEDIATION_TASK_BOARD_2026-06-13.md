# 系统性评审整改任务板

**日期**: 2026-06-13  
**对应报告**: `reports/PROJECT_SYSTEM_REVIEW_2026-06-13.md`  
**当前 Gate**: 🔴 **REQUEST_CHANGES**  
**适用范围**: `gaokao-volunteer-system` 当前 working tree 与后续交付基线

---

## 0. 当前门禁结论

| 维度               |       状态 | 说明                                                                           |
| ------------------ | ---------: | ------------------------------------------------------------------------------ |
| pytest 回归        |    🟢 PASS | `460 passed, 2 warnings`                                                       |
| ruff 静态检查      |    🟢 PASS | `ruff check . --exclude .worktrees` 通过                                       |
| mypy 类型检查      |    🟢 PASS | `python3 -m mypy .` 通过（122 source files；仅保留 annotation-unchecked note） |
| 安全门禁           | 🟡 PARTIAL | XFF 信任边界与 admin 默认弱口令/登录节流已修；仍待更广安全项                   |
| 覆盖率门禁         |    🔴 FAIL | 总覆盖率约 61%，关键模块低于目标                                               |
| CI 可信度          |    🟢 PASS | clean env 已可安装 admin 依赖并跑通 `admin/tests/test_app.py`                  |
| 文档真相           |    🟢 PASS | README/PRD/ROADMAP/IMPLEMENTATION_PLAN_v2/旧报告已校准                         |
| 场景A 人工服务闭环 |    🟢 PASS | 后台 + 订单 + 分享 + 渠道同步已成形                                            |
| 场景B Web 自助闭环 |    🔴 FAIL | 用户端下单/支付/填资料/交付主链缺失                                            |

---

## 1. P0 — 必须先修（阻断项）

### P0-1 文档真相统一

**当前状态**: ✅ 已完成（2026-06-13）

**目标**

- 建立新的当前真相源，停止旧报告继续误导后续实施。

**文件**

- `README.md`
- `product/PRD.md`
- `product/ROADMAP.md`
- `docs/IMPLEMENTATION_PLAN_v2.md`
- `docs/AUDIT_REPORT_2026-06-11.md`
- `docs/REMEDIATION_TASK_BOARD_2026-06-11.md`
- `reports/PRODUCT_TECH_REVIEW_2026-06-12.md`

**完成标准**

- 明确三态：`已完成 / 进行中 / 规划中`
- 明确当前项目标签：运营后台 + 审核增强链路 / 非完整 Web 自助产品
- 旧报告顶部加“历史快照”提示，并指向 2026-06-13 新报告

**验证**

```bash
rg -n "历史快照|规划中|已完成|进行中|Web系统场景|完整产品" README.md product docs reports
```

---

### P0-2 修复 webhook 来源 IP 信任边界

**当前状态**: ✅ 已完成（2026-06-13）

**目标**

- `X-Forwarded-For` 只能在显式信任代理时生效；默认回退到 socket client_address。

**文件**

- `data/channel_sync/webhook_server.py`
- `data/channel_sync/tests/test_xianyu_channel.py`
- `docs/CHANNEL_INTEGRATION.md`

**完成标准**

- `_client_ip()` 使用 `_trust_x_forwarded_for()` 决策
- 默认不信任 XFF
- 测试覆盖：
  - 默认 XFF 不生效
  - 显式开启时 XFF 生效
  - socket fallback 仍可用

**验证**

```bash
python3 -m pytest -q data/channel_sync/tests/test_xianyu_channel.py
python3 -m ruff check data/channel_sync
```

---

### P0-3 管理后台弱口令与登录节流加固

**当前状态**: ✅ 已完成（2026-06-13，mypy 全仓问题仍属 P1）

**目标**

- 避免默认管理员弱口令成为可利用入口，并为登录增加基本抗爆破能力。

**文件**

- `admin/config.py`
- `admin/db.py`
- `admin/routes/auth.py`
- `admin/tests/test_auth.py`
- `README.md`

**完成标准**

- 生产环境下禁止默认 `admin123`
- 最低密码复杂度或长度门槛明确
- 登录失败次数节流 / 冷却机制落地
- README 明确首次启动后的密码轮换要求

**验证**

```bash
pytest -q admin/tests/test_auth.py
python3 -m mypy admin/config.py admin/routes/auth.py admin/db.py
```

---

### P0-4 修复 CI clean env 依赖不闭环

**当前状态**: ✅ 已完成（2026-06-13）

**目标**

- CI 在干净环境下可真实跑完整后端测试，不再依赖本地已有 admin 运行依赖。

**文件**

- `.github/workflows/ci.yml`
- `requirements-dev.txt`
- `requirements-admin.txt`
- 如需：新增 `requirements-ci.txt`

**完成标准**

- CI 安装 admin 运行依赖
- admin/tests 在 clean env 可导入执行
- CI 不再只是假设 data/skills/scripts 可测

**验证**

```bash
python3 -m venv /tmp/gvs-ci-check
/tmp/gvs-ci-check/bin/pip install -r requirements-dev.txt -r requirements-admin.txt
/tmp/gvs-ci-check/bin/pytest -q admin/tests/test_app.py
```

---

## 2. P1 — 应尽快修（高优先级质量项）

### P1-1 让 mypy 成为可执行门禁

**当前状态**: ✅ 已完成（2026-06-13：全仓 `python3 -m mypy .` 已通过；核心修复覆盖 `skills/gaokao-audit/*`、`scripts/*`、`tests/test_all.py`）

**目标**

- 先收敛类型检查范围，再逐步修复核心生产代码错误。

**文件**

- 新增：`mypy.ini` 或 `pyproject.toml`
- `data/share/short_link.py`
- `data/cases/dao.py`
- `skills/gaokao-audit/scripts/*.py`
- 必要时分阶段限制 tests/legacy 范围

**完成标准**

- mypy 可稳定执行
- 至少 `admin/`、`data/orders/`、`data/channel_sync/`、`data/share/` 核心运行时路径通过
- tests / legacy 噪声与生产代码分开治理

**验证**

```bash
python3 -m mypy admin data/orders data/channel_sync data/share
```

---

### P1-2 覆盖率门禁落地

**目标**

- 从“产出 coverage.xml”升级为“coverage fail-under + 关键模块达标”。

**文件**

- `.github/workflows/ci.yml`
- `codecov.yml`（如需要）
- 相关测试文件

**完成标准**

- CI 采集 `admin` 覆盖率
- 至少建立 `--cov-fail-under` 或分模块门槛
- 优先提升低覆盖模块：
  - `admin/routes/orders.py`
  - `admin/routes/ui.py`
  - `admin/users.py`
  - `admin/share_page.py`
  - `skills/gaokao-audit/scripts/report_generator.py`
  - `skills/gaokao-audit/scripts/checker_integration.py`

**验证**

```bash
pytest --cov=admin --cov=data --cov=skills --cov=scripts --cov-report=term-missing -q
```

---

### P1-3 CSV 公式注入防护

**当前状态**: ✅ 已完成（2026-06-13：CSV 导出对 `= + - @` 前缀做 neutralize，并补回归测试）

**目标**

- 导出 CSV 前对危险前缀做 neutralize（如 `= + - @`）。

**文件**

- `admin/routes/orders.py`
- `admin/tests/test_routes_orders.py`

**完成标准**

- 导出列中所有用户可控文本经过安全处理
- 测试覆盖公式注入前缀样例

**验证**

```bash
pytest -q admin/tests/test_routes_orders.py -k export
python3 -m mypy admin/routes/orders.py admin/tests/test_routes_orders.py
python3 -m ruff check admin/routes/orders.py admin/tests/test_routes_orders.py
```

---

### P1-4 分享密码存储升级

**目标**

- 将 `data/share/short_link.py` 的无盐 SHA-256 升级为 PBKDF2 / bcrypt / argon2 中至少一种。

**文件**

- `data/share/short_link.py`
- `data/share/tests/test_short_link.py`
- `data/share/tests/test_permission.py`
- `README.md`

**完成标准**

- 新建链接密码使用强哈希
- 兼容迁移策略明确（若已有历史数据）
- 解析与校验路径回归通过

**验证**

```bash
pytest -q data/share/tests
python3 -m mypy data/share/short_link.py
```

---

## 3. P2 — 可以后续做（产品/结构项）

### P2-1 明确是否继续建设用户端 Web 自助闭环

**目标**

- 做产品决策：
  - A. 收缩外部口径，只承认当前是运营后台系统
  - B. 真正建设场景B：用户端下单/支付/填资料/交付

**文件**

- `product/PRD.md`
- `product/ROADMAP.md`
- `docs/BUSINESS_SCENE.md`
- 新计划文档（如需要）

**完成标准**

- 范围决策明确
- 如果做 B，则新建明确实施计划，不再复用旧的漂移状态

---

### P2-2 异常吞噬改为结构化降级日志

**目标**

- 保留兜底能力，但不再 `except Exception: pass` 静默吞掉关键证据。

**文件**

- `data/channel_sync/webhook_server.py`
- `data/share/short_link.py`

**完成标准**

- 兜底路径至少有 debug/warn 级结构化日志
- 不影响主响应契约

---

### P2-3 清理 bandit/mypy 噪声与历史脚本残留

**目标**

- 降低 false positive 比例，让安全/类型门禁可长期使用。

**范围**

- `scripts/legacy/*`
- `tests/*` 中仅测试专用的 assert/subprocess 噪声
- `data/share/short_link.py` 中重复常量 / `_self_test()` 噪声

---

## 4. 模块优先级建议

| 优先级 | 模块                          | 原因                            |
| ------ | ----------------------------- | ------------------------------- |
| P0     | 文档真相层                    | 当前所有后续判断都被它污染      |
| P0     | `data/channel_sync`           | 存在真实安全边界问题            |
| P0     | `admin/auth` / `admin/config` | 默认口令 + 无节流               |
| P0     | `.github/workflows/ci.yml`    | 现有 CI 不能代表项目真实健康    |
| P1     | `data/share`                  | 功能全，但安全/类型债明显       |
| P1     | `admin/*`                     | 覆盖率与类型质量明显偏弱        |
| P2     | 用户端 Web 产品               | 这是范围选择题，不是单纯 bugfix |

---

## 5. 当前最短闭环路径

```text
Step 1 统一文档真相
  ↓
Step 2 修 webhook XFF 信任边界
  ↓
Step 3 修默认 admin 弱口令 + 登录节流
  ↓
Step 4 修 CI clean env 与 coverage/type gate
  ↓
Step 5 再决定是否继续做用户端 Web 自助闭环
```

---

## 6. 禁止的误报口径

在以下事项闭环前，禁止对外宣称：

- ❌ “项目整体完成”
- ❌ “Web 自助产品已可交付”
- ❌ “CI/安全/类型门禁已完善”
- ❌ “已达到完整产品形态”

允许的真实口径：

- ✅ “人工服务场景后台主链已成形”
- ✅ “订单/分享/渠道同步/审核链路已具备可运行实现”
- ✅ “用户端 Web 自助闭环仍未落地”
- ✅ “当前仍需修复文档真相、CI、类型与安全门禁”
