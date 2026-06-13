# T6.5 案例管理 MVP Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 在现有管理后台中补齐一个最小可用的案例管理 MVP，只覆盖案例列表、详情、创建/编辑必需字段、三类分类、审核状态，以及与 T6.6 WebUI 的清晰接口边界。

**Architecture:** 继续沿用 `admin/` + `data/cases/` 的分层：`data/cases` 负责 SQLite 模型/DAO/Schema，`admin/routes/cases.py` 负责 HTTP 契约与鉴权，T6.6 仅消费这些 API 做 HTML + 静态页面。MVP 不新增复杂工作流，只保留案例内容维护与审核发布两条主链路，避免把 WebUI 逻辑和业务状态耦合在一起。

**Tech Stack:** FastAPI、Pydantic v2、sqlite3、dataclass、pytest、纯 HTML/JS（T6.6）。

---

## 1. 已确认上下文

已存在的事实：

- `admin/routes/cases.py` 已提供 `/api/cases` CRUD 与 `/api/cases/{id}/review`。
- `data/cases/models.py`、`dao.py`、`schema.py` 已定义案例表结构与持久化层。
- `admin/app.py` 已挂载 `cases_router`，并在启动时初始化 cases schema。
- `admin/tests/test_routes_cases.py` 已覆盖 CRUD / 审核 / 过滤主路径。
- `docs/ADMIN_DESIGN.md` 已给出“成功 / 典型 / 警告”的管理目标，但还需要收敛成 MVP 可执行边界。

本计划的输出目标不是扩功能，而是把“案例管理 MVP”收敛成可实现、可验收、不会和 T6.6 混线的设计说明。

## 2. MVP 范围

### 2.1 必做

- 案例列表
- 案例详情
- 创建 / 编辑所需字段
- 分类字段：`success` / `typical` / `warning`
- 审核状态字段：`pending` / `approved` / `rejected`
- 与 T6.6 的接口边界说明

### 2.2 不做

- 复杂 RBAC
- 工作流流转图
- 富文本编辑器
- 评论 / 版本历史 / 审核流多级状态
- 批量导入 / 批量审核
- 案例浏览统计

## 3. 数据契约（MVP 统一口径）

### 3.1 列表字段

列表接口必须返回以下字段，供 T6.6 页面直接渲染：

- `id`
- `title`
- `category`
- `summary`
- `review_status`
- `review_note`
- `reviewer`
- `reviewed_at`
- `created_at`
- `updated_at`
- `tags`

列表额外保留：

- `total`
- `limit`
- `offset`

### 3.2 详情字段

详情页必须返回完整案例正文，MVP 详情字段如下：

- `id`
- `title`
- `category`
- `summary`
- `content`
- `review_status`
- `review_note`
- `reviewer`
- `reviewed_at`
- `created_at`
- `updated_at`
- `tags`

### 3.3 创建 / 编辑必需字段

创建与编辑统一使用同一组基础字段：

- `title`（必填）
- `category`（必填）
- `summary`（可空）
- `content`（可空）
- `tags`（可空数组，默认空）

说明：

- 审核字段不允许由创建 / 编辑接口直接写入。
- 审核状态只允许通过独立审核接口修改，避免前端绕过审核。

### 3.4 分类字段

分类只保留三类：

| 值        | 含义     | MVP 作用            |
| --------- | -------- | ------------------- |
| `success` | 成功案例 | 对外展示的正向结果  |
| `typical` | 典型案例 | 结构化方法论样本    |
| `warning` | 警告案例 | 错误示范 / 风险提示 |

### 3.5 审核状态字段

审核状态只保留三态：

| 值         | 含义   | 默认 |
| ---------- | ------ | ---- |
| `pending`  | 待审   | 是   |
| `approved` | 已通过 | 否   |
| `rejected` | 已驳回 | 否   |

审核动作必须记录：

- `review_note`
- `reviewer`
- `reviewed_at`

## 4. API 边界与 T6.6 分工

### 4.1 T6.5 负责的接口

| 方法   | 路径                     | 用途               |
| ------ | ------------------------ | ------------------ |
| GET    | `/api/cases`             | 列表 / 过滤 / 分页 |
| POST   | `/api/cases`             | 创建               |
| GET    | `/api/cases/{id}`        | 详情               |
| PATCH  | `/api/cases/{id}`        | 编辑               |
| POST   | `/api/cases/{id}/review` | 审核通过 / 驳回    |
| DELETE | `/api/cases/{id}`        | 删除               |

### 4.2 T6.6 只消费、不承载的内容

T6.6 只做：

- HTML 页面布局
- 列表页渲染
- 新建 / 编辑表单
- 详情页展示
- 审核按钮与表单提交
- 静态资源托管

T6.6 不做：

- 数据校验规则的业务真相
- 审核状态流转规则
- 案例分类枚举定义
- 任何数据库写入逻辑

原则：

- 业务真相留在 API / DAO
- 页面只负责展示与提交
- 页面状态不反向定义业务状态

## 5. 实现落点（若进入编码）

### 5.1 业务层

- `data/cases/models.py`：维护案例 dataclass / 枚举
- `data/cases/dao.py`：CRUD、过滤、审核写入
- `data/cases/schema.py`：表结构 / 索引 / 默认值

### 5.2 HTTP 层

- `admin/routes/cases.py`：请求模型、响应模型、JWT 鉴权、错误映射
- `admin/app.py`：确保路由挂载与启动初始化

### 5.3 测试层

- `admin/tests/test_routes_cases.py`：CRUD、审核、404、过滤
- 可补充：`data/cases/tests/` 用于 DAO / schema 级别验证

## 6. 验证标准

最小验证闭环：

1. 列表能返回 `category`、`review_status`、`tags`
2. 详情能返回 `content`
3. 创建 / 编辑只能写基础字段
4. 审核只能通过审核接口修改
5. `pending -> approved/rejected` 可落库
6. 列表过滤 `category + review_status` 可用
7. 删除后详情返回 404
8. T6.6 只依赖 API 契约，不直接碰 DAO

建议验证命令：

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m pytest admin/tests/test_routes_cases.py -q
```

## 7. 风险与约束

- 风险 1：创建 / 编辑 / 审核响应字段不一致，导致 T6.6 页面二次映射复杂。
  - 缓解：统一响应结构，列表和详情共享同一基础模型。
- 风险 2：审核字段被普通编辑接口覆盖，破坏发布边界。
  - 缓解：基础编辑 payload 不包含审核字段。
- 风险 3：T6.6 把页面逻辑写成“第二套业务规则”。
  - 缓解：页面只消费 API 枚举值，所有枚举定义单一来源。
- 风险 4：分类语义漂移，`success/typical/warning` 被扩成更多状态。
  - 缓解：MVP 只允许三类，不预留多余枚举。

## 8. 交付判定

当且仅当以下条件都满足时，T6.5 MVP 才算设计完成：

- 字段集明确且最小化
- 列表 / 详情 / 创建 / 编辑 / 审核边界清楚
- 分类与审核状态枚举闭合
- T6.6 仅消费 API，不重复定义业务规则
- 后续实现者可以直接按本文档落地，不需要再猜字段
