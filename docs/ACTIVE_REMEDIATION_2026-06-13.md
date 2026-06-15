# ACTIVE_REMEDIATION

最后更新: 2026-06-15
状态词: 当前仍然有效的问题清单（仅保留未解决项）
真相源: `docs/CURRENT_STATE.md`
来源基线:

- `reports/PRODUCT_PLANNING_TECH_ALIGNMENT_REVIEW_2026-06-13.md`
- 本轮复核与代码/文档真相校准结果

---

## 0. 使用规则（防止虚假完成和漂移）

本清单只保留“当前仍然有效”的问题。
以下类型不得再重复列为当前阻塞：

1. 已在代码中落地且已推送三仓的问题
2. 只属于历史评审快照、但已在后续修复的问题
3. 尚未进入当前版本范围、且已明确标注为后续版本（例如 T12 Web 自助 MVP）的能力缺口

判断规则：

- 已落地 = 代码/配置/脚本/测试/文档已存在并已验证
- 已收尾 = 工作区干净 + main 已同步三仓
- 后续范围 = `CURRENT_STATE.md` 已明确声明“不属于 v2.1 当前完成范围”

---

## 1. 当前仍然有效的问题（只保留未解决项）

### A. 版本范围内已知但未完成的产品/合规缺口

#### A-1 用户端 Web 自助闭环未完成

严重度: P0（面向 Web 自助产品时）
当前状态: 部分解决，仍未整体收口
范围归属: T12（后续阶段）

已完成：

- 前台公开入口 `/` / `/pricing` / `/checkout/{service_version}`
- 公开下单与 portal token 链路
- 支付后资料填写草稿/提交
- 站内状态页 / 报告查看 / PDF 下载最小闭环
- 后台订单列表/详情可见资料提交状态

仍缺：

- 前台套餐页更完整交互与产品化打磨
- 真实支付接入与回调验签的线上 acceptance
- `info_submitted -> serving` 自动处理主链
- 完整站内通知/交付产品化
- 自助购买后自动处理主链路的生产化闭环

说明：

- 当前不是“完全没做 T12”，而是“本地 MVP 主链大部分已落地，但整体仍未到线上可验收完成”。
- 正确表述应为：`v2.1 完成了人工服务运营闭环，T12 已形成本地 MVP 主链，但线上商业闭环仍未完成`。

建议动作：

- 以 T12 为唯一主线推进，不在旧报告中分散描述
- 后续优先收 `自动处理主链` 与 `真实支付 acceptance`

#### A-2 支付、退款、对账闭环未完成

严重度: P0
当前状态: 部分解决，仍受外部前置阻塞
范围归属: T12 / 后续商业化主线

已完成：

- 支付单模型与 `mock` / `alipay_sim` / `alipay` provider 抽象
- `POST /api/public/payments/alipay/notify`
- `GET /portal/payment-return`
- 本地 RSA2 签名校验 / 金额校验 / 幂等防重
- refund 占位接口与 portal `refund_pending` 状态

仍缺：

- 真实商户主体 / 产品签约 / app_id
- 私钥与支付宝公钥在真实环境装载
- 备案域名与公网 `notify_url`
- 沙箱/生产真实支付 acceptance
- 对账任务与退款回写/异常补偿产品化

说明：

- 当前剩余问题不再是“支付域没建起来”，而是“真实 provider 线上验收与商业化配套未完成”。

建议动作：

- 保持 `docs/PAYMENT_PROVIDER_ONBOARDING.md` 为真实接入 runbook
- 在具备真实商户与域名后执行沙箱/生产 acceptance

#### A-3 自动交付主链未形成完整产品级服务

严重度: P1
当前状态: 部分解决
范围归属: T12 / delivery service 后续主线

已完成：

