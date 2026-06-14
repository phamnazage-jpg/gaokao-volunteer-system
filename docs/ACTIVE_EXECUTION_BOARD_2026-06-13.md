# ACTIVE_EXECUTION_BOARD

最后更新: 2026-06-13
状态词: 当前有效问题执行板
真相源: `docs/CURRENT_STATE.md`
问题来源: `docs/ACTIVE_REMEDIATION_2026-06-13.md`

---

## 1. 当前门禁结论

结论: v2.1 已完成；后续工作只围绕“仍然有效问题”推进。

禁止事项:

- 不再重复处理已修复的历史问题
- 不把 T12 之外的 Web 自助能力混入已完成的 v2.1 结论
- 不把“设计占位”误报为“已实现”
- 不把 Git/文档修订当成支付/交付/合规能力的替代

---

## 2. 最短闭环主线

推荐执行顺序:

1. X-01 T12 Web 自助 MVP 立项板
2. X-02 支付域设计
3. X-03 Delivery 交付服务设计
4. X-04 合规基线文档
5. X-05 备份恢复方案
6. X-06 本地一键验证脚本
7. X-08 crowd_db 数据完整度等级化
8. X-07 历史快照头注补齐

说明:

- X-01/X-02/X-03 决定“用户端 Web 自助闭环”是否能成立，是最核心主线
- X-04/X-05 是投产合规与可靠性底线
- X-06/X-07/X-08 是工程真相与质量增强项

---

## 3. 执行任务清单

### X-01 建立 T12 唯一实施板

Owner: planner / PM
优先级: P0
状态: completed

目标:

- 为 T12 Web 自助闭环建立唯一实施板，避免后续继续在旧报告里分散描述

交付物:

- `docs/plans/T12-web-self-service-mvp.md`
- `docs/T12_ACCEPTANCE_CRITERIA.md`

完成标准:

- 明确前台主链路：落地页 → 套餐页 → 支付 → 资料填写 → 状态页 → 交付页
- 明确非目标：不在 T12 内扩展新推荐算法/社区/高级会员体系
- 明确验收标准与依赖关系

验证方法:

- 读文档时能一眼看出 T12 的边界、DoD、阶段划分

依赖:

- 无

---

### X-02 支付域设计

Owner: tech-lead / engineer
优先级: P0
状态: completed

目标:

- 建立支付、退款、对账、回调验签的统一领域模型

交付物:

- `docs/PAYMENT_DOMAIN_DESIGN.md`
- `docs/plans/T12-payment-implementation.md`

完成标准:

- 定义 payment_order / payment_attempt / refund / reconciliation_job
- 定义支付状态机与退款状态机
- 定义回调验签、幂等、金额校验、补偿策略
- 明确最小 provider（只选一个先做 MVP）

验证方法:

- 文档能回答：支付成功但报告生成失败怎么办？
- 文档能回答：重复回调如何去重？

依赖:

- X-01

---

### X-03 Delivery 交付服务设计

Owner: tech-lead / engineer
优先级: P0
状态: completed

目标:

- 建立用户支付后的交付链路，不再把“报告生成”误当成“已交付”

交付物:

- `docs/DELIVERY_SERVICE_DESIGN.md`

完成标准:

- 定义 delivery_job / delivery_attempt / delivery_status
- 明确至少一种 MVP 交付方式（站内下载或邮件）
- 定义失败重试、幂等、告警、用户可见状态

验证方法:

- 文档能回答：交付失败如何重试？如何让用户看到状态？

依赖:

- X-01
- X-02

---

### X-04 合规基线文档

Owner: PM / legal / ops
优先级: P1
状态: completed

目标:

- 补齐隐私政策、服务协议、监护人同意、数据保留与删除规则

交付物:

- `docs/LEGAL_PRIVACY_BASELINE.md`
- `docs/PRIVACY_POLICY_DRAFT.md`
- `docs/DATA_RETENTION_AND_DELETION.md`

