# LEGAL_PRIVACY_BASELINE

状态: 草案（T12 上线前基线）  
适用范围: `/pricing` → `/checkout` → `/api/public/orders` → `/portal/{token}` 全链路，以及后台订单处理、报告交付、渠道补录场景。  
最后更新: 2026-06-14

---

## 1. 目标

本文件定义 T12 用户端 Web 自助 MVP 在法务/隐私侧的**最小上线基线**，防止以下误判：

- 代码能跑 = 可以直接收真实考生资料
- 有加密字段 = 已完成隐私合规
- 可删除数据库记录 = 已具备正式删除流程

本文件只定义当前必须落实的最低要求，不代替正式律师审阅。

---

## 2. 当前涉及的数据类型

### 2.1 用户主动提交的数据

1. 家长/联系人信息
   - 称呼
   - 手机号
   - 微信号（可选）
2. 考生信息
   - 姓名
   - 省份
   - 分数
   - 位次
   - 选科
   - 兴趣方向
   - 家长备注
3. 订单与交付信息
   - 订单号
   - 套餐版本
   - 支付状态
   - 报告 HTML/PDF 路径
4. 后台处理信息
   - 状态流转历史
   - 处理人
   - 处理原因

### 2.2 敏感级别分层

- S1 高敏: 手机号、身份证号（如未来启用）、支付回调标识、密钥材料
- S2 中敏: 姓名、分数、位次、选科、兴趣、家长备注
- S3 低敏: 订单号、套餐、状态、非个体化统计

---

## 3. 处理目的与边界

允许的处理目的：

1. 生成志愿填报审核/方案服务
2. 联系用户完成资料补充、状态通知、交付提醒
3. 进行售后、退款、争议处理
4. 做最小必要的审计与故障排查

禁止的处理目的：

1. 未经单独同意用于营销推送
2. 出售或共享给无关第三方
3. 用于广告画像或跨场景推荐
4. 在对外案例中展示未脱敏真实资料

---

## 4. 未成年人 / 监护人基线

项目面向高考考生场景，默认视为涉及未成年人或其监护人数据。

最低要求：

1. 前台资料提交前，应展示“监护人已知情并同意提交资料用于志愿填报服务”的确认文案
2. 同意记录至少要保存：
   - `consent_version`
   - `consent_scope`
   - `consent_given_at`
   - `consent_operator`（self/guardian/admin_import）
3. 后台人工补录渠道单时，也必须记录同意来源：
   - 闲鱼/微信/学校/线下确认

当前状态:

- `consent_version / consent_scope / privacy_accepted / service_terms_accepted / guardian_confirmed` 已落在 `order_intakes` payload 提交链路
- `consent_given_at / privacy_accepted_at / service_terms_accepted_at / consent_channel / consent_operator` 现已在 portal 提交链路自动补齐
- 但后台代录 / 外部渠道补录仍需逐步统一到同一审计口径，因此仍不可宣称“监护人同意闭环已整体完成”

---

## 5. 对外文案最低要求

前台至少应明确告知：

1. 收集哪些信息
2. 用于什么目的
3. 不用于营销出售
4. 可申请删除
5. 监护人同意要求
6. 服务结果为辅助决策，不承诺录取结果

建议文案入口：

- 下单页提交前
- 资料填写页提交前
- 页脚“隐私政策 / 数据删除说明”链接

---

## 6. 同意记录最小字段

上线前至少应在订单上下文保存以下字段：

- `consent_version`: 当前协议/隐私政策版本
- `privacy_accepted_at`: 隐私政策同意时间
- `service_terms_accepted_at`: 服务说明同意时间
- `guardian_confirmed`: 是否监护人确认
- `consent_channel`: web / wechat / xianyu / school
  (实现侧 4 个 source；旧版文档曾列 `admin` 渠道值，因未在生产路径写入而移除，6/20 校准)

这些字段可先落在：

- `order_intakes` payload
- 或订单扩展字段 / tags

但不得只停留在前端文案、完全不落库。

---

## 7. 当前代码与本基线的差距

已具备（6/20 增量）：

- 订单敏感字段加密/脱敏基础
- 订单删除 DAO 能力（含 OrdersDAO conn ownership 修复，T12-D）
- Portal token 访问控制基础
- **后台代录 / 外部渠道补录的同意审计统一化**（A-2 6/20 落地：`consent_method` / `consent_operator` / `consent_channel` / `consent_given_at` / `consent_version` 5 字段在 admin/portal 双轨写库；admin `CreateOrderRequest.consent` 必填；`consent_operator` 严格按 `self/guardian/admin_import` 白名单；缺失或非法 consent → HTTP 422）
- **数据删除 SOP 的脚本化/产品化**（T12-D 6/20 落地：`scripts/gaokao-retention-cleanup.py` + systemd unit + cron 样例 + runbook §8 端到端 acceptance 步骤）

尚缺（截至 6/20）：

- 对外正式法务审阅与版本管理（PM/legal 拍板，4 份草案已就绪）
- `consent_version` 升级机制（当前硬编码 `t12-web-mvp-v1`，改版时需 bump）
- `consent_scope` 命名空间统一（portal `web-self-service-order-intake` vs admin `{source}-channel-intake`，建议提升为 Literal）

---

## 8. T12 验收口径

只有同时满足以下条件，才可说“隐私合规基线已补齐”：

- 已有正式文档：隐私政策 + 数据保留删除规则
- 前台存在可见入口
- 同意字段已落库
- 后台/运维知道如何响应删除请求

在此之前，只能说：

- **已建立隐私合规草案基线**
- 不能说“隐私合规已整体完成”
