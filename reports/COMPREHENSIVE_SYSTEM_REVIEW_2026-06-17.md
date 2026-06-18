# 高考志愿填报项目全面系统评审报告

**项目路径**: `/home/long/project/gaokao-volunteer-system`  
**评审日期**: 2026-06-17  
**主审**: Codex  
**邀请专家**:

- 产品规划评审专家
- 技术架构评审专家
- 实现质量评审专家

**评审范围**:

- 产品定位、PRD、ROADMAP、市场与商业化文档
- 管理后台、用户端 Web 自助链路、支付、通知、备份恢复、规则审计 CLI
- 测试、验证脚本、运维 runbook、部署模板

## 0. 2026-06-18 复核说明

本报告第 4 节保留的是 2026-06-17 的审计基线问题，用于追溯；截至 2026-06-18，P0 / P1 已全部闭环，P2-1 / P2-3 / P2-4 也已验证通过。当前仍未闭环的是 P2-2：其余 `4` 省真实 evidence 摘录；证据层模板脚手架已经补齐，但不应与真实摘录混为一谈，北京、湖南、江苏、浙江、上海、安徽、山东、广东、湖北、河北、海南、福建、四川、江西、甘肃、贵州、云南、辽宁、吉林、黑龙江、广西、青海、西藏已完成省级样本闭环，其中河北、海南、福建、四川、江西、甘肃、贵州、云南、辽宁、吉林、黑龙江、广西、青海、西藏都已达 `11/11`。

---

## 1. 执行摘要

### 1.1 总体结论

本项目当前更准确的定位，仍然是：

> **已完成“人工服务运营增强系统 + AI 审核增强链路”，但尚未形成可以稳定对外承诺的完整 Web 自助 SaaS 闭环。**

本轮评审结论为：

> **`REQUEST_CHANGES / 条件不通过`**

原因不是“功能太少”，而是以下三类问题同时存在：

1. **产品口径未统一**：产品文档仍在同时描述“人工服务运营系统”和“完整 Web 自助产品”两种商业形态。
2. **关键工程闭环不可靠**：支付、通知、备份恢复、规则审计等主链路存在会直接影响生产正确性的缺陷或半开闭环。
3. **文档与实现多处漂移**：真相源、README、架构文档、运维 runbook 之间仍有实质性矛盾。

2026-06-18 复核后，以上三类问题在 P0 / P1 维度已经全部闭环，`REQUEST_CHANGES` 结论仅保留为 2026-06-17 的历史基线，不再代表当前工作树状态。

### 1.2 综合评分

| 维度 | 评分 | 结论 |
| --- | --- | --- |
| 产品定位与边界 | C+ | 定位在 `CURRENT_STATE` 中已收口，但 PRD/市场/路线图仍未统一 |
| 商业化规划 | C | 定价、渠道、启动时间、产品形态在多份文档中相互冲突 |
| 技术架构 | B- | 分层方向务实，但支付/通知/备份等关键基础设施仍有断点 |
| 实现质量 | C+ | 代码量与测试量可观，但关键边界条件仍存在真实缺陷 |
| 可运维性 | C | 灾备链路、生产 fail-closed、恢复演练可信度不足 |
| 合规与对外表述 | C | 边界已在 `CURRENT_STATE` 中收紧，但产品文档仍过度乐观 |

### 1.3 当前建议

当前不建议把本仓库按“完整用户端自助产品”对外承诺或对外验收。  
但从工程闭环角度，支付、备份恢复、规则审计、专业目录和文档真相源的 P0 / P1 / P2-1 / P2-3 / P2-4 已完成回归验证；剩余工作只应聚焦 P2-2 的其它 `4` 省真实 evidence 补摘录，而不应再把已完成项当作阻塞项。

---

## 2. 评审方法与证据

### 2.1 核心阅读材料