- `delivery_notifications` 事件表
- `report_ready` 事件自动落库
- `status / attempt_count / last_attempt_at / failure_reason` 追踪字段
- 站内查看 + PDF 下载最小交付闭环
- `DeliveryDispatcher` + `scripts/gaokao-delivery-dispatch.py`
- `ready -> sent` / 缺文件 `-> failed` 的最小执行链
- 站内通知发送器：dispatch 时真实生成 `station_notice` 内容，并在 portal 状态页向用户展示“通知已发送”
- 真实邮件通知发送器：`SMTPDeliverySender` + `customer_email` 采集链 + `email` 通道 dispatch（本地 stub SMTP 已验证）
- dispatcher/watchdog runbook + systemd/cron 样例（`docs/DELIVERY_RETENTION_OPS_RUNBOOK.md` / `deploy/systemd` / `deploy/cron`）

仍缺：

- 自动重试调度 / 生产告警链（watchdog/systemd/cron 样例已补，生产安装未完成）
- 面向用户的独立通知审计页
- 对账/退款与交付失败补偿联动

说明：

- 当前已不再是“报告生成=无交付状态”，但仍未达到完整 delivery service 产品级能力。

建议动作：

- 先把站内通知或邮件发送器做成唯一 MVP 主通道
- 再补失败重试与告警

#### A-4 合规基线已建立，但正式法务审定与执行工具仍未完结

严重度: P1
当前状态: 部分解决
范围归属: 产品/合规主线

已完成：

- `docs/LEGAL_PRIVACY_BASELINE.md`
- `docs/PRIVACY_POLICY_DRAFT.md`
- `docs/DATA_RETENTION_AND_DELETION.md`
- 服务条款草案、删除执行 SOP
- 前台资料提交同意字段落库
- 后台 `DELETE /api/orders/{id}?mode=delete|anonymize&reason=...` 最小执行入口
- 删除时自动清理报告 HTML/PDF，并写入 `order_deletion_audits`

仍缺：

- 正式法务审定版本
- 前台/客服删除工单流程
- 目标生产主机上的自动清理实际安装/留痕（仓库已提供 runbook + systemd/cron 样例）
- 合规文本上线前最终校对

说明：

- 当前不再是“完全没有合规基线”，而是“文档基线 + 后台最小执行入口 + retention cleanup 脚本与调度样例已建，前台流程与生产安装留痕仍待完成”。

#### A-5 业务数据备份/恢复/密钥托管已形成基线，但生产化仍未完结

严重度: P1
当前状态: 部分解决
范围归属: 运维/可靠性主线

已完成：

- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `docs/KEY_MANAGEMENT_BASELINE.md`
- `docs/plans/P1-8-backup-restore-drill.md`
- `scripts/backup_snapshot.sh` 最小目录快照入口
- `scripts/backup_verify.sh` 本地恢复校验入口
- `scripts/backup_restore_smoke.py` 恢复副本最小服务 smoke
- `ops/cron/gaokao-backup.crontab.example`
- `ops/systemd/gaokao-backup*.service|timer` 定时接入口径示例

仍缺：

- 异机/异地备份落地
- 目标主机上的 cron/systemd 实际安装、日志与告警验收
- 密钥轮换的真实执行记录

说明：

- 当前不再是“只有文档没有验证”，而是“已有本地快照、完整性校验、restore smoke 和定时接入口径样例，但生产化运维链未闭环”。

---

### B. 已完成范围内仍需继续增强的真实质量问题

#### B-1 crowd_db 27 省“结构覆盖”不等于“高质量覆盖”

严重度: P1
当前状态: 部分解决

事实：

- 27 省 JSON 文件已存在
- `risk_report` 已输出 `quality_level / quality_label`
- `gaokao-data-trace` human 输出已展示质量等级
- 低置信省份仍主要是“结构覆盖已完成，但推荐质量待增强”

风险：

- 若对外统一宣传“27省高质量反扎堆推荐”，仍有误导风险

建议动作：

- 在 README / 产品文案中继续避免“27省高质量推荐全覆盖”表述
- `data.crowd_db.quality_summary` 已补 province-level summary，后续可接产品文案/页面
- 继续提升非湖南省份高置信数据密度

#### B-2 本地验证环境已基本统一，仍待生产 runner 长期观察

严重度: P1
当前状态: 已解决（本地/CI 统一脚本门禁已落地）

