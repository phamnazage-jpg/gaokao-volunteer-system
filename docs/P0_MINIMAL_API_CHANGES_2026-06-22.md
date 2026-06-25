# P0_MINIMAL_API_CHANGES_2026-06-22

最后更新: 2026-06-22
状态词: P0 最小接口变更清单
真相源:
- `product/PRD_UPGRADE_2026-06-21.md`
- `docs/UPGRADE_EXECUTION_BOARD_2026-06-22.md`
- `docs/P0_EXECUTION_TASK_BREAKDOWN_2026-06-22.md`

> 本文只定义 P0 为了成立“审核优先主线”所需的最小接口与数据承接变更；不提前展开 P1 / P2。

---

## 1. 当前可复用接口盘点

当前已存在的关键接口 / 页面：

### 1.1 公开下单链

- `POST /api/public/orders`
- 返回：
  - `order_id`
  - `checkout_url`
  - `portal_status_url`
  - `portal_info_url`

当前作用：

- 创建订单
- 进入支付
- 进入 Portal 资料页 / 状态页

### 1.2 Portal 资料链

- `GET /portal/{token}/info`
- `POST /portal/{token}/info`
- `POST /portal/{token}/attachments`

当前作用：

- 四步资料向导
- 保存草稿 / 正式提交
- 上传已有方案附件

### 1.3 Portal 状态链

- `GET /portal/{token}/status`
- `GET /portal/{token}/report`
- `GET /portal/{token}/report.pdf`

当前作用：

- 看订单阶段
- 看报告 / PDF

### 1.4 当前主要限制

1. `POST /portal/{token}/info` 当前绑定 `IntakePayload`
2. `IntakePayload(mode=submit)` 当前要求至少一个偏好字段存在
3. 现有 `stage` 面向支付 / 补资料 / 交付，不面向审核结果分流
4. 现有接口无 `profile_minimum_complete` / `review_entry_source` / `review_followup_action` 语义

---

## 2. P0 最小接口策略

结论：

- **优先复用现有 Portal 链路**
- **最小新增页面域状态与轻量返回字段**
- **避免在 P0 修改订单六态状态机**

也就是：

1. 不新建整套用户系统接口
2. 先复用：
   - `/portal/{token}/info`
   - `/portal/{token}/attachments`
   - `/portal/{token}/status`
3. 必要时新增轻量接口或返回字段，承接：
   - 审核输入
   - Step 1 最小建档
   - 审核结果分流

---

## 3. P0 必改接口项

## 3.1 调整 `IntakePayload` 提交校验

### 当前问题

`data/orders/intake_schema.py` 当前在 `mode=submit` 时要求：

- `candidate_score`
- `candidate_rank`
- `candidate_subjects`
- 协议字段
- `candidate_interests`
- `target_cities`
- `target_majors`
- `university_preferences`

以上字段当前已不再作为 `mode=submit` 的阻塞校验；P0 Step 1 最小提交仅要求省份 / 分数 / 位次 / 选科 + consent。

### P0 目标

P0 提交只要求：

- `candidate_province`
- `candidate_subjects`
- `candidate_score`
- `candidate_rank`
- 协议字段

### 变更建议

把 `IntakePayload(mode=submit)` 的“至少一个偏好字段”校验下放到 P1 语义，不再阻塞 P0。

### 影响

- Step 1 可独立提交
- 审核入口不再被偏好字段卡死

---

## 3.2 把 `candidate_province` 纳入 Portal info 提交链

### 当前问题

当前 Portal info 表单主提交字段中：

- 有 `candidate_score`
- 有 `candidate_rank`
- 有 `candidate_subjects`
- **没有 Step 1 主视图里的 `candidate_province`**

而 PRD 已明确 Step 1 四字段必须包含省份。

### 变更建议

1. 给 `IntakePayload` 增加 `candidate_province`
2. 给 `/portal/{token}/info` 前端表单补 `candidate_province`
3. 在 `submit_order_info()` 中把 `candidate_province` 写回：
   - `order_intakes.payload_json`
   - 必要时冗余回 `orders.candidate_province`

### 影响

- Step 1 四字段闭环成立
- 审核最小约束与档案最小建档一致

---

## 3.3 为 `/portal/{token}/info` 响应补最小建档状态

### 当前返回

`PortalIntakeResponse` 目前只有：

- `intake_status`
- `stage`
- `order_id`

### P0 缺口

P0 需要知道：

- Step 1 是否完成
- 页面提交后是否可回到审核链路

### 变更建议

给 `PortalIntakeResponse` 增加：

- `profile_minimum_complete: bool`

可选增加：

- `profile_missing_fields: string[]`

### 计算规则

当以下字段齐全时：

- `candidate_province`
- `candidate_subjects`
- `candidate_score`
- `candidate_rank`

则 `profile_minimum_complete = true`

---

