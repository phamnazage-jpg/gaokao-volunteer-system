# UPGRADE_EXECUTION_BOARD_2026-06-22

最后更新: 2026-06-22
状态词: 用户侧升级规划执行板
真相源: `product/PRD_UPGRADE_2026-06-21.md`
配套文档:
- `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md`
- `docs/FIELD_MAPPING_AUDIT_FIRST_PROFILE_2026-06-21.md`
- `docs/CURRENT_STATE.md`
- `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`

> 本文件定义的是用户侧升级执行顺序与交付切线，不替代当前生产 readiness 执行板。

---

## 1. 当前执行结论

结论:

- 用户侧升级路线已明确收敛为“**审核优先 + Step 1 最小建档 + 审核结果分流 + 后续决策增强**”
- 本轮 P0 只负责让默认主线成立，不追求一次性完成完整档案、完整内容中心或完整资产化
- 当前生产 readiness 问题仍由 `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md` 管理；本执行板不覆盖真实支付 acceptance、自动交付主链、正式法务审定、异机恢复等门禁任务

本执行板的唯一目标是：

> 在不夸大现有能力、不混入生产门禁问题的前提下，把用户侧升级拆成可执行、可验收、可逐步落地的 P0 / P1 / P2 任务板。

---

## 2. 全局执行原则

### 2.1 默认主线原则

统一主线:

1. 首页
2. 先审核现有志愿方案 / 现有想法
3. 根据审核结果决定：
   - 进入冲稳保微调
   - 补充 Step 1 或后续档案
   - 进入完整规划 / 报告
4. 最终结合政策中心与同分段参考完成决策

禁止滑回：

- 先完整建档再开始服务
- 默认直接生成全新志愿方案
- 让 Step 2-4 偏好字段阻塞审核入口

### 2.2 分期原则

#### P0：先让审核优先主线成立

必须交付：

- 首页任务化 + 审核主 CTA 前置
- 审核页最小闭环
- Step 1 最小建档
- 审核结果分流

#### P1：再做决策与内容增强

增强交付：

- 冲稳保一级化
- Step 2-4 偏好建档
- 报告重组与资产外显
- 政策中心
- 同分段参考
- 内容可信度展示规则

#### P2：最后做深层增强

增强交付：

- 深层偏好增强
- 性格 / 兴趣测评联动
- 多版本方案管理

### 2.3 口径边界原则

禁止表述：

- “已完成完整 Web 自助 SaaS”
- “已完成全国统一高置信同分段参考 / 政策中心”
- “审核优先升级已替代生产 readiness 收口”
- “报告资产化已包含完整版本体系”

允许表述：

- “P0 审核优先主线已成立”
- “P1 冲稳保 / 政策 / 同分段参考处于增强阶段”
- “当前升级板与生产 readiness 执行板并行，各自管理不同问题域”

---

## 3. P0 执行板（当前最优先）

### P0-1 首页任务化 + 审核主 CTA 前置

- Owner: product / design / frontend
- 优先级: P0
- 状态: completed（2026-06-23 第三轮质量收敛完成；首页主 CTA / 工作台主动作 / 最近复核入口已本地验证）
- 目标:
  - 首页从落地 / 下单入口切为高考志愿工作台
  - 主 CTA 固定为“先审核现有志愿方案”
  - 用户进入首页后可快速理解当前阶段、下一步动作、审核优先主线
- 输入依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §7.1 / §8.1
  - `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md` §3
- 交付物:
  - 首页结构说明
  - 首页组件清单
  - 首页主 / 次 / 弱 CTA 文案
- 验收:
  - 首屏必须有 Banner、任务清单、主 CTA、次 CTA、最近审核结果 / 报告入口
  - 未建档用户可直接进入审核页
  - 首页不得把完整规划 / 生成方案作为默认第一主动作

### P0-2 审核页最小闭环

- Owner: product / backend / frontend
- 优先级: P0
- 状态: completed（2026-06-23 第三轮质量收敛完成；审核页已补齐输入区 / 最小约束区 / 结果区 / 分流区）
- 目标:
  - 审核页支持输入现有方案 / 现有想法
  - 审核页只要求最小约束信息：省份、科目组合、分数 / 位次
  - 审核后输出风险摘要与下一步建议
