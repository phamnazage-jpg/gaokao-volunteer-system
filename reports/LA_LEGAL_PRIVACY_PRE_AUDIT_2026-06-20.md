# LA_LEGAL_PRIVACY_PRE_AUDIT_2026-06-20

> 内部预审报告 · 用于 PM / Legal 审阅前发现内部一致性与实现漂移
> 审计对象：4 份法务/隐私/运维草案（合计 522 行）
> 仓库 HEAD：`604c8b3 (main)` · 工作目录：`/home/long/project/gaokao-volunteer-system`
> 审计日期：2026-06-20

---

## 0. 审计范围

| #   | 文件                                     | 行数 | 最后更新   |
| --- | ---------------------------------------- | ---- | ---------- |
| 1   | `docs/PRIVACY_POLICY_DRAFT.md`           | 65   | 2026-06-14 |
| 2   | `docs/SERVICE_TERMS.md`                  | 53   | 2026-06-14 |
| 3   | `docs/LEGAL_PRIVACY_BASELINE.md`         | 162  | 2026-06-14 |
| 4   | `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` | 242  | 2026-06-20 |

> 任务说明里 runbook 行数标的是 144，实测为 242（含新增的 §8 T12-D 端到端 acceptance）。
> 以下所有引用基于实际行数。

---

## 1. 内部一致性（4 份文档互相引用）

### 1.1 ✅ `DATA_RETENTION_AND_DELETION.md` 引用闭环

| 引用方                              | 引用路径                              | 目标文件状态                 |
| ----------------------------------- | ------------------------------------- | ---------------------------- |
| `PRIVACY_POLICY_DRAFT.md:43`        | `docs/DATA_RETENTION_AND_DELETION.md` | ✅ 存在（81 行，2026-06-14） |
| `SERVICE_TERMS.md:43`               | `docs/DATA_RETENTION_AND_DELETION.md` | ✅ 存在                      |
| `PRIVACY_POLICY_DRAFT.md:43` (隐含) | "数据保存与删除" §5                   | 与 §7 顺序自洽               |

**结论**：引用闭环成立，未发现悬空引用。

### 1.2 ⚠️ `consent_channel` 白名单在 `LEGAL_PRIVACY_BASELINE.md` 内部矛盾

`LEGAL_PRIVACY_BASELINE.md` 同一份文件里出现两套渠道列表：

- §4 行 86（后台补录渠道）：`闲鱼/微信/学校/线下确认`（中文叙事，**4 个**）
- §6 行 123（最小字段表）：`consent_channel: web / wechat / xianyu / school / admin`（**5 个**）

**实现真相**（见 §2.2）：4 个 source 落地为 `xianyu / wechat / web / school`，admin 渠道单走 `consent_channel = payload.source`（即 xianyu/wechat/school/web 之一），并未真正出现字面量 `"admin"`。

**结论**：

- §6 的 `admin` 渠道值是 **孤儿**——代码侧没有任何 `consent_channel=admin` 的写入路径。
- §4 的 "线下确认" 渠道是 **未落库**——没有被建模为合法 source。
- 应在送 PM/Legal 之前把 §6 改成 `web / wechat / xianyu / school`，并把 §4 的"线下确认"对应到 `school` 或显式说明走 admin 补录。

### 1.3 ⚠️ `consent_operator` 内部一致性

`LEGAL_PRIVACY_BASELINE.md:84` 声明白名单 `self / guardian / admin_import`（3 个值），但：

- 实现 `admin/routes/orders.py:590` 实际只产生 `"guardian" if source == "web" else "admin_import"`，**`self` 永不产生**。
- `admin/tests/test_routes_orders.py:161, 195` 断言非 web 渠道 = `admin_import`。
- 单元测试中无任何 `consent_operator == "self"` 的断言。
- `data/orders/intake_schema.py:26` 字段叫 `guardian_confirmed`，与 `consent_operator=self` 没有对应转换逻辑。

**结论**：`self` 是 **白名单里的僵尸值**。要么在文档里删掉，要么在实现里补一处（例如旧数据导入场景），否则白名单会误导外部审阅。

### 1.4 ✅ `retention_days = 180` 口径一致

