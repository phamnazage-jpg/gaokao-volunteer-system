# CURRENT_STATE

最后更新: 2026-06-15
状态词: 本地验证完成（v2.1 已交付增强 + T12 本地修复闭环已收口，待 commit/push）
真相源优先级:

1. 本文件
2. docs/FINAL_COMPLETION_REPORT_2026-06-13.md
3. docs/ACTIVE_REMEDIATION_2026-06-13.md
4. product/PRD.md / product/ROADMAP.md / docs/IMPLEMENTATION_PLAN_v2.md
5. reports/PRODUCT_PLANNING_TECH_ALIGNMENT_REVIEW_2026-06-13.md（历史评审快照）

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

- overall = 60.53%
- core = 82.54%
- 满足：整体≥60%、核心≥80%

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
- 生产告警链与独立通知审计页仍未形成当前主系统标准能力（站内通知 + 邮件通知发送器已落地）
- 上传入口仍以后台 / CLI / 内部入口为主，用户前台入口不足
- 业务数据备份 / 恢复 / 密钥托管已有本地基线与验证，但异机备份和生产接入仍不足
- 隐私政策 / 服务协议 / 监护人同意 / 数据保留与删除流程仍缺前台/客服自助工单与正式法务版本

### P2 工程改进

- crowd_db 高置信数据应区分湖南与其他省份
- 架构图仍需进一步拆分 Current / Target 视觉表达
- legacy 邮件脚本应继续弱化为非主链能力

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
