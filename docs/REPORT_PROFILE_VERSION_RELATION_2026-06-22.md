# REPORT_PROFILE_VERSION_RELATION_2026-06-22

最后更新: 2026-06-22
状态词: 报告版本与档案版本关系说明
真相源:
- `product/PRD_UPGRADE_2026-06-21.md`
- `docs/FIELD_MAPPING_AUDIT_FIRST_PROFILE_2026-06-21.md`
- `docs/UPGRADE_EXECUTION_BOARD_2026-06-22.md`

> 本文只钉住版本语义与最小关系，避免后续在“档案版本 / 审核结果版本 / 报告版本”上各写各的。

---

## 1. 为什么现在就要定义版本关系

当前项目已经有：

- 订单
- Portal intake
- 报告交付
- 状态页 / 报告页

但升级规划已经引入三个新语义：

- `profile_version`
- `review_result_version`
- `report_version`

如果现在不钉住，后续很容易出现三种漂移：

1. 前端把“最近一次查看”当版本
2. 后端把“每次导出 PDF”当版本
3. 产品把“档案更新后重新解读”与“报告重新生成”混成同一件事

所以本文只做一件事：

> 定义版本对象是什么、何时递增、彼此怎么关联。

---

## 2. 三个版本对象的定义

## 2.1 `profile_version`

定义：

- 每次用户保存一份可用于后续审核 / 规划的档案快照时，形成一个新的 `profile_version`

它代表的是：

- 当时的考生信息与偏好信息快照

它**不是**：

- 当前页面打开次数
- 表单每次按键修改
- 单字段临时草稿变化

### 最小包含内容

P0 / P1 至少覆盖：

- `candidate_province`
- `candidate_subjects`
- `candidate_score`
- `candidate_rank`
- P1 后续再加入 Step 2-4 偏好字段

### 递增规则

- 只有“保存档案快照成功”才递增
- 草稿未形成有效快照时，不递增

---

## 2.2 `review_result_version`

定义：

- 每次用户基于某组输入发起审核，并产出一份审核结果快照时，形成一个新的 `review_result_version`

它代表的是：

- 某次审核的输入与输出结论快照

它**不是**：

- 用户打开审核页
- 用户修改但未提交审核
- 结果页单纯重新渲染

### 最小包含内容

至少包括：

- 审核输入摘要
- 审核使用的最小约束
- 风险等级
- 核心发现
- 推荐后续动作

### 递增规则

- 只有“审核提交成功并产出结果”才递增
- 单纯重看历史结果，不递增

---

## 2.3 `report_version`

定义：

- 每次正式生成一份可交付 / 可查看的报告快照时，形成一个新的 `report_version`

它代表的是：

- 对外可查看、可下载、可沉淀的报告资产版本

它**不是**：

- PDF 重新下载一次
- 前端重新打开报告页
- 分享链接被访问一次

### 最小包含内容

至少包括：

- 报告结论摘要
- 风险说明
- 冲稳保结构
- 下一步建议
- 生成时使用的档案版本引用
- 生成时使用的审核结果版本引用（如存在）

### 递增规则

- 只有“正式生成新报告快照”才递增
- 同一份报告重复下载 / 查看，不递增

---

## 3. 三者之间的最小关系

## 3.1 核心关系

最小关系如下：

- `review_result_version` 产生时，**引用一个输入快照**
- `report_version` 产生时，**引用一个 `profile_version`**
- `report_version` 如基于某次审核生成，**可再引用一个 `review_result_version`**

也就是：

- 档案版本描述“你当时提供了什么信息”
- 审核结果版本描述“系统当时怎么判断”
- 报告版本描述“最终交付给用户的是什么”

---

## 3.2 推荐最小引用关系

### `review_result_version`

建议最小关联：

- `profile_version`：可选
- `review_input_snapshot`：必有

因为 P0 允许用户先审核再补档案，所以：

- 审核结果未必总是基于完整档案版本
- 但必须至少绑定当次审核输入快照

### `report_version`

建议最小关联：

- `profile_version`：必有
- `review_result_version`：可选但推荐有

原因：