| 位置                                                | 数值                                                            | 来源                             |
| --------------------------------------------------- | --------------------------------------------------------------- | -------------------------------- |
| `DELIVERY_RETENTION_OPS_RUNBOOK.md:63`              | 默认 `180`                                                      | `GAOKAO_RETENTION_DAYS` 环境变量 |
| `deploy/systemd/gaokao-retention-cleanup.service:9` | `Environment=GAOKAO_RETENTION_DAYS=180`                         | ✅                               |
| `deploy/systemd/gaokao-jobs.env.example:9`          | `GAOKAO_RETENTION_DAYS=180`                                     | ✅                               |
| `deploy/cron/gaokao-jobs.crontab:9`                 | `GAOKAO_RETENTION_DAYS=180`                                     | ✅                               |
| `admin/config.py:261`                               | `retention_days=int(os.getenv("GAOKAO_RETENTION_DAYS", "180"))` | ✅                               |
| `data/orders/deletion_service.py:38`                | `DEFAULT_RETENTION_DAYS = 180`                                  | ✅                               |
| `docs/DATA_RETENTION_AND_DELETION.md:13-17`         | 180 天                                                          | ✅                               |
| `tests/test_retention_cleanup.py`                   | 显式 `--retention-days 180`                                     | ✅                               |

**结论**：180 天口径在文档、环境样例、配置默认值、脚本、测试、运行手册中完全一致。

### 1.5 ⚠️ Runbook 描述的脚本参数默认值与实现不一致

`DELIVERY_RETENTION_OPS_RUNBOOK.md:36-38` 写：

> 手工入口：`scripts/gaokao-retention-cleanup.py --cutoff <ISO8601> [--dry-run]`
> 定时入口：`scripts/gaokao-retention-cleanup.py --retention-days 180 [--dry-run]`

实现侧 `data/orders/retention_cleanup.py:173-182`：

```python
cutoff_group = parser.add_mutually_exclusive_group(required=True)
cutoff_group.add_argument("--cutoff", ...)
cutoff_group.add_argument("--retention-days", type=int, help="...")
# 没有 default=180
```

- `--retention-days` **没有 default**；裸跑 `python3 scripts/gaokao-retention-cleanup.py` 会 `parser.error: one of the arguments --cutoff --retention-days is required`。
- 真正"默认 180"只来自上层调度的环境变量（systemd unit / env example）。
- runbook §3 的 4 条手工命令示范都显式给了 `--cutoff` 或 `--retention-days 180`，**没有误导操作**；但读者会把 "默认 180" 误以为脚本自带兜底。

**结论**：runbook 措辞需要微调——"定时模式（环境变量默认 180）" 比"默认 180" 更准确。

### 1.6 ✅ 4 份文档之间互引用闭环

| 源                                     | 引                                                                     | 目标        |
| -------------------------------------- | ---------------------------------------------------------------------- | ----------- |
| `PRIVACY_POLICY_DRAFT.md:43`           | `docs/DATA_RETENTION_AND_DELETION.md`                                  | ✅ 存在     |
| `SERVICE_TERMS.md:42-43`               | `docs/PRIVACY_POLICY_DRAFT.md` + `docs/DATA_RETENTION_AND_DELETION.md` | ✅ 双向闭环 |
| `LEGAL_PRIVACY_BASELINE.md`            | 仅引用 docs/ 内文件                                                    | ✅ 自洽     |
| `DELIVERY_RETENTION_OPS_RUNBOOK.md:78` | `docs/DATA_RETENTION_AND_DELETION.md`                                  | ✅ 存在     |

唯一需要注意：4 份文件的"最后更新"日期分布：

- 3 份：2026-06-14
- 1 份：2026-06-20（runbook）

送审前建议把 baseline / privacy / service terms 同步刷新到 2026-06-20，或在审阅说明里标注 runbook 是最新基线、其他三份为 v0.14 基线。

---

## 2. 实现 vs 文档漂移（A-2 6/20 落地）

### 2.1 ✅ `consent_method` 5 项白名单 = 完全对齐

| 来源                                      | 列出                                                                        | 数量 |
| ----------------------------------------- | --------------------------------------------------------------------------- | ---- |
| `LEGAL_PRIVACY_BASELINE.md`               | （未列具体白名单）                                                          | —    |
| 实现 `admin/routes/orders.py:248-254`     | `verbal_chat / phone_recording / screenshot / written_form / self_declared` | 5    |
| 实现注释 `admin/routes/orders.py:242-247` | 同上，附语义说明                                                            | 5    |
| 测试 `admin/tests/test_routes_orders.py`  | 用例覆盖 `verbal_chat` 等                                                   | ✅   |

