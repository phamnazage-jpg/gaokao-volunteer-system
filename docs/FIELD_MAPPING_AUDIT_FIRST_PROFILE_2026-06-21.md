# 高考个人档案字段映射表（审核优先版）

> 基于 `product/PRD_UPGRADE_2026-06-21.md` v0.2 与 `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md` v0.2，将现有 Portal / Order / `order_intakes` 字段映射到新的“审核优先档案体系”。

**版本**: v0.2  
**状态**: Draft / 待复审  
**最后更新**: 2026-06-22

---

## 1. 文档目的

本映射表用于回答四个问题：

1. 新档案体系里的字段，当前项目哪些已经有
2. 这些字段现在存在哪一层（Order / `order_intakes.payload_json` / 前端临时态）
3. 哪些字段是 P0 必需，哪些字段延后到 P1 / P2
4. 哪些状态 / 版本语义需要先定义，避免后续实现漂移

本表默认遵守：

> **审核优先**：用户不需要先补齐完整档案才能开始服务；档案字段首先服务于“审核 / 复核”精度提升，其次才服务于完整规划。

---

## 2. 现有数据层概况

### 2.1 当前已存在的 3 层

#### A. Order 主表（`data/orders/models.py` / `dao.py`）

适合存：

- 订单级主字段
- 面向列表 / 状态 / 交付的冗余字段
- 少量需要快速查询的考生核心字段

当前已见核心字段：

- `candidate_province`
- `candidate_score`
- `candidate_rank`
- `candidate_subjects`
- `candidate_interests`
- `candidate_strong_subjects`
- `candidate_weak_subjects`
- `candidate_family`
- `notes`
- `consent_method`
- `consent_given_at`

#### B. `order_intakes.payload_json`（`data/orders/intake_schema.py` / `intake_store.py`）

适合存：

- Portal / 档案提交的结构化 payload
- 审核与规划过程中不断补充的字段
- 同意审计上下文

当前已见字段：

- `candidate_score`
- `candidate_rank`
- `candidate_subjects`
- `candidate_interests`
- `target_cities`
- `target_majors`
- `university_preferences`
- `existing_plan_summary`
- `guardian_notes`
- `consent_version`
- `consent_scope`
- `privacy_accepted`
- `service_terms_accepted`
- `guardian_confirmed`
- 自动补齐：`consent_channel` / `consent_operator` / `consent_given_at` / `privacy_accepted_at` / `service_terms_accepted_at`

#### C. 前端页面临时态

当前前端页面中有展示与交互，但未必已结构化入库的扩展能力，后续新增字段优先从这里切。

---

## 3. 新档案体系目标分层

### Step 1 考生信息（最小必填 / P0）

用于：

- 启动审核
- 启动冲稳保判断
- 启动最小版本报告

字段：

- 高考省份
- 科目组合
- 分数
- 位次

### Step 2 院校偏好（P1）

用于：

- 审核时判断当前院校倾向是否失衡
- 进入完整规划时做院校维度筛选

字段：

- 院校地域偏好
- 院校类型
- 目标院校

### Step 3 专业偏好（P1）

用于：

- 审核当前专业方向是否偏离用户意向
- 完整规划时做专业匹配与排除

字段：

- 专业偏好
- 不接受专业
- 优先策略

### Step 4 其他偏好（P1 / P2）

用于：

- 提升推荐解释性
- 提升后续报告个性化质量

字段：

- 毕业规划
- 学费倾向
- 就业地域偏好
- 家庭背景
- 行业资源
- 补充说明

---

## 4. 字段映射主表

| 新档案字段 | 当前是否存在 | 当前字段名 | 当前存储层 | 建议最终层 | 分期 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| 高考省份 | ✅ | `candidate_province` | Order | Order + Intake | P0 | 最小必填 |
| 科目组合 | ✅ | `candidate_subjects` | Order + Intake | Order + Intake | P0 | 最小必填 |
| 分数 | ✅ | `candidate_score` | Order + Intake | Order + Intake | P0 | 最小必填 |
| 位次 | ✅ | `candidate_rank` | Order + Intake | Order + Intake | P0 | 最小必填 |
| 现有方案摘要 | ✅ | `existing_plan_summary` | Intake | Intake | P0 | 审核主输入字段 |
| 专业兴趣简述 | ✅ | `candidate_interests` | Order + Intake | Intake 为主 | P1 | 当前更像自由文本 |
| 目标院校（列表） | ⚠️ 部分 | 当前未结构化 | - | Intake | P1 | 需要新增 `target_schools` |
| 目标专业（列表） | ✅ | `target_majors` | Intake | Intake | P1 | 已有 |
| 目标城市 / 地域偏好 | ✅ | `target_cities` | Intake | Intake | P1 | 需要升级为更通用地域偏好 |
| 院校偏好说明 | ✅ | `university_preferences` | Intake | Intake | P1 | 现阶段仍可兼容保留 |
| 家庭背景 | ⚠️ 弱存在 | `candidate_family` | Order | Intake（主）+ Order（必要冗余） | P2 | 当前语义不足 |
| 强势学科 | ✅ | `candidate_strong_subjects` | Order | Order / Intake | P2 | 当前 Portal 未系统化采集 |
| 弱势学科 | ✅ | `candidate_weak_subjects` | Order | Order / Intake | P2 | 当前 Portal 未系统化采集 |
| 监护人 / 补充备注 | ✅ | `guardian_notes` | Intake | Intake | P1 | 可并入补充说明层 |
| 同意版本 | ✅ | `consent_version` | Intake | Intake + 必要冗余 | 已有 | 不属于偏好字段，但需持续保留 |
| 同意范围 | ✅ | `consent_scope` | Intake | Intake + 必要冗余 | 已有 | 同上 |
| 隐私同意 | ✅ | `privacy_accepted` | Intake | Intake | 已有 | 同上 |
| 服务条款同意 | ✅ | `service_terms_accepted` | Intake | Intake | 已有 | 同上 |
| 监护人确认 | ✅ | `guardian_confirmed` | Intake | Intake | 已有 | 同上 |