- 输入依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §8.1 F-P0-2
  - `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md` §4
  - `docs/FIELD_MAPPING_AUDIT_FIRST_PROFILE_2026-06-21.md` §5
- 数据依赖:
  - `existing_plan_summary`
  - `candidate_province`
  - `candidate_subjects`
  - `candidate_score`
  - `candidate_rank`
- 交付物:
  - 审核输入结构定义
  - 审核页状态机
  - 审核输出摘要结构
- 验收:
  - 审核提交时不要求 Step 2-4 完整档案
  - 页面必须有输入区、最小约束区、结果区、分流区
  - 审核结果不能停在孤立结果页

### P0-3 Step 1 最小建档

- Owner: product / backend / frontend
- 优先级: P0
- 状态: completed（2026-06-23 第三轮质量收敛完成；Step 1 四字段保存 / 回填 / 最小完成态已本地验证）
- 目标:
  - 只落 Step 1：省份、科目组合、分数、位次
  - 支持保存草稿、回填、复用
  - 明确“未填完整档案也可先审核”
- 输入依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §7.2 / §8.1 F-P0-3
  - `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md` §5
  - `docs/FIELD_MAPPING_AUDIT_FIRST_PROFILE_2026-06-21.md` §3 / §5
- 数据依赖:
  - `profile_minimum_complete`
  - Step 1 四字段回填语义
- 交付物:
  - Step 1 表单定义
  - Step 1 保存 / 回填规则
  - 最小完成状态定义
- 验收:
  - Step 1 可独立保存
  - 保存后可在审核页和报告页复用
  - Step 2-4 未完成不影响审核提交

### P0-4 审核结果分流

- Owner: product / frontend / analytics
- 优先级: P0
- 状态: completed（2026-06-23 第三轮质量收敛完成；三条分流路径与 followup action 已可记录 / 回放）
- 目标:
  - 审核结果页显式导向三类动作：冲稳保、补档案、完整规划 / 报告
  - 三类动作均可追踪
- 输入依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §8.1 F-P0-4
  - `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md` §4 / §10
  - `docs/FIELD_MAPPING_AUDIT_FIRST_PROFILE_2026-06-21.md` §5.3
- 数据依赖:
  - `review_entry_source`
  - `review_followup_action`
- 交付物:
  - 审核结果页结构
  - 分流动作枚举
  - 埋点字段定义
- 验收:
  - 至少有一个默认推荐动作
  - 三条分流路径都可实际进入对应页面
  - 分流动作可被状态或埋点记录

### P0-5 P0 验收门槛

- Owner: product / tech-lead
- 优先级: P0
- 状态: completed（2026-06-23 本地验证）
- 验收结论成立条件:
  1. 首页默认主入口已切为审核
  2. 审核入口可在未完整建档状态下工作
  3. Step 1 可保存并回填
  4. 审核结果可进入至少一条后续动作，且三条路径均存在
  5. 对外口径未误写为“完整 SaaS 已完成”
  6. 验证: `./.venv/bin/python -m pytest -q admin/tests/test_web_public.py admin/tests/test_web_public_content_pages.py admin/tests/test_web_public_portal_info.py admin/tests/test_web_public_review_flow.py data/orders/tests/test_schema.py` → `70 passed`

---

## 4. P1 执行板（P0 稳定后推进）

### P1-1 冲稳保一级化

- Owner: product / design / frontend
- 优先级: P1
- 状态: completed（2026-06-23；审核后可直接进入冲稳保视图，冲 / 稳 / 保已作为一级分栏呈现）
- 目标:
  - 把冲稳保从报告标签升级为一级入口与一级决策框架
- 输入依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §8.2 F-P1-1
  - `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md` §6
- 验收:
  - 冲 / 稳 / 保必须是一级切换或一级分栏
  - 审核结果页可直接进入冲稳保视图

### P1-2 Step 2-4 偏好建档