- 报告是资产化对象，必须知道基于哪一版档案生成
- 如果报告是由某次审核深化而来，再关联那次审核结果更清楚

---

## 4. “是否基于最新档案生成”的判定规则

这是最容易说乱的一条。必须固定。

### 规则

当且仅当：

- `report.profile_version == latest_profile_version`

才可表述为：

- “该报告基于最新档案生成”

否则只能表述为：

- “该报告基于历史档案版本生成，建议刷新”

### 注意

不能用下面这些替代：

- 报告最近浏览时间
- 报告 PDF 最近下载时间
- 用户最后一次打开档案页时间

这些都不是版本判定。

---

## 5. P0 / P1 / P2 各阶段对版本的要求

## 5.1 P0

P0 不要求完整版本体系落库，但必须：

1. 在文档与接口语义上定义三个版本对象
2. 审核结果至少能绑定审核输入快照
3. Step 1 保存与报告回填之间留出 `profile_version` 语义位置

P0 重点是：

- **先定义语义，不强制一步到位做重表设计**

## 5.2 P1

P1 开始要求：

1. 报告页外显版本、时间、基于哪个档案
2. 能判断报告是否基于最新档案生成
3. 冲稳保和报告重组不打乱版本含义

## 5.3 P2

P2 才要求：

1. 多版本方案管理
2. 更完整的方案版本与报告版本关系
3. 不同阶段方案（初始 / 查分后 / 正式填报前）的并行管理

---

## 6. 推荐最小数据结构语义

这里先定义语义，不限定物理表。

### 6.1 ProfileVersion

最小字段语义：

- `profile_version_id`
- `order_id`
- `snapshot_payload`
- `created_at`
- `source`（portal / admin / import 等）

### 6.2 ReviewResultVersion

最小字段语义：

- `review_result_version_id`
- `order_id`
- `profile_version_id`（可空）
- `review_input_snapshot`
- `review_output_snapshot`
- `created_at`

### 6.3 ReportVersion

最小字段语义：

- `report_version_id`
- `order_id`
- `profile_version_id`
- `review_result_version_id`（可空）
- `report_snapshot`
- `artifact_refs`
- `created_at`

---

## 7. 当前实现下的落地建议

基于现有代码现状：

- 当前已有 `order_intakes.payload_json`
- 当前已有 `audit_report` / `pdf_path`
- 当前已有 Portal 状态页与报告页

建议：

### 7.1 P0

- 不立即改重 schema
- 先在文档、接口、页面语义上保留版本字段位置

- 报告生成链补 `profile_version` 引用
- 报告页展示“基于哪个档案版本”
- 如果有审核结果对象，再补 `review_result_version` 关联
- 当前实现（2026-06-23）已采用 `order_intakes.payload_json` 轻量保存：
  - `profile_versions[]` / `latest_profile_version_id`
  - `review_results{}` / `latest_review_result_id`
  - `report_versions[]` / `latest_report_version_id`
- “是否基于最新档案生成” 已按 `report.profile_version == latest_profile_version` 在报告页外显

### 7.3 P2

- 多版本方案页先复用 `profile_versions` 阶段标签（初始 / 查分后 / 正式填报前）
- 独立重表设计仍可后置


---

## 8. 禁止的错误实现

禁止：

1. 把 PDF 文件名变化当作新 `report_version`
2. 把页面重新打开当作新 `review_result_version`
3. 把草稿自动保存每次都当作新 `profile_version`
4. 让“最新浏览时间”替代“最新档案版本”
5. 让多版本方案先于版本语义定义落地

---

## 9. 最小结论

可以把三者压缩成一句话：

- `profile_version` = 用户给了什么信息
- `review_result_version` = 系统当时怎么判断
- `report_version` = 最终交付给用户什么结果

只要这三个定义不乱，后面的报告资产化、多版本方案、审核结果回放才不会互相打架。

---

## 10. 下一步建议

1. 在接口清单里给 `profile_version` / `review_result_version` / `report_version` 预留字段位
2. 在 P1 报告页实现时，把“基于哪个档案版本”做成显式外显项
3. 在进入多版本方案管理前，先确认版本对象的最小持久化方案