---

## 5. P0 字段边界（先让审核优先主线成立）

### 5.1 P0 只要求以下字段可用

- `candidate_province`
- `candidate_subjects`
- `candidate_score`
- `candidate_rank`
- `existing_plan_summary`（或等价审核输入）

### 5.2 P0 不要求完成的内容

- 不要求 `target_schools` 已落地
- 不要求 Step 2-4 偏好字段全部结构化
- 不要求一次性迁移旧订单数据
- 不要求旧 payload 立即补齐所有新字段

### 5.3 P0 需要先定义的状态 / 元数据语义

- `profile_minimum_complete`：最小建档是否完成
- `review_entry_source`：用户从首页 / 审核页 / 报告页等入口进入审核
- `review_followup_action`：审核后进入了哪条分流动作

这些语义可以先以派生状态或轻量元数据存在，不强制一开始就做重 schema 改造。

---

## 6. P1 / P2 建议新增字段

### 6.1 P1：院校 / 专业偏好层

- `target_schools`
- `school_preference_types`
- `school_region_preferences`
- `disliked_majors`
- `priority_strategy`

### 6.2 P1：其他偏好层（先落高频）

- `graduation_plan`
- `tuition_preference`
- `employment_region_preferences`

### 6.3 P2：深层解释型偏好

- `family_background`
- `industry_resources`
- `extra_notes`

---

## 7. 字段分层建议（避免乱塞到 Order 主表）

### 7.1 应保留在 Order 主表的字段

这些字段适合继续保留或冗余到 Order，便于：

- 状态页
- 列表页
- 快速查询
- 报告摘要

建议保留：

- `candidate_province`
- `candidate_score`
- `candidate_rank`
- `candidate_subjects`
- `candidate_interests`（如继续保留）
- `candidate_strong_subjects`
- `candidate_weak_subjects`
- `candidate_family`（仅作为旧字段兼容）

### 7.2 应以 Intake 为主的字段

这些字段更适合存到 `order_intakes.payload_json`：

- 所有偏好型、可选型、多选型字段
- 所有逐步补充字段
- 审核与规划解释型字段

原因：

- 变化频率高
- 可逐步补全
- 不一定需要主表强查询
- 便于迭代扩展

### 7.3 何时再冗余到 Order

如果后续页面 / 接口高频读取某个字段，且不想每次 decode intake，可把稳定字段冗余回 Order。

优先考虑未来可能冗余的：

- `priority_strategy`
- `graduation_plan`
- `tuition_preference`

前提：

- 先在 Intake 侧稳定语义
- 再决定是否冗余，不要一开始就把所有偏好塞进主表

---

## 8. 状态与版本字段（最小定义）

为与升级 PRD 保持一致，字段层至少要承接以下语义：

- `profile_version`：每次用户保存档案快照时递增
- `review_result_version`：每次审核提交产生一个结果快照
- `report_version`：每次报告生成产生一个版本

最小关系：

- 报告要能关联其生成时的 `profile_version`
- 审核结果要能关联输入快照
- “是否基于最新档案生成”要能比较得出

这三者可以先定义为领域对象 / 组装层语义，不要求在首轮就铺完整物理表设计。

---

## 9. 迁移与兼容建议

### 9.1 不破坏现有主链

原则：

- 不因为新档案体系而破坏当前 Portal 主链
- 不要求一次性迁移旧订单数据
- 不要求旧 payload 立即补齐所有新字段

### 9.2 兼容策略

#### 旧字段兼容

- `university_preferences` 暂继续保留
- `guardian_notes` 暂继续保留
- `candidate_family` 暂继续保留

#### 新字段渐进接入

- 新页面先写新字段
- 旧页面仍能读旧字段
- 报告组装层做兼容映射

---

## 10. 字段映射实施优先级

### P0

- 锁定最小审核字段与建档字段边界
- 固化 `existing_plan_summary` 的产品主角色
- 定义 `profile_minimum_complete` / `review_entry_source` / `review_followup_action` 语义

### P1

- 加 `target_schools`
- 加 `school_preference_types`
- 加 `school_region_preferences`
- 加 `disliked_majors`
- 加 `priority_strategy`
- 加 `graduation_plan`
- 加 `tuition_preference`
- 加 `employment_region_preferences`

- `family_background`
- `industry_resources`
- `extra_notes`
- `interest_assessment_type`
- `interest_assessment_result`
- `interest_assessment_notes`
- `target_cities` 前台输入控件与保存链路已打通（2026-06-23）


---

## 11. 验收口径

字段映射完成后，应满足：

1. 审核优先主线可用最小字段启动
2. Step 2-4 不会反向阻塞审核入口
3. 新偏好字段有明确命名和分层归属
4. Order 与 Intake 的职责边界清楚
5. 版本语义在实现前就已钉住，不会后期漂移

---

## 12. 后续衔接文档

基于本映射表，下一步建议直接产出：

1. `P0/P1/P2 产品升级执行板`
2. `具体接口变更清单`
3. `Portal 表单改版实现计划`
4. `报告版本与档案版本关系说明`
