# CURRENT_STATE

最后更新: 2026-06-15
状态词: 本地验证完成（v2.1 已交付增强 + T12 本地修复闭环已收口）
真相源优先级:

1. 本文件
2. docs/FINAL_COMPLETION_REPORT_2026-06-13.md
3. docs/P0_P1_P2_REMEDIATION_PLAN_2026-06-14.md（当前整改板；2026-06-15 已做状态归一）
4. docs/ACTIVE_REMEDIATION_2026-06-13.md
5. product/PRD.md / product/ROADMAP.md / docs/IMPLEMENTATION_PLAN_v2.md
6. reports/PRODUCT_PLANNING_TECH_ALIGNMENT_REVIEW_2026-06-13.md（历史评审快照）

---

## 1. 当前准确定位

项目当前准确定位为：

- 已完成: 人工服务运营增强系统（闲鱼 / 微信 / 学校渠道）
- 已完成: 管理后台、订单、分享、渠道同步、AI 审核、CI/CD、性能与安全加固
- 未完成: 用户端 Web 自助支付 / 资料填写 / 站内交付的完整商业闭环（T12 进行中）
- 已完成且已本地验证: `mock` / `alipay_sim` / `alipay` 三层支付代码链与 notify/return 路由；退款状态闭环、portal token secret 分离、payment webhook fail-closed、删除/匿名化扩围、分享 allowlist、channel_sync DB 隔离与 DAO 真相收敛
- 未完成且仍阻塞线上验收: 真实支付宝商户凭据、公网 notify_url、备案域名、真实支付 acceptance

一句话：

> 当前版本已经完成 v2.1 的后台运营链路与 AI 审核增强闭环，但不是完整 Web 自助 SaaS。

---

## 2. 已完成模块

- T1 AI审核服务
- T2 反扎堆检测
- T3 数据溯源
- T4 订单管理
- T5 集成测试与发布
- T6 管理后台
- T7 分享功能
- T8 渠道集成
- T9 错误处理
- T10 CI/CD
- T11 性能与安全

覆盖率门槛证据：
覆盖率门槛证据：

- overall = 92.46%
- core = 100.00%
- 满足：整体≥80%、核心≥100%

最新覆盖率口径已统一：

- 单一真相源：`scripts/check_coverage_gate.py`
- CI / dev-verify / codecov 全部指向同一阈值

三仓同步状态：

- gitea/main 已同步
- origin/main 已同步
- tksea/main 已同步
- tag v2.1 已推送

---

## 3. 尚未完成 / 不应误报为已完成

### T12 用户端 Web 自助 MVP

当前仅能说：

- 已启动 / 实施中
- 还不能说“已完成”

未完成主链路包括：

- 真实支付接入与回调验签的线上 acceptance
- `info_submitted -> serving` 自动处理主链 +本地自动桥接 `info_submitted -> serving` 已落地；仍缺真实 worker/生成服务/线上调度收口
- 站内通知发送器、真实邮件通知发送器与调度已落地；仍缺生产告警链与独立通知审计页
- 前台删除工单流程与更完整的产品化交互

因此：

- Web 自助购买场景 = **本地 MVP 主链已大部分落地，但线上闭环未完成**
- 完整教育 SaaS 化 = 未完成

---

## 4. 已修正的历史评审问题

以下问题在 2026-06-13 之后已被修正，不应继续按“当前未解决”表述：

1. PRD P2 / P3 功能编号冲突
2. ROADMAP 中已落地功能仍保持未勾选
3. TECH_ARCHITECTURE 仍标“设计中”
4. FINAL_COMPLETION_REPORT 仍写“条件完成”
5. 依赖清单未显式声明 Jinja2 / WeasyPrint / cairocffi / ruff / mypy
6. GitHub origin 凭据导致发布链阻塞

这些应被视为：

- 已修正的历史问题
- 不应再作为当前阻塞项重复引用

---

## 5. 仍然有效的评审问题

以下问题仍成立，应继续作为后续版本约束：

### P0 / P1 真实缺口

- 用户端 Web 自助支付闭环缺失
- 生产通知链已有底层 validated/delivered 状态机、portal 通知审计页、后台独立通知审计页、运维告警审计页与 watchdog alert sink；仍缺真实 SMTP/IM 接入后的生产级监控联调
- 前台入口已支持基础资料填写、附件上传与 5 步向导（基础信息 / 偏好与目标 / 已有方案与附件 / 协议确认 / 提交确认）；已支持最多 5 个附件，但仍缺更细粒度字段校验与更完整文件类型策略
- 业务数据备份 / 恢复 / 密钥托管已有本地基线与验证，但异机备份和生产接入仍不足
- 隐私政策 / 服务协议 / 监护人同意 / 数据保留与删除流程仍缺前台/客服自助工单与正式法务版本

> 重要更新（2026-06-15）：
> 上述 5 项是 v2.1 当前阶段以外的真实缺口。
> 上一轮 2026-06-14 严格复审里的 P1 整改项已全部完成：
>
> - P1-1 支付回调双写裂缝已修复
> - P1-5 退款域模型闭环已修复
> - P1-2 删除/匿名化已覆盖 orders 主表 + payments.callback_payload + order_intakes.payload_json
> - P1-7 验证链口径统一（CI / dev-verify / codecov / gate script 同一阈值）

### P2 工程改进

- crowd_db 高置信数据应区分湖南与其他省份
- 架构图仍需进一步拆分 Current / Target 视觉表达
- legacy 邮件脚本应继续弱化为非主链能力

### 仍然有效的 P1 / P2 整改项

完整清单见 `docs/P0_P1_P2_REMEDIATION_PLAN_2026-06-14.md`：

- P2-1 公共下单孤儿订单
- P2-3 delivery `sent` 语义修正
- P1-3 真实支付回调校验
- P1-4 webhook DB 连接污染
- P1-6 分享 allowlist
- P1-8 备份恢复演练
- P2-4 portal token / JWT secret 分离（已通过 P2-4 单元测试 + prod fail-closed）
- P2-5 payment webhook secret fail-closed（已通过 P2-5 单元测试 + prod fail-closed）

已完成并不再列为整改项：

- P2-2 channel_sync 单一 DAO 真相
- P2-6 历史快照头注补齐
- X-02 支付域设计
- X-03 Delivery 交付服务设计
- X-04 合规基线文档
- X-05 备份恢复与密钥托管方案
- X-06 本地一键验证脚本
- X-08 crowd_db 数据完整度等级化

---

## 6. 对外表述边界

允许对外说：

- 已具备人工服务运营后台能力
- 已具备 AI 审核、反扎堆、数据溯源、分享、渠道同步能力
- 已完成 v2.1 当前计划闭环

不应对外说：

- 已完成完整 Web 自助 SaaS
- 已完成系统内支付闭环
- 已完成用户端完整交付闭环
- 27 省 crowd_db 均为高置信强推荐数据

---

## 7. 推荐阅读顺序

1. docs/CURRENT_STATE.md
2. docs/FINAL_COMPLETION_REPORT_2026-06-13.md
3. product/PRD.md
4. product/ROADMAP.md
5. docs/IMPLEMENTATION_PLAN_v2.md
6. reports/PRODUCT_PLANNING_TECH_ALIGNMENT_REVIEW_2026-06-13.md（作为历史评审参考）