已解决：

- requirements-admin / requirements-dev 已修正
- `scripts/dev-verify.sh` 已成为本地统一入口
- `.github/workflows/ci.yml` 已统一走 `scripts/dev-verify.sh`
- `scripts/check_coverage_gate.py` 已纳入 dev-verify，core coverage gate 与本地/CI 对齐

仍缺：

- 生产 runner / Python 3.12 长期观察（当前已通过 skip 兼容 SMTP stdlib 移除）

建议动作：

- 后续若迁移 Python 3.12+，将 SMTP stub 从 stdlib `smtpd/asyncore` 迁移到 `aiosmtpd`

#### B-3 历史评审文档仍可能被误读为当前阻塞

严重度: P2
当前状态: 部分解决

已解决：

- 对齐评审报告已加历史快照说明
- `CURRENT_STATE.md` 已建立

已解决：

- `docs/AUDIT_REPORT_2026-06-11.md` 已标注历史快照
- `docs/REMEDIATION_TASK_BOARD_2026-06-11.md` 已标注历史快照
- `reports/PROJECT_SYSTEM_REVIEW_2026-06-13.md` 已标注历史快照与真相源跳转

仍缺：

- 无

---

## 2. 明确不再重复追踪的问题（已解决）

以下问题已经修复，不应再出现在新的整改清单里：

1. PRD P2/P3 功能编号冲突
2. ROADMAP 中已落地功能仍未勾选
3. TECH_ARCHITECTURE 仍标“设计中”
4. FINAL_COMPLETION_REPORT 仍为“条件完成”
5. requirements 未声明 Jinja2 / WeasyPrint / cairocffi / ruff / mypy
6. CI 的 `--cov-fail-under=80` 与实际门槛冲突
7. GitHub origin 凭据阻塞发布
8. T1~T11 Goal 阻塞链问题

这些问题如果未来再次出现，应视为新回归，而不是沿用旧问题编号。

---

## 3. 推荐的单一后续主线

为了避免继续漂移，建议把后续工作只收敛到 3 条主线：

### 主线 1：T12 Web 自助 MVP

目标：补齐“用户端自助下单/支付/资料填写/站内交付”闭环

### 主线 2：合规与数据治理

目标：隐私政策 / 监护人同意 / 备份恢复 / 密钥托管

### 主线 3：数据质量增强

目标：提升非湖南省份的 crowd_db 置信度与可解释性

不建议再做的事：

- 重复写“已完成能力”的审计报告
- 继续把历史快照问题当作当前阻塞
- 在 T12 未闭环前继续泛化更多高级功能

---

## 4. 最小执行板（当前仍值得做）

| ID   | 任务                                       | 优先级 | 是否属于已完成阶段问题 |
| ---- | ------------------------------------------ | ------ | ---------------------- |
| X-01 | 为 T12 建立唯一实施板和验收报告模板        | P0     | 否（后续阶段）         |
| X-02 | 建立支付域设计（订单/支付/退款/回调/对账） | P0     | 否（后续阶段）         |
| X-03 | 建立 delivery service 设计                 | P1     | 否（后续阶段）         |
| X-04 | 新建 LEGAL_PRIVACY_BASELINE 文档           | P1     | 是（当前真实缺口）     |
| X-05 | 新建 BACKUP_AND_RECOVERY_PLAN 文档         | P1     | 是（当前真实缺口）     |
| X-06 | 增加 dev-verify.sh 一键验证脚本            | P1     | 是（当前真实缺口）     |
| X-07 | 为历史报告补统一“历史快照”头注             | P2     | 是（当前真实缺口）     |
| X-08 | 为 crowd_db 增加数据完整度等级与报告文案   | P1     | 是（当前真实缺口）     |

---

## 5. 当前最准确的最终表述

> v2.1 已完成“人工服务运营增强系统”闭环，不应再被旧报告中的已修复问题干扰；当前真正仍有效的问题集中在 T12 Web 自助闭环、支付/交付、合规、备份恢复和多省高置信数据质量这五个方向。