- Owner: product / backend / frontend
- 优先级: P1
- 状态: completed（2026-06-23；Step 2-4 字段命名与映射表一致，且不阻塞审核入口）
- 目标:
  - 落院校偏好、专业偏好、其他偏好三层建档
  - 统一字段命名、字段归属、文案语义
- 输入依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §7.2 / §8.2 F-P1-2
  - `docs/FIELD_MAPPING_AUDIT_FIRST_PROFILE_2026-06-21.md` §6 / §7 / §10
- 验收:
  - 新字段命名与映射表一致
  - Step 2-4 不阻塞审核入口

### P1-3 报告重组与资产外显

- Owner: product / backend / frontend
- 优先级: P1
- 状态: completed（2026-06-23；报告页已外显版本 / 最新性 / 下一步动作，并写入轻量 report_versions）
- 目标:
  - 报告页重组为结论摘要、风险、冲稳保、下一步动作的资产页
  - 显式外显版本、时间、基于哪个档案
- 输入依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §7.3 / §8.2 F-P1-5 / §10.4
  - `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md` §7
- 数据依赖:
  - `profile_version`
  - `review_result_version`
  - `report_version`
- 验收:
  - 报告页必须展示版本与下一步动作
  - 用户可判断报告是否基于最新档案生成

### P1-4 政策中心

- Owner: product / content / frontend
- 优先级: P1
- 状态: completed（2026-06-23；政策中心已展示来源 / 更新时间 / 适用省份，并提供辅助入口）
- 目标:
  - 按省提供政策摘要、时间节点、批次规则、选科要求、误区说明
- 输入依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §8.2 F-P1-4 / F-P1-6
  - `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md` §8
- 验收:
  - 页面必须展示来源、更新时间、适用省份
  - 未覆盖内容必须显式标注

### P1-5 同分段参考

- Owner: product / data / frontend
- 优先级: P1
- 状态: completed（2026-06-23；同分段参考已展示学校 / 专业 / 城市 / 扎堆提示与置信边界）
- 目标:
  - 提供同分段学校 / 专业 / 城市参考与扎堆提示
- 输入依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §8.2 F-P1-3 / F-P1-6
  - `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md` §9
  - `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md` Q-A 数据边界
- 验收:
  - 页面必须展示数据说明与置信等级说明
  - 非高置信数据不得使用强推荐口吻

### P1-6 内容可信度规则落地

- Owner: product / content / legal-review
- 优先级: P1
- 状态: completed（2026-06-23；政策中心 / 同分段参考已共用统一信任条并保留非高置信边界）
- 目标:
  - 把政策中心 / 同分段参考的来源、更新时间、适用范围、置信等级规则写成统一组件与文案规范
- 依赖:
  - `product/PRD_UPGRADE_2026-06-21.md` §8.2 F-P1-6
- 验收:
  - 页面级文案不再出现“全国统一高置信完整能力”误导表达

### P1-7 P1 验收门槛

- Owner: product / tech-lead
- 优先级: P1
- 状态: completed（2026-06-23 本地验证）
- 验收结论成立条件:
  1. 冲稳保成为一级能力
  2. Step 2-4 字段与映射表一致
  3. 报告页完成资产化基础外显
  4. 政策中心 / 同分段参考具备清晰可信度边界
  5. 未对外夸大 27 省能力与政策完整性
  6. 验证: `./.venv/bin/python -m pytest -q admin/tests/test_web_public_content_pages.py admin/tests/test_web_public_portal_info.py admin/tests/test_web_public_review_flow.py data/orders/tests/test_schema.py` → `60 passed`

---

## 5. P2 执行板（增强层）

### P2-1 深层偏好增强

- Owner: product / backend / frontend
- 优先级: P2
- 状态: completed（2026-06-23；family_background / industry_resources / employment_region_preferences / graduation_plan 已稳定落在 intake）
- 目标:
  - 增强家庭背景、行业资源、就业地域偏好、毕业规划等深层字段
- 依赖:
  - P1 字段语义稳定
- 验收:
  - 字段用途明确
  - 默认非强制
  - 不制造隐私压迫感