## 3.4 新增或补充首页 / 状态页聚合返回字段

### 当前问题

首页目标态要求显示：

- 当前阶段
- 是否有最近审核结果
- 是否可看报告
- Step 1 是否完成

现有公开链路没有专门的工作台聚合结构。

### P0 建议

二选一：

#### 方案 A：新增轻量聚合接口

建议新增：

- `GET /portal/{token}/workspace-summary`

最小返回：

- `stage`
- `profile_minimum_complete`
- `has_recent_review_result`
- `has_report`
- `primary_action`

#### 方案 B：复用 `_build_portal_context()` 输出

如果暂不新开接口，则在现有状态页 / 首页承接层统一从 `_build_portal_context()` 衍生：

- `profile_minimum_complete`
- `has_report`
- `primary_action`

### 推荐

- P0 推荐 **方案 B 先落**
- 等首页工作台稳定后再决定是否抽独立聚合接口

---

## 3.5 定义审核输入最小承接结构

### 当前可复用资产

现有已存在：

- `existing_plan_summary`
- attachments 上传

### P0 目标

审核最小输入统一为：

- `existing_plan_summary`
- `attachments[]`
- `candidate_province`
- `candidate_subjects`
- `candidate_score`
- `candidate_rank`

### 变更建议

不急着在 P0 新建复杂审核对象表；先定义轻量审核输入契约，供页面和后端处理链共用。

建议文档化结构：

- `review_input_summary`
- `review_input_attachments`
- `review_constraints`

如果后端要临时落地，可先存在：

- `order_intakes.payload_json`
- 或单独轻量 JSON artifact

---

## 3.6 定义审核结果最小返回结构

### 当前问题

现有 Portal 链路没有“审核结果分流”的最小对象。

### P0 最小返回建议

新增轻量审核结果返回结构：

- `review_result_id`
- `risk_level`
- `top_findings[]`
- `recommended_action`
- `available_actions[]`

其中：

- `recommended_action ∈ {go_cwb, go_step1, go_full_plan}`
- `available_actions[]` 至少含三类入口

### 注意

P0 可以先把它定义成页面域结构，不强制先做完整持久化模型。

---

## 3.7 定义审核分流记录字段

### 当前缺口

现有代码中尚未实现：

- `review_entry_source`
- `review_followup_action`

### P0 建议

最小先定义语义，不必一开始改重 schema：

- `review_entry_source ∈ {home, status, report, direct}`
- `review_followup_action ∈ {cwb, step1, full_plan, none}`

### 落地方式建议

P0 可先落在：

- 页面埋点事件
- 轻量 metadata 字段
- 或会话态 / 结果对象中

只要保证：

- 来源可追踪
- 分流动作可统计

---

## 4. P0 不建议现在改的接口项

以下内容不要提前混入 P0：

1. Step 2-4 全量偏好字段接口
2. 政策中心完整 API
3. 同分段参考完整 API
4. 完整报告资产列表 API
5. 多版本方案管理 API
6. 订单六态状态机扩容

原因：

- 这些都属于 P1 / P2
- 先改只会扩大范围

---

## 5. 最小接口变更表

| 变更项 | 类型 | 当前状态 | P0 动作 | 必须性 |
| --- | --- | --- | --- | --- |
| `IntakePayload` 去掉偏好字段提交门槛 | 校验逻辑 | 与 P0 冲突 | 修改 | 必须 |
| `IntakePayload` 增 `candidate_province` | 请求字段 | 缺失 | 新增 | 必须 |
| `/portal/{token}/info` 表单补省份 | 页面 + 提交 | 缺失 | 修改 | 必须 |
| `/portal/{token}/info` 响应补 `profile_minimum_complete` | 响应字段 | 缺失 | 新增 | 建议 |
| 统一审核最小输入结构 | 契约定义 | 未定义 | 新增 | 必须 |
| 定义审核结果最小返回结构 | 契约定义 | 未定义 | 新增 | 必须 |
| 定义 `review_entry_source` | 状态 / 埋点语义 | 未定义 | 新增 | 必须 |
| 定义 `review_followup_action` | 状态 / 埋点语义 | 未定义 | 新增 | 必须 |
| 首页工作台聚合接口 | 新接口 | 无 | 可延后 / 先复用 | 可选 |

---

## 6. 推荐实现顺序

1. 先修改 `IntakePayload`，解除 P0 与当前提交校验冲突
2. 把 `candidate_province` 接入 `/portal/{token}/info`
3. 定义 `profile_minimum_complete`
4. 定义审核输入 / 审核结果最小契约
5. 定义分流动作与来源字段
6. 最后再决定是否补首页工作台聚合接口

---

## 7. 下一步建议

1. 基于本文继续落《报告版本与档案版本关系说明》
2. 确认 `review_result` 是页面态还是轻量持久化对象
3. 确认 `profile_minimum_complete` 是纯派生字段还是落库存字段