- `docs/CURRENT_STATE.md`
- `README.md`
- `product/PRD.md`
- `product/ROADMAP.md`
- `product/MARKET_RESEARCH.md`
- `docs/TECH_ARCHITECTURE.md`
- `docs/PAYMENT_DOMAIN_DESIGN.md`
- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`

### 2.2 重点抽样代码

- `admin/config.py`
- `admin/app.py`
- `admin/routes/web_public.py`
- `admin/db.py`
- `data/payments/service.py`
- `data/payments/dao.py`
- `data/notifications/email_service.py`
- `data/notifications/dispatcher.py`
- `data/rules/audit_engine.py`
- `data/rules/cli.py`
- `scripts/dev-verify.sh`
- `scripts/backup_snapshot.sh`
- `scripts/backup_restore_smoke.py`

### 2.3 本轮实证复核

本轮做了若干最小复现，确认以下问题不是纯文档推断：

1. **退款后重复收到成功回调，会把 payment 从 `refunded` 写回 `paid`，但订单仍停留在 `refunded`。**

复现结果：

```python
{'payment_status': 'paid', 'order_status': 'refunded'}
```

2. **规则审计 CLI 读取到了 `max_volunteers=45`，但 `audit_plan()` 仍返回通过。**

复现结果：

```python
45
{'province': '湖南', 'overall_pass': True, 'issues': []}
```

3. **管理库开启 WAL 后，`backup_snapshot.sh` 只复制 `admin.db` 本体，备份副本中表列表为空。**

复现结果：

```python
live_tables ['admin_users', 'sqlite_sequence']
backup_tables []
```

4. **`GAOKAO_SKIP_INSTALL=1` 仍会触发 `python -m pip install --upgrade pip`，离线环境会访问 PyPI。**

本轮执行 `GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh` 时实际出现了 `pypi.org` DNS 重试。

---

## 3. 专家评审结论

### 3.1 产品规划评审专家

核心结论：

- 项目定位、MVP 边界、商业化节奏仍未统一。
- PRD、ROADMAP、MARKET_RESEARCH 仍在描述不同的产品形态和不同的收入模型。

### 3.2 技术架构评审专家

核心结论：

- 支付上线默认不是 fail-closed。
- 通知多渠道、备份恢复、生产运维闭环存在结构性缺口。

### 3.3 实现质量评审专家

核心结论：

- 灾备链路存在“表面成功、实际不可恢复”的高风险。
- 新的 `audit run` 命令面仍停留在 majors-only，未真正执行省规则。

---

## 4. 主要发现

### 4.1 P0 / 严重问题

#### P0-1 产品定位与 MVP 边界仍未统一

**问题**

`docs/CURRENT_STATE.md` 已明确当前产品是“人工服务运营增强系统”，不能对外表述为完整 Web 自助 SaaS（`docs/CURRENT_STATE.md:42-58`, `docs/CURRENT_STATE.md:191-204`）。  
但 `product/PRD.md:470-519` 仍把 `Web系统流程`、系统内付费、自动建单、站内查看与邮件交付写成并列核心业务流程；`product/MARKET_RESEARCH.md:411-425` 又把项目描述为“免费/低价、全流程、纯 AI”工具；`product/ROADMAP.md:269-339` 则把商业化启动、支付接入、Web 发布拆到了多个不同阶段。

**影响**

- 验收标准无法统一
- 对外承诺容易失真
- 排期、投入优先级、商业化节奏持续漂移

**结论**

这是当前最上游的问题。只要定位不统一，后续技术与产品评审都会继续互相打架。

#### P0-2 支付回调可把已退款 payment 回写为 `paid`，导致支付与订单状态分裂

**证据**

- `data/payments/service.py:252-283`
- `data/payments/dao.py:104-147`
- `data/orders/state_machine.py:25-46`

`handle_webhook()` 只把“当前 payment 已是 `paid`”视为幂等；若 payment 当前为 `refunded`，收到成功回调后仍会执行 `payments.update_status(..., status="paid")`。订单侧因已处于终态 `refunded`，不会回退，于是形成：

- payment = `paid`
- order = `refunded`

**本轮复现**

```python
{'payment_status': 'paid', 'order_status': 'refunded'}
```

**影响**

- 财务语义错误
- 售后/退款状态与支付记录矛盾
- 后续统计、对账、客服判断都会失真

#### P0-3 生产支付 provider 没有 fail-closed，生产模板默认仍是 `mock`

**证据**

- `admin/config.py:161-205`
- `admin/app.py:63-92`
- `.env.docker.example:2-14`
- `admin/routes/web_public.py:238-279`
- `admin/routes/web_public.py:1550-1589`
- `docs/PAYMENT_DOMAIN_DESIGN.md:105-115`

当前：

- `GAOKAO_PAYMENT_PROVIDER` 默认值是 `mock`
- 启动校验不校验 provider 是否为真实支付
- 生产示例 `.env.docker.example` 同时写了 `GAOKAO_ENV=prod` 与 `GAOKAO_PAYMENT_PROVIDER=mock`
- 模拟支付页与模拟支付完成入口仍长期暴露

**影响**

- 生产环境可能被错误地跑在模拟支付上
- 真实支付验收边界被污染
- 对外“已支持支付”的说法不可信

#### P0-4 `gaokao-cli audit run` 当前并没有真正执行省规则审计

**证据**

- `data/rules/audit_engine.py:32-52`
- `data/rules/cli.py:196-203`
- `tests/test_audit_cli_major_validation_phase2.py:88-163`

`AuditEngine.get_province_snapshot()` 能读出 `mode / max_volunteers / retrieval_rule`，但 `audit_plan()` 当前只做 `_validate_majors()`，完全没有执行省规则检查。

**本轮复现**

在真相源中配置湖南 `max_volunteers=45`，构造 46 个志愿项后，结果仍是：

```python
{'province': '湖南', 'overall_pass': True, 'issues': []}
```

**影响**

- CLI 对外输出“通过”并不等于方案合规
- 容易造成错误信任
- 与 `CURRENT_STATE` 中“统一审计引擎最小可用”的说法不一致

#### P0-5 管理库备份在 WAL 模式下是“假成功”快照

**证据**

- `admin/db.py:27-42`
- `scripts/backup_snapshot.sh:134-141`
- `tests/test_backup_workflow.py:24-31`
- `tests/test_backup_workflow.py:80-91`

`admin.db` 被强制切到 WAL 模式，但 `backup_snapshot.sh` 只复制 `admin.db` 本体，不做 checkpoint，也不复制 `-wal/-shm`。

**本轮复现**

```python
live_tables ['admin_users', 'sqlite_sequence']
backup_tables []
```

**影响**

- 快照看起来存在，实际恢复后管理员表可能为空
- 属于灾备失效级问题

---

### 4.2 P1 / 高优先级问题

#### P1-1 `payments` 缺少“每订单单一活跃支付单”约束，存在 portal 阶段回退风险

**证据**

- `data/payments/dao.py:14-33`
- `data/payments/service.py:137-180`
- `admin/routes/web_public.py:578-624`
- `docs/PAYMENT_DOMAIN_DESIGN.md:111-125`

当前没有 `UNIQUE(order_id)` 或“单活跃单”约束，`create_checkout()` 也是典型 check-then-insert。  
一旦出现重复 pending payment，portal 阶段推导逻辑会优先显示 `pending_payment`。

**影响**

- 支付事实源不稳定
- portal 状态可能与订单真实状态矛盾
- 并发或重复创建支付单时存在结构性风险

#### P1-2 通知表唯一键忽略 `channel`，多渠道通知在架构上就不成立

**证据**

- `data/notifications/email_service.py:11-29`
- `data/notifications/email_service.py:107-130`
- `data/notifications/dispatcher.py:48-123`

唯一约束当前是 `UNIQUE(order_id, event_type)`，没有包含 `channel`。  
结果是同一订单同一事件无法同时存在 `station` 与 `email` 两条通知；冲突还会被静默 `rollback()`。

**影响**

- 多渠道通知设计失真
- 运维上看似支持多渠道，实际只能留一条
- 冲突无告警，排查困难

#### P1-3 备份范围未覆盖真实上传附件与订单挂载的交付文件

**证据**

- `docs/BACKUP_AND_RECOVERY_PLAN.md:8-14`
- `admin/config.py:196-199`
- `admin/routes/web_public.py:352-379`
- `scripts/backup_snapshot.sh:9-16`
- `scripts/backup_snapshot.sh:134-141`

文档宣称要覆盖“上传/分享产物”，但脚本只备份：

- `admin.db`
- `orders.db`
- `short_links.db`
- `share_report_dir`
- `data/examples`

没有备份：

- `GAOKAO_PORTAL_UPLOAD_DIR`
- 订单记录引用的 `audit_report` / `pdf_path` 真实文件

**影响**

- 数据库恢复成功但用户附件/交付物丢失
- 业务上仍不可恢复

#### P1-4 restore smoke 会注入伪造密钥并强制 `mock` provider，容易产生“恢复已验证”的假阳性

**证据**

- `scripts/backup_restore_smoke.py:17-20`
- `scripts/backup_restore_smoke.py:90-109`
- `docs/BACKUP_AND_RECOVERY_PLAN.md:13-14`
- `docs/BACKUP_AND_RECOVERY_PLAN.md:33-40`

restore smoke 会在恢复演练时注入默认 JWT/Fernet/Admin/Payment 配置，并强制：

- `GAOKAO_PAYMENT_PROVIDER=mock`
- `GAOKAO_PAYMENT_BASE_URL=http://testserver`