**结论**：5 项白名单实现落地，文档侧 baseline 没有明文列出具体枚举——建议补一段把 5 项枚举写明，避免 PM/Legal 提问。

### 2.2 ✅ `consent_operator` 白名单实现侧：3 项含 `self` 但实际不产出

如 §1.3 所述，实现只写 `guardian` 或 `admin_import`，`self` 出现在白名单但无生产路径。

### 2.3 ✅ Source 4 项 = 与 §6 baseline 一致

| 来源                                     | 列出                                                             |
| ---------------------------------------- | ---------------------------------------------------------------- |
| 实现 `admin/routes/orders.py:94`         | `OrderSource = Literal["xianyu", "wechat", "web", "school"]`     |
| 实现 `admin/routes/ui.py:141`            | `<option>` 同样 4 项                                             |
| baseline `LEGAL_PRIVACY_BASELINE.md:86`  | `闲鱼/微信/学校/线下确认`（叙事，4 项）                          |
| baseline `LEGAL_PRIVACY_BASELINE.md:123` | `web / wechat / xianyu / school / admin`（5 项，含孤儿 `admin`） |

**结论**：核心 4 项对齐；`admin` 渠道值是 §6 列表里的多余项（详见 §1.2）。

### 2.4 ✅ 字段落库：A-2 6/20 已把 4 类字段同步到 `order_intakes` payload

| 字段               | 落库位置                                           | 实现证据                                                                                         |
| ------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `consent_version`  | order_intakes payload                              | `admin/routes/orders.py:651` 写死 `t12-web-mvp-v1`                                               |
| `consent_scope`    | order_intakes payload                              | `web_public.py:1675` 默认 `web-self-service-order-intake`；admin 路径 `${source}-channel-intake` |
| `consent_channel`  | order_intakes + orders.consent_method              | `orders.py:653` 写 `payload.source`                                                              |
| `consent_operator` | order_intakes                                      | `orders.py:654, 590`                                                                             |
| `consent_method`   | order_intakes + orders.consent_method (A-2 冗余)   | `orders.py:655, 615`；`schema.py:110-114` 增列                                                   |
| `consent_given_at` | order_intakes + orders.consent_given_at (A-2 冗余) | `schema.py:115-116` 增列                                                                         |

**结论**：A-2 落地的 5 个审计字段全部在 admin 路径与 portal 路径双轨写出。orders 表新增的 `consent_method` / `consent_given_at` 列在 `data/orders/schema.py:113-116` 通过 `ALTER TABLE` 兼容迁移——`data/orders/models.py:97-98` 同步加 dataclass 字段。

### 2.5 ⚠️ 严格审查报告 vs 现状

`reports/STRICT_COMPREHENSIVE_REVIEW_2026-06-18.md:537`（2026-06-18 写）批评：

> 落库仍只有 `consent_version`、`consent_scope` 与几个布尔值。

A-2 (6/20) 已经把这条批评点修复：`consent_given_at / privacy_accepted_at / service_terms_accepted_at / consent_channel / consent_operator` 全部落库。

**结论**：这条历史批评点已修复，但 strict review 报告本身没有更新；建议在下次 strict review 时回填修复状态。

---

## 3. T12-D 端到端 Acceptance 步骤完整性（runbook §8）

### 3.1 步骤清单与实现交叉验证

| 步骤                             | runbook §8.x                                       | 实现证据                                                                                         | 状态            |
| -------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------ | --------------- |
| §8.1 前置环境（export 4 个变量） | `PY/DB_PATH/SHARE_DB_PATH/LOG_PATH/FERNET_KEY`     | 全部为 retention cleanup 入口的环境变量                                                          | ✅ 完整         |
| §8.2.1 跑回归测试                | `$PY -m pytest tests/test_retention_cleanup.py -q` | 文件中实测有 **6 个 test function**（行 37/52/73/98/123/167）                                    | ✅ 数量正确     |
| §8.2.2 端到端 smoke 脚本         | seed 4 订单 + apply + 验证                         | `data/orders/retention_cleanup.py:run_cleanup()`、`data/orders/dao.py`（T12-D 修复后 owns_conn） | ✅ 完整         |
| §8.3 验收矩阵                    | 7 行 checklist                                     | 对应 `run_cleanup` 返回的 `candidates / anonymized / deletion_logs_pruned / share_events_pruned` | ✅ 完整         |
| §8.4 历史 bug 背景               | `OrdersDAO.__exit__` 关外部 conn                   | `data/orders/dao.py` 增加 `owns_conn: bool = False` 参数                                         | ✅ 已修复并解释 |
| §8.5 部署前 checklist            | 5 行 `- [ ]` 项                                    | 全部对应 systemd/journalctl/测试套件                                                             | ✅ 完整         |