### P2-2 性格 / 兴趣测评联动

- Owner: product / algorithm / frontend
- 优先级: P2
- 状态: completed（2026-06-23；MBTI / 霍兰德等结果已进入辅助判断因子区块，且文案锁定“只作辅助”）
- 目标:
  - 将 MBTI / 霍兰德等结果作为辅助因子接入
- 依赖:
  - P1 路径稳定
- 验收:
  - 测评结果只作辅助，不作唯一判断

### P2-3 多版本方案管理

- Owner: backend / frontend / product
- 优先级: P2
- 状态: completed（2026-06-23；profile_versions / report_versions 已支持初始 / 查分后 / 正式填报前阶段区分）
- 目标:
  - 支持初始档案方案、查分后校准方案、正式填报前调整方案管理
- 依赖:
  - `profile_version` / `review_result_version` / `report_version` 语义已稳定
- 验收:
  - 用户能区分不同阶段的方案版本
  - 版本关系不与报告版本语义冲突

### P2-4 P2 验收门槛

- Owner: product / tech-lead
- 优先级: P2
- 状态: completed（2026-06-23 本地验证）
- 验收结论成立条件:
  1. 深层偏好字段已稳定
  2. 测评联动不破坏主路径
  3. 多版本方案不与报告 / 档案版本语义冲突
  4. 验证: `./.venv/bin/python -m pytest -q admin/tests/test_web_public_content_pages.py admin/tests/test_web_public_portal_info.py admin/tests/test_web_public_review_flow.py data/orders/tests/test_schema.py` → `60 passed`

---

## 6. 与生产 readiness 执行板的边界

本执行板**不覆盖**以下事项：

- T12-A 真实支付 acceptance
- T12-B `info_submitted -> serving` 自动主链
- T12-D retention cleanup 生产化部署验收
- L-A 正式法务审定
- L-B 异机备份恢复演练
- Q-A 非湖南省份高置信数据密度深化

这些任务继续由：

- `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`

负责管理。

本执行板与生产 readiness 执行板的关系是：

- 生产 readiness 板管“现有系统上线门禁与真实能力收口”
- 升级执行板管“用户侧体验升级顺序与验收切线”

两者并行，但**不能混写、不能互相替代**。

---

## 7. 当前推荐执行顺序

### 第一阶段

1. P0-1 首页任务化 + 审核主 CTA 前置
2. P0-2 审核页最小闭环
3. P0-3 Step 1 最小建档
4. P0-4 审核结果分流
5. P0-5 P0 验收门槛核定

### 第二阶段

6. P1-1 冲稳保一级化
7. P1-2 Step 2-4 偏好建档
8. P1-3 报告重组与资产外显
9. P1-4 政策中心
10. P1-5 同分段参考
11. P1-6 内容可信度规则落地
12. P1-7 P1 验收门槛核定

### 第三阶段

13. P2-1 深层偏好增强
14. P2-2 性格 / 兴趣测评联动
15. P2-3 多版本方案管理
16. P2-4 P2 验收门槛核定

---

## 8. 当前推荐读取顺序

1. `product/PRD_UPGRADE_2026-06-21.md`
2. `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md`
3. `docs/FIELD_MAPPING_AUDIT_FIRST_PROFILE_2026-06-21.md`
4. `docs/UPGRADE_EXECUTION_BOARD_2026-06-22.md`（本文件）
5. `docs/CURRENT_STATE.md`
6. `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`

---

## 9. 下一步执行建议

最优先:

1. 先把 P0-1 ~ P0-4 各自拆成页面 / 接口 / 状态 / 埋点四类子任务
2. 输出最小接口变更清单，确认 Step 1、审核输入、审核结果分流的数据承接方式
3. 在 P0 验收通过前，不提前拉长到完整政策中心、完整同分段参考或多版本方案管理

原因:

- 当前最大风险不是缺想法，而是范围失控
- P0 的唯一目标是让“审核优先”真正成立
- 只有 P0 成立后，P1 的冲稳保 / 内容中心 / 资产化才有稳定承接面
