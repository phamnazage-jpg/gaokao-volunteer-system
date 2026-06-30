# CLI_API_MAPPING

最后更新: 2026-06-18
真相源: 本文件是"CLI / HTTP / Skill / 内部 import"四层调用关系的入口索引。
设计上下文: `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §5-§7

---

## 1. 四层关系

```
┌──────────────────────────────────────────────────────────────┐
│ 入口层                                                        │
│  - gaokao-cli (CLI)                                          │
│  - admin FastAPI (HTTP)                                      │
│  - Hermes skill tool (Agent)                                 │
│  - 旧 scripts/* (compatibility, 3-6 个月内 alias)            │
└────────────────┬─────────────────────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ Transport 层 (gaokato/transport/)                            │
│  - cli.py      — argparse/typer 入口                         │
│  - http_client — admin 内部调用封装                           │
│  - skill_adapter — 给 hermes skill 用的稳定接口              │
└────────────────┬─────────────────────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ Application Services 层 (gaokato/services/)                  │
│  - audit.py, order.py, plan.py, report.py,                   │
│    payment.py, majors.py, rules.py, delivery.py             │
└────────────────┬─────────────────────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ Domain 层(现有 data/ 域)                                     │
│  data/rules, data/orders, data/payments, data/majors_catalog,│
│  data/crowd_db, data/notifications                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. CLI 入口对照

| 旧入口                                | 新 CLI 子命令                            | 服务层                      |
| ------------------------------------- | ---------------------------------------- | --------------------------- |
| `scripts/gaokao-checker`              | `gaokao-cli audit run` / `rules list` / `rules explain` / `rules scaffold-evidence` | `gaokato.services.audit`    |
| `scripts/gaokao-audit`                | `gaokao-cli audit run`                   | 同上                        |
| `scripts/gaokao-order-manager`        | `gaokao-cli order {create,get,list,...}` | `gaokato.services.order`    |
| `scripts/gaokao-shortlink`            | `gaokao-cli share {create,list,resolve,...}` | `data/cli_compat_gaokao_shortlink.py` |
| `scripts/gaokao-poster`               | `gaokao-cli share poster`                    | `data/cli_compat_share.py`            |
| `scripts/gaokao-data-trace`           | `gaokao-cli majors list-changes`         | `gaokato.services.majors`   |
| `scripts/gaokao-channel-fallback`     | `gaokao-cli channel fallback`            | (新增)                      |
| `scripts/gaokao-delivery-dispatch.py` | `gaokao-cli delivery dispatch`           | `gaokato.services.delivery` |
| `scripts/gaokao-delivery-watchdog.py` | `gaokao-cli delivery watchdog`           | 同上                        |
| `scripts/gaokao-retention-cleanup.py` | `gaokao-cli retention cleanup`           | (新增)                      |
| `scripts/payment_provider_doctor.py`  | `gaokao-cli payment doctor`              | `gaokato.services.payment`  |
| `scripts/backup_snapshot.sh`          | `gaokao-cli backup snapshot`             | (新增)                      |
| `scripts/backup_verify.sh`            | `gaokao-cli backup verify`               | (新增)                      |

### 2.1 已落地命令清单（2026-06-17 snapshot）

当前 `gaokao-cli` 真实可用的子命令：

| 顶层命令    | 子命令                                                                | 落点                                                             |
| ----------- | --------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `rules`     | `status` / `verify` / `list [--province]` / `explain <rule_id>` / `scaffold-evidence [--province]` | `data/rules/cli.py` `RuleLoader`                                 |
| `majors`    | `status` / `lookup <name>` / `verify` / `changes`                     | `data/majors_catalog/cli.py` `MajorsCatalogLoader`               |
| `majors`    | `school-status --year <y>` / `school-verify --year <y>`               | `data/majors_catalog/cli.py`                                     |
| `audit`     | `run --province <p> --plan <json>`                                    | `data/rules/audit_engine.py` `AuditEngine`                       |
| `share`     | `create/list/resolve/revoke/revoke-report/stats/stats-report/purge` + `poster` | `data/cli_compat_share.py` → `data/cli_compat_gaokao_shortlink.py` / `scripts/gaokao-poster` |
| `payment`   | `doctor`（委派到 `scripts/payment_provider_doctor.py`）               | 复用 `data/cli_compat_payment_doctor.py`                         |
| `channel`   | `check [--flags]` / `manual-template [--flags]`                       | 复用 `data/channel_sync/monitor.py`                              |
| `delivery`  | `dispatch [--channel --limit]` / `watchdog [--channel --limit]`       | 复用 `scripts/gaokao-delivery-{dispatch,watchdog}.py`            |
| `retention` | `cleanup [--flags]`（无子命令，flags 由脚本内部解析）                 | 复用 `data/orders/retention_cleanup.py`                          |
| `backup`    | `snapshot` / `verify`（调用 `scripts/backup_*.sh`）                   | 复用 `scripts/backup_*.sh`                                       |
| `doctor`    | `--json` 自检 rules / majors / majors_verify                          | `data/rules/cli.py`（复用 `RuleLoader` + `MajorsCatalogLoader`） |

---

## 3. HTTP / admin 路由对照

| 现有 admin 路由                                | 服务层                                   |
| ---------------------------------------------- | ---------------------------------------- |
| `admin/routes/orders.py`                       | `gaokato.services.order.*`               |
| `admin/routes/cases.py`                        | `gaokato.services.case.*` (待抽)         |
| `admin/routes/users.py`                        | `gaokato.services.user.*` (待抽)         |
| `admin/routes/stats.py`                        | `gaokato.services.stats.*` (待抽)        |
| `admin/routes/notifications.py`                | `gaokato.services.notification.*` (待抽) |
| `admin/routes/payments.py` (隐含在 web_public) | `gaokato.services.payment.*`             |
| `admin/routes/web_public.py`                   | 直接调 `gaokato.services.*`              |

---

## 4. Hermes skill 调用对照

| Skill                    | 改前                                               | 改后                                                               |
| ------------------------ | -------------------------------------------------- | ------------------------------------------------------------------ |
| `gaokao-counselor-long`  | `import skills.gaokao-audit.scripts.audit_service` | `from gaokato.services import audit` 或 `gaokao-cli audit run ...` |
| `gaokao-audit`           | 自包含脚本                                         | 调 `gaokato.services.audit.audit_plan`                             |
| `gaokao-spec-checker`    | 自包含 regex                                       | 调 `gaokato.services.audit` 薄 wrapper                             |
| `gaokao-college-advisor` | prompt 内部                                        | 调 `gaokato.services.plan.generate`                                |
| `zhangxuefeng-skillset`  | prompt 内部                                        | 不变(只借用表达风格)                                               |

---

## 5. 退出码与输出规范

| 退出码 | 含义                              |
| ------ | --------------------------------- |
| 0      | 成功                              |
| 1      | 业务错误(校验不通过 / 查询无结果) |
| 2      | 调用错误(参数 / IO / 网络)        |
| 3      | 不可恢复(权限 / 数据完整性)       |

JSON 错误:

```json
{
  "ok": false,
  "code": "E05099",
  "message": "...",
  "details": {}
}
```

---

## 6. 智能体能力注册表

`gaokato/capabilities/registry.py` 列出全部能力。每个能力包含:

- `name`
- `description`
- `cli` 子命令路径
- `schema`(参数 JSON schema)
- `risk`(`read` / `write` / `destructive`)
- `roles`(可调用角色)
- `examples`

---

## 7. Phase 4 必须收口

- 全部 25+ 子命令上线
- 旧 scripts/\* 全部 alias + deprecation warning
- `gaokao-cli doctor` 自检全绿
- `gaokato/capabilities/registry.py` 全集登记

---

**下一阶段**: Phase 4-5 实施,见 `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md` §11