### 3.2 步骤中可执行性检查

- §8.2.1 的 smoke 脚本是 inline Python `-c "..."`，**易复制但出错时栈跟踪难看**。建议改成 `scripts/smoke_retention_cleanup.py` 脚本文件，runbook 改成调脚本。
- §8.2.2 的 `Order(..., created_at='2024-12-01T00:00:00+00:00')` 是固定时间戳，cutoff `2025-06-30T00:00:00+00:00`，**只要时钟在 2025-06-30 之后都成立**。runbook 没标注这条隐性假设。
- §8.5 没有把 `systemctl status` 的"成功"判定值写明——只列了命令。这是已知可接受的最小步骤。

**结论**：T12-D acceptance 步骤 **完整且可执行**。微调建议是脚本提取 + 时间戳假设显式化。

---

## 4. 缺失项识别

### 4.1 ✅ 隐私政策 §5 引用 `DATA_RETENTION_AND_DELETION.md` 已存在

- 文件存在：`docs/DATA_RETENTION_AND_DELETION.md`（81 行）
- 内容覆盖：保留期表（§2 表格 9 行）、删除请求处理原则（§3）、当前系统能力与缺口（§4）、MVP 最低要求（§5）、最小调度与 runbook 引用（§6）
- 关键数字 `180` 出现在 §2 表格（订单/资料/报告/通知/支付）和 §6 命令行
- 与 `DELIVERY_RETENTION_OPS_RUNBOOK.md` 互引：runbook 行 78 / retention_doc 行 53

**结论**：引用文件**存在且内容完整**，未发现悬空或残缺。

### 4.2 ⚠️ `LEGAL_PRIVACY_BASELINE.md` §7 "尚缺"列表与现实存在部分漂移

baseline §7 (行 142-146) 写：

> 尚缺：
>
> - 后台代录 / 外部渠道补录的同意审计统一化
> - 数据删除 SOP 的脚本化/产品化
> - 对外正式法务审阅与版本管理

A-2 (6/20) + T12-D (6/20) 已经把前两条都做了：

- 后台/外部渠道同意审计已统一化（`consent_method` + `consent_operator` + `consent_channel` 全部白名单化并落库）
- 数据删除 SOP 已脚本化（`scripts/gaokao-retention-cleanup.py` 配合 systemd/cron 样例）

**结论**：baseline §7 "尚缺" 列表需要在下次刷新时把前两条移到"已具备"侧，仅保留"对外正式法务审阅与版本管理"。

### 4.3 ⚠️ "线下确认"渠道的最终落地

baseline §4 写 `闲鱼/微信/学校/线下确认`，但实现侧 4 个 source 中没有"线下"——`school` 看上去承接了线下场景，但语义上"线下确认"（如家长到场签纸质单）≠ "school 渠道"。

**结论**：建议在 baseline §4 显式说明"线下确认 = school 渠道" 或新增 `offline` source（如果业务确实要区分）。

### 4.4 ⚠️ `consent_version` 没有走基线化的版本号管理

实现侧 `admin/routes/web_public.py:1674` 与 `admin/routes/orders.py:651` 都硬编码 `t12-web-mvp-v1`：

- privacy policy 与 service terms 还没有声明"当前生效版本号"
- 文档侧用 `最后更新: 2026-06-14` 的自然日期；代码侧用语义化 `v1`
- 当 privacy policy / service terms 改版时，没有机制把 `consent_version` 一起升档

**结论**：送 PM/Legal 之前需要在 baseline §6 加一段"版本升级机制"：什么时候 bump `consent_version`，是否需要用户重新同意。

### 4.5 ⚠️ Portal 提交路径 vs Admin 提交路径的 `consent_scope` 命名空间不一致