**影响**

- 即使真实密钥、真实支付配置未恢复，也可能通过演练
- 运维误判恢复质量

#### P1-5 README、TECH_ARCHITECTURE、runbook 与当前真相源仍有实质性漂移

**证据**

- `README.md:168-173`
- `docs/CURRENT_STATE.md:177-181`
- `docs/TECH_ARCHITECTURE.md:100-139`
- `docs/DELIVERY_RETENTION_OPS_RUNBOOK.md:18-20`
- `data/notifications/dispatcher.py:48-123`

典型矛盾：

- README 仍写 `ready -> sent`，但 `CURRENT_STATE` 已明确 `sent` 已移除
- runbook 写 dispatcher 处理 `ready` 与 `failed`，代码实际处理 `ready` 与 `validated`
- 技术架构文档仍把若干现状写成“硬编码脚本 / 临时文件 / 管理后台 CLI”，与当前实现不符

**影响**

- 对外和对内沟通成本上升
- 新成员容易被旧文档误导
- 运维执行口径失真

---

### 4.3 P2 / 中优先级问题

#### P2-1 `dev-verify.sh --skip-install` 不遵守“跳过安装”契约，离线环境仍访问网络

**证据**

- `scripts/dev-verify.sh:32-56`
- 尤其是 `scripts/dev-verify.sh:46`