完成标准:

- 明确收集哪些数据、为什么收集、保留多久、如何删除
- 明确未成年人/监护人授权说明
- 明确同意记录最小字段

验证方法:

- 可回答：用户要求删除报告和订单数据时怎么办？

依赖:

- 无

---

### X-05 备份恢复与密钥托管方案

Owner: ops
优先级: P1
状态: completed

目标:

- 给 SQLite、报告文件、上传文件、加密密钥建立最小可恢复方案

交付物:

- `docs/BACKUP_AND_RECOVERY_PLAN.md`
- `docs/KEY_MANAGEMENT_BASELINE.md`
- 可选：`scripts/backup_verify.sh`

完成标准:

- 定义 RPO / RTO
- 定义数据库、文件、密钥分别如何备份
- 定义恢复演练步骤
- 定义密钥轮换与应急恢复策略

验证方法:

- 文档能指导在临时目录恢复一份可读系统数据

依赖:

- 无

---

### X-06 本地一键验证脚本

Owner: engineer / ops
优先级: P1
状态: completed

目标:

- 固化本地开发验证入口，避免“当前机器可跑、下台机器不可跑”

交付物:

- `scripts/dev-verify.sh`
- README 中的统一开发验证说明

完成标准:

- 能自动执行依赖检查 / pytest / ruff / mypy / 覆盖率门禁
- 明确 venv 初始化和 requirements 安装方式

验证方法:

- 在干净 shell 中执行脚本，能给出明确 pass/fail

依赖:

- X-02 之后可扩展，但可先独立完成基础版

---

### X-07 历史快照头注补齐

Owner: docs / PM
优先级: P2
状态: completed

目标:

- 防止后续 agent 再把历史报告当当前阻塞

交付物:

- 补丁更新以下文档头部说明：
  - `docs/AUDIT_REPORT_2026-06-11.md`
  - `docs/REMEDIATION_TASK_BOARD_2026-06-11.md`
  - `reports/PROJECT_SYSTEM_REVIEW_2026-06-13.md`

完成标准:

- 顶部有“历史快照”说明
- 指向 `docs/CURRENT_STATE.md`
- 指明哪些结论仅代表当时快照

验证方法:

- 搜索“历史快照”能覆盖上述文档

依赖:

- 无

---

### X-08 crowd_db 数据完整度等级化

Owner: data / engineer
优先级: P1
状态: completed

目标:

- 区分“27省结构覆盖”与“高置信推荐覆盖”，避免对外误导

交付物:

- `docs/CROWD_DB_DATA_QUALITY.md`
- crowd_db schema / 输出文案修订（后续代码任务）

完成标准:

- 定义 data completeness level / confidence band
- 明确哪些省份可输出强结论，哪些只能输出弱提示
- 明确对报告文案的影响

验证方法:

- 任意一份报告都能看出该省份数据置信度等级

依赖:

- 无

---

## 4. 当前仍然禁止的错误完成表述

禁止:

- “已完成完整 Web 自助 SaaS”
- “支付闭环已完成”
- “交付系统已完成”
- “27省高质量推荐数据已完成”

允许:

- “v2.1 人工服务运营增强系统已完成”
- “T12 Web 自助闭环仍在实施中”
- “支付/交付/合规/备份恢复仍是当前有效问题”

---

## 5. 当前推荐读取顺序

1. `docs/CURRENT_STATE.md`
2. `docs/ACTIVE_REMEDIATION_2026-06-13.md`
3. 本文件 `docs/ACTIVE_EXECUTION_BOARD_2026-06-13.md`
4. `product/PRD.md`
5. `product/ROADMAP.md`

---

## 6. 下一步执行建议

最优先:

- 先做 X-01 / X-02 / X-03

原因:

- 这是唯一能把“人工服务运营系统”继续推进为“用户端 Web 自助闭环产品”的主线
- 其余问题虽然重要，但不应抢在主闭环前面