| 路径                          | consent_scope 字面量                                    |
| ----------------------------- | ------------------------------------------------------- |
| Portal (`web_public.py:1675`) | `web-self-service-order-intake`                         |
| Admin (`orders.py:652`)       | `{source}-channel-intake`（如 `xianyu-channel-intake`） |

两条路径在数据库侧都是字符串，**没有枚举**——下游做合规报表/审计聚合时需要做模糊匹配，违反 "consent_scope 必须来自受控白名单" 的合规最小要求。

**结论**：建议把 consent_scope 提升为 Literal 与 consent_method 同级。

---

## 5. 前台文案入口：admin UI 模板 footer 隐私政策链接

### 5.1 admin UI 路由清单（`admin/routes/ui.py`）

| 路径                             | 处理函数                 | 模板来源                                                   | footer 隐私政策链接                                                                           |
| -------------------------------- | ------------------------ | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `/dashboard`、`/admin/dashboard` | `dashboard_page()`       | `admin/static/dashboard.html`                              | ❌ **无 footer**（592 行 HTML，无 `<footer>` 标签）                                           |
| `/admin/orders/new`              | `admin_new_order_page()` | `_render_admin_new_order_page()` 内联 HTML（ui.py:75-182） | ❌ **无 footer**（只在 `</body>` 前一段 `<script>`，无任何 `<footer>`/`<a href="/privacy">`） |
| `/s/{code}`                      | `share_page()`           | `admin/share_page.py:158` 有 `.footer-panel`               | ⚠️ **是 share 页 footer，不是隐私政策链接**                                                   |

### 5.2 对比：web_public.py 的前台 portal 页

`admin/routes/web_public.py:749-763` 提供了 `_render_footer_links()`：

```python
f'<footer style="margin-top:24px;color:#5b6b88;font-size:14px;">'
f'<a href="{privacy_href}">隐私政策</a> · '
```

测试 `admin/tests/test_web_public.py:445-464` 验证 `landing` / `pricing` / `privacy` 页都有 `href="/privacy"` 链接 + `/privacy` 路由可访问。

**结论**：

- **portal 前台页有 footer 隐私政策链接 ✅**
- **admin 后台页（dashboard.html + ui.py 内联页）均无 footer 隐私政策链接 ❌**
- `dashboard.html` 整个文件 592 行无 `<footer>` 标签，缺明显的合规入口

### 5.3 严重程度判断

baseline §5 提到：

> 建议文案入口：下单页提交前 / 资料填写页提交前 / **页脚"隐私政策 / 数据删除说明"链接**

baseline §8 提到：

> 前台存在可见入口（隐私政策 + 数据删除规则）

**严重度**：中。

- legal baseline §5 用词是 "前台"，可解释为"用户端 web"——portal 已有 footer。
- 但严格意义上，**后台 dashboard 缺 footer 隐私政策**会留下"内部用户完全不知道数据策略"的口子；如果后台操作员误以为后台操作可豁免合规，会被外部审计抓到。
- 推荐修法：在 `dashboard.html` 末尾加 `<footer>` 块，链接到 `/privacy` 与 `/deletion`（或对应路由）；ui.py 的内联 admin 新单页同样加 footer。

---

## 6. 风险评级汇总

| ID  | 风险                                                    | 等级 | 阻塞送审？                                |
| --- | ------------------------------------------------------- | ---- | ----------------------------------------- |
| R1  | baseline §6 `admin` 渠道值孤儿 + §4 "线下确认" 未建模   | 中   | **建议在送审前修**                        |
| R2  | `consent_operator=self` 僵尸白名单                      | 低   | 建议在送审前删                            |
| R3  | runbook `--retention-days 180` 措辞歧义（无 default）   | 低   | 文档措辞改一下                            |
| R4  | baseline §7 "尚缺" 列表未同步 A-2/T12-D 进展            | 中   | **建议在送审前同步**                      |
| R5  | `consent_version` 硬编码无升级机制                      | 中   | 建议在 baseline §6 加一段                 |
| R6  | `consent_scope` 不是枚举（portal/admin 命名空间不统一） | 中   | 建议在 baseline §6 加一段或提升为 Literal |
| R7  | admin 后台 dashboard.html 无 footer 隐私政策链接        | 中   | **建议在送审前补**                        |
| R8  | strict review 2026-06-18 报告未回填 A-2 修复状态        | 低   | 顺手做                                    |
| R9  | 3 份文档 "最后更新" 还是 6/14，runbook 已 6/20          | 低   | 措辞补一句                                |