虽然脚本支持 `GAOKAO_SKIP_INSTALL=1` / `--skip-install`，但 `ensure_venv()` 仍固定执行：

```bash
python -m pip install --upgrade pip >/dev/null
```

因此离线环境下即便“跳过安装”，仍会访问 PyPI。

**影响**

- 本地一键验证不可靠
- 离线/受限网络环境体验差
- 与脚本对外承诺不一致

#### P2-2 `test_backup_verify_runs_restore_smoke_on_snapshot` 已被长期列入已知失败，说明灾备校验主链并不稳定

**证据**

- `scripts/dev-verify.sh:12-25`
- `tests/test_backup_workflow.py:99-122`

当前验证脚本把备份恢复相关用例长期放进 `PRE_EXISTING_IGNORES`。  
这意味着最需要被保护的灾备链路，反而被默认从一键验证中弱化掉了。

#### P2-3 当前测试没有覆盖退款后成功回调重入，也没有覆盖省规则审计本体

**证据**

- `data/payments/tests/test_service.py:49-124`
- `data/payments/tests/test_webhook.py:28-195`
- `tests/test_audit_cli_major_validation_phase2.py:88-163`

当前测试覆盖了：

- 正常支付成功
- 幂等成功回调
- 金额不一致
- app_id / merchant_id / notify_id 校验

但没有覆盖：

- `refunded -> paid` 回归
- `max_volunteers` / `mode` / `retrieval_rule` 等省规则落地

---

## 5. 已修复历史问题

以下问题本轮不再计为当前阻塞项：

- PRD P2/P3 功能编号冲突  
  证据：`docs/CURRENT_STATE.md:119-128`，当前 `product/PRD.md:157-165` 已使用 `F021-F025`
- ROADMAP 已落地功能勾选状态不同步  
  证据：`docs/CURRENT_STATE.md:121-128`，当前 `product/ROADMAP.md:142-206` 已完成首轮修正
- “TECH_ARCHITECTURE 仍标设计中”  
  证据：`docs/CURRENT_STATE.md:123-127`

这部分需要与当前真实问题分开，避免重复引用旧结论造成噪音。

### 5.1 2026-06-18 闭环复核