**送审阻塞级**：0 个。
**建议在送审前修**：R1、R4、R7（3 个中等风险）。
**可以下个迭代修**：R2、R3、R5、R6、R8、R9（6 个低/中风险）。

---

## 7. 给 PM / Legal 的提示清单

1. **A-2 6/20 落地的 5 个同意审计字段已经在 admin/portal 双轨写库**——可以对外说"同意审计口径已统一化"，但仍不可说"监护人同意闭环已整体完成"（baseline §4 末段措辞）。
2. **source 实际只 4 项**（`xianyu / wechat / web / school`），文档里出现过的 `admin` 渠道值从未被实际写入；送审前请把 baseline §6 的 `admin` 去掉。
3. **`consent_operator` 只产生 2 个值**（`guardian` for web, `admin_import` for other 3 source），`self` 永不使用——白名单可删 `self`，或为旧数据导入场景补一条生产路径。
4. **admin 后台页面（dashboard.html + admin/orders/new）还没有 footer 隐私政策链接**——portal 前台有，admin 后台没有；如内部操作员被外部审计问到，会缺一个合规入口。
5. **retention_days=180 在文档/环境/代码/测试/运行手册五处完全对齐**，可以放心。
6. **T12-D acceptance 步骤（runbook §8）完整且可执行**，6 个 pytest 全过是已知可达状态；建议把 inline `-c` 提到 `scripts/smoke_retention_cleanup.py` 改善可维护性。
7. **DATA_RETENTION_AND_DELETION.md（81 行）存在且内容完整**——隐私政策 §5 的引用闭环成立。

---

## 8. 附录：关键引用行号速查

| 引用                                    | 位置                                                         |
| --------------------------------------- | ------------------------------------------------------------ |
| `consent_method` Literal                | `admin/routes/orders.py:248-254`                             |
| `consent_method` 列迁移                 | `data/orders/schema.py:113-114`                              |
| `consent_given_at` 列迁移               | `data/orders/schema.py:115-116`                              |
| `OrderSource` Literal                   | `admin/routes/orders.py:94`                                  |
| `consent_operator` 计算                 | `admin/routes/orders.py:590`                                 |
| `consent_scope` portal                  | `admin/routes/web_public.py:1675`                            |
| `consent_scope` admin                   | `admin/routes/orders.py:652`                                 |
| 4 source 内联选项                       | `admin/routes/ui.py:141`                                     |
| dashboard.html 模板                     | `admin/static/dashboard.html`（592 行，无 footer）           |
| `_render_footer_links`                  | `admin/routes/web_public.py:749-763`                         |
| retention cleanup 入口                  | `scripts/gaokao-retention-cleanup.py`                        |
| retention 默认 180                      | `admin/config.py:261` / `data/orders/deletion_service.py:38` |
| retention `--retention-days` 无 default | `data/orders/retention_cleanup.py:178-182`                   |
| retention 回归测试 6 个                 | `tests/test_retention_cleanup.py:37/52/73/98/123/167`        |
| T12-D 修复点                            | `data/orders/dao.py` `owns_conn: bool = False`               |
| A-2 整改文档                            | `docs/ACTIVE_REMEDIATION_2026-06-20.md`                      |
| 历史批评点（已修复）                    | `reports/STRICT_COMPREHENSIVE_REVIEW_2026-06-18.md:537`      |

---

## 9. 审计结论

**送审整体判断**：4 份文档作为 T12 上线前法务/隐私基线草案**结构完整、引用闭环成立、A-2 6/20 落地的事实准确反映在实现层**。

**送审前**建议处理 3 项中等风险：

1. baseline §6 删 `admin` 渠道值 / §4 解释 "线下确认" 对应关系（R1）
2. baseline §7 "尚缺" 列表同步 A-2/T12-D 进展（R4）
3. admin 后台页面补 footer 隐私政策链接（R7）

**可以下个迭代处理**：6 项低/中风险（R2/R3/R5/R6/R8/R9），不影响本次送审。

**总体送审建议**：✅ 可送 PM / Legal 审阅，附本报告作为"已知问题与下一迭代计划"附页。