- P0-1 / P0-2 / P0-3 / P0-4 / P0-5 已由最新回归重新确认通过。
- P1-1 / P1-2 / P1-3 / P1-4 / P1-5 已由最新回归重新确认通过。
- P2-1 / P2-3 / P2-4 已由最新回归重新确认通过。
- P2-2 已完成 stale 告警联动、evidence matrix、`rules scaffold-evidence` 脚手架和模板索引；北京、湖南、江苏、浙江、上海、安徽、山东、广东、湖北、河北、海南、福建、四川、江西、甘肃、贵州、云南、辽宁、吉林、黑龙江、广西、青海、西藏、新疆、天津、河南、重庆都已闭环 `11/11`，其中重庆普通类本科批已按重庆市教育考试院 `2025-06-17` 志愿设置 / 录取规则问答、`2026-06-09` 考后时间节点安排与重庆市教委 `2025` 实施办法，将旧的 `batch: 普通批` 修正为 `本科批`、`collection_count: 1` 修正为动态机读口径 `null`，并确认 `专业+学校 / 96 / 无调剂 / 分数优先、遵循志愿、一次投档 / 3+1+2 / 750` 口径；当前 `rules status --json` 已推进到 `evidenced_rule_count=298`、`missing_evidence_rule_count=0`，`rules verify` 与 `doctor` 保持 `ok=true` 且 stale 计数为 `0`，因此 P2-2 已完成闭环。

---

## 6. 整改建议

### 6.0 2026-06-18 状态说明

本节原本是 2026-06-17 的整改建议清单。  
截至 2026-06-18：

- `6.1` 与 `6.2` 中列出的 P0 / P1 / P2-4 事项均已闭环并拿到最新验证证据。
- 当前剩余整改重点不再包含 P2-2；后续规则侧工作转为内蒙古 / 陕西 / 宁夏 3 省 truth 与 evidence 首次建档。

### 6.1 72 小时内必须处理

1. 修复 `PaymentService.handle_webhook()`，禁止把 `refunded` / 其他终态 payment 回写为 `paid`。  
   状态：已完成并回归通过。
2. 为生产环境增加 payment provider fail-closed 校验，禁止 `prod + mock/alipay_sim` 启动。  
   状态：已完成并回归通过。
3. 修复 `backup_snapshot.sh` 对 WAL 管理库的快照方式，至少做 checkpoint 或复制 `-wal/-shm`。  
   状态：已完成并回归通过。
4. 在 `audit_plan()` 中真正落地 `max_volunteers` 等省规则，补一条失败用例。  
   状态：已完成并回归通过。
5. 修正文档口径，把当前正式定位统一为“运营增强系统”，直到 Web 自助链路真正确认闭环。  
   状态：已完成并回归通过。

### 6.2 1 周内应完成

1. 为 `payments` 增加单活跃支付约束或等价保护。  
   状态：已完成并回归通过。
2. 调整 `delivery_notifications` 唯一键为 `(order_id, event_type, channel)`，并补冲突告警。  
   状态：已完成并回归通过。
3. 扩展备份范围，覆盖 `portal_upload_dir` 与订单实际引用的交付物。  
   状态：已完成并回归通过。
4. 修正 `backup_restore_smoke.py`，禁止用伪造生产配置制造假阳性。  
   状态：已完成并回归通过。
5. 修复 `dev-verify.sh --skip-install` 契约，并恢复真正有效的一键验证。  
   状态：已完成并回归通过。

### 6.3 下一个版本前

1. 补齐内蒙古 / 陕西 / 宁夏 3 省 truth yaml 与首批官方 evidence 后完成逐省人工复核。
2. 统一 PRD / ROADMAP / MARKET_RESEARCH / README / CURRENT_STATE 口径。
3. 明确对外承诺边界：
   - 可以说什么
   - 不能说什么
   - 哪些只是本地 MVP
4. 补齐正式合规材料与前台同意留痕设计。
5. 重新梳理“完整 Web 自助 SaaS”的最小上线门槛，避免继续漂移。

---

## 7. 最终结论

这个项目已经不是“没有体系”的脚本集合，而是一个有明显运营后台能力、支付/通知/备份/审计等雏形的系统。  
但也正因为已经进入系统阶段，当前最需要解决的不是再堆新能力，而是把以下少数未闭环项做成可信闭环：

1. **产品口径统一**
2. **支付状态一致性**
3. **灾备链路真实性**
4. **规则审计名实一致**

2026-06-18 复核后，1-3 已闭环；第 4 项中规则审计主链路也已闭环，剩余的是 P2-2 的其它 `3` 省真实 evidence 补摘录。  
在这最后一项没有收口之前，本项目适合作为**人工服务运营增强系统**继续演进，不适合作为**完整 Web 自助商业产品**对外验收。
