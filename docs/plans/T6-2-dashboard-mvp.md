# T6.2 仪表盘 MVP Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 在现有 T6.1 FastAPI 管理后台骨架上补齐一个最小可用的仪表盘 MVP，只覆盖订单 / 用户 / 收入卡片、趋势图接口、FastAPI 路由清单与 ECharts 页面布局，不引入复杂筛选。

**Architecture:** 后端继续沿用 `admin/` 模块分层：路由层只做鉴权与响应封装，统计聚合下沉到 `admin/stats.py` 纯函数，直接对 SQLite 做只读 SQL 聚合。前端保持极简 HTML + ECharts：首屏 3 张 KPI 卡片 + 1 张趋势折线图 + 3 张分布图，不引入前端框架。

**Tech Stack:** FastAPI、Pydantic v2、SQLite (`sqlite3`)、纯 HTML/JS、ECharts 5。

---

## 1. 输入上下文与约束

已验证现状：

- `admin/app.py` 已存在 FastAPI app 工厂，并已挂载 `stats_router`。
- `admin/routes/stats.py` 已存在 `/api/stats/orders` 与 `/api/stats/dashboard` 路由位置。
- `admin/config.py` 已存在 `Settings.orders_db_path`，可区分 admin DB 与 orders DB。
- `README.md` 与 `docs/plans/T6-admin-mvp.md` 已给出 T6.2 目标口径，可作为本计划的事实基线。

本计划的 MVP 边界：

- 必做：3 张卡片（订单 / 用户 / 收入）
- 必做：1 个趋势接口（供折线图）
- 必做：FastAPI 路由清单
- 必做：ECharts 页面布局
- 不做：自定义时间范围、按渠道筛选、导出、钻取、对比环比、RBAC 细粒度权限

## 2. MVP 信息架构

### 2.1 页面结构

页面只分 3 个区域：

1. 顶部 KPI 卡片区
2. 中部趋势图区
3. 底部分布图区

### 2.2 卡片指标（MVP）

仅展示以下 3 张主卡片：

| 卡片   | 字段                          | 数据来源         | 展示格式    | 说明                                      |
| ------ | ----------------------------- | ---------------- | ----------- | ----------------------------------------- |
| 订单数 | `summary.total_orders`        | `orders` 表      | 整数        | 全量累计订单                              |
| 用户数 | `summary.total_users`         | `admin_users` 表 | 整数        | 后台可识别用户总数                        |
| 收入   | `summary.total_revenue_cents` | `orders` 表      | 元/两位小数 | 仅统计 `paid/serving/delivered/completed` |

MVP 不额外拆“今日 / 7d / 30d”成独立卡片；这些字段保留在响应里给 tooltip/副标题复用：

- `orders_today`
- `orders_7d`
- `orders_30d`
- `revenue_today_cents`
- `revenue_7d_cents`
- `revenue_30d_cents`

### 2.3 图表区域

| 区域         | 图表类型 | 对应字段                    | 目的             |
| ------------ | -------- | --------------------------- | ---------------- |
| 趋势区       | 双折线图 | `trends.7d` 或 `trends.30d` | 看订单与收入走势 |
| 状态分布     | 柱状图   | `by_status`                 | 看漏斗积压       |
| 来源分布     | 柱状图   | `by_source`                 | 看渠道结构       |
| 服务版本分布 | 柱状图   | `by_service_version`        | 看产品结构       |

MVP 默认首屏展示 `7d` 趋势；页面只提供一个轻量切换按钮：`7d / 30d`，不提供任意日期选择器。

## 3. 数据契约设计

### 3.1 推荐主接口

MVP 推荐以前端只请求一个主接口为主：

- `GET /api/stats/dashboard`

原因：

- 一次请求即可填满卡片、趋势、分布三类组件
- 避免前端并发多个请求导致空态/加载态不一致
- 与“最小 MVP”目标一致

### 3.2 Dashboard 响应结构

```json
{
  "summary": {
    "total_orders": 6,
    "total_revenue_cents": 100000,
    "total_users": 1,
    "orders_today": 3,
    "orders_7d": 4,
    "orders_30d": 5,
    "revenue_today_cents": 20000,
    "revenue_7d_cents": 70000,
    "revenue_30d_cents": 100000
  },
  "by_status": {
    "pending": 0,
    "paid": 1,
    "serving": 1,
    "delivered": 0,
    "completed": 1,
    "refunded": 1
  },
  "by_source": {
    "xianyu": 0,
    "wechat": 0,
    "web": 0,
    "school": 0
  },
  "by_service_version": {
    "audit": 0,
    "basic": 0,
    "standard": 0,
    "premium": 0
  },
  "trends": {
    "today": [{ "date": "2026-06-12", "orders": 3, "revenue_cents": 20000 }],
    "7d": [{ "date": "2026-06-06", "orders": 0, "revenue_cents": 0 }],
    "30d": [{ "date": "2026-05-14", "orders": 0, "revenue_cents": 0 }]
  },
  "generated_at": "2026-06-12T16:30:00+00:00"
}
```

### 3.3 关键口径

- 收入口径：仅 `paid` / `serving` / `delivered` / `completed` 计入 `total_revenue_cents`
- 时间粒度：按 UTC 日聚合，字段格式 `YYYY-MM-DD`
- 0 填充：趋势窗口内无订单的日期也必须返回 0 点
- 数据最小化：统计查询不读取 PII 字段

## 4. FastAPI 路由清单

### 4.1 MVP 必备路由

| 方法 | 路径                   | 鉴权 | 用途             | 备注                  |
| ---- | ---------------------- | ---- | ---------------- | --------------------- |
| GET  | `/api/stats/dashboard` | JWT  | 仪表盘主接口     | 前端首屏主数据源      |
| GET  | `/api/stats/orders`    | JWT  | 订单统计兼容接口 | 保留给旧页面/兼容调用 |
| GET  | `/health`              | 公开 | 健康检查         | 用于服务探活          |
| GET  | `/docs`                | 公开 | Swagger UI       | 调试联调              |
| GET  | `/openapi.json`        | 公开 | OpenAPI schema   | 合约校验              |

### 4.2 路由实现归属

- `admin/routes/stats.py`
  - `get_dashboard()`：返回 dashboard 聚合 payload
  - `get_order_stats()`：返回兼容版订单统计 payload
- `admin/app.py`
  - `app.include_router(stats_router)`：挂载统计路由
- `admin/auth.py`
  - 复用 `get_current_user` 做 JWT 保护

## 5. 后端实现拆分

### 5.1 文件落点

| 文件                                         | 动作      | 责任                        |
| -------------------------------------------- | --------- | --------------------------- |
| `admin/stats.py`                             | 新增/实现 | 纯函数聚合层                |
| `admin/routes/stats.py`                      | 修改      | FastAPI 响应模型 + 路由封装 |
| `admin/config.py`                            | 修改      | `orders_db_path` 配置       |
| `admin/tests/test_routes_stats_dashboard.py` | 新增      | dashboard 路由测试          |
| `README.md`                                  | 修改      | 补 T6.2 使用说明            |

### 5.2 聚合层接口建议

`admin/stats.py` 最小公开函数：

- `build_dashboard_payload(orders_db_path: str, admin_db_path: str) -> dict`
- `build_order_stats_payload(orders_db_path: str) -> dict`
- `compute_summary(...) -> dict`
- `compute_by_status(...) -> dict`
- `compute_by_source(...) -> dict`
- `compute_by_service_version(...) -> dict`
- `compute_trends(...) -> dict`

原则：

- SQL 聚合只做只读查询
- 路由层不直接拼 SQL
- 趋势补零逻辑做成独立辅助函数，便于单测

## 6. ECharts 页面布局

### 6.1 页面网格

建议 12 列响应式布局：

```text
┌──────────────────────────────────────────────┐
│ Header: 标题 + 更新时间 + 7d/30d 切换       │
├──────────────┬──────────────┬───────────────┤
│ 卡片1 订单数 │ 卡片2 用户数 │ 卡片3 收入     │
├──────────────────────────────────────────────┤
│ 趋势图（订单/收入双折线，占满整行）         │
├──────────────┬──────────────┬───────────────┤
│ 状态分布     │ 来源分布     │ 服务版本分布   │
└──────────────┴──────────────┴───────────────┘
```

### 6.2 组件说明

- 卡片区：纯 HTML + CSS 即可，不需要 ECharts
- 趋势图：ECharts 双 y 轴可选；若 MVP 想更简单，可单 y 轴并统一展示原值
- 分布图：3 张基础柱状图，统一使用分类轴 + 单系列

### 6.3 前端最小交互

只保留：

- 页面加载自动拉取 dashboard
- 点击 `7d / 30d` 切换趋势数据源
- 鼠标 hover 显示 tooltip

不做：

- 多筛选器联动
- 自动刷新
- 下载图片/CSV
- 图表钻取

## 7. 实施任务分解

### Task 1: 对齐统计口径与响应契约

**Objective:** 先冻结字段命名与收入/时间窗口口径，避免前后端反复返工。

**Files:**

- Modify: `docs/plans/T6-2-dashboard-mvp.md`
- Reference: `README.md`
- Reference: `docs/plans/T6-admin-mvp.md`

**Steps:**

1. 固定卡片字段只使用 `summary.total_orders` / `summary.total_users` / `summary.total_revenue_cents`
2. 固定趋势字段使用 `trends.7d` / `trends.30d`
3. 文档化收入与 0 填充口径
4. 复核字段名与 README 现有描述一致

**Verification:**

- 人工检查文档中字段名只出现一套命名
- README / 本计划 / 路由响应模型三者不冲突

### Task 2: 落统计聚合层

**Objective:** 让 dashboard 数据生成逻辑从路由层抽离到可测试纯函数。

**Files:**

- Create/Modify: `admin/stats.py`
- Reference: `admin/db.py`
- Test: `admin/tests/test_routes_stats_dashboard.py`

**Steps:**

1. 先写空库响应测试
2. 再写真实订单聚合测试
3. 实现 summary / by_status / by_source / by_service_version / trends
4. 跑 dashboard 相关测试并确认 0 填充与窗口边界正确

**Verification:**

- `pytest admin/tests/test_routes_stats_dashboard.py -v`
- 空库与真实数据两类断言都通过

### Task 3: 接入 FastAPI 路由

**Objective:** 暴露稳定的 `/api/stats/dashboard` 与兼容 `/api/stats/orders`。

**Files:**

- Modify: `admin/routes/stats.py`
- Reference: `admin/app.py`
- Reference: `admin/auth.py`

**Steps:**

1. 为 dashboard 定义响应模型
2. 路由层只做鉴权 + 调用聚合函数
3. 保留 `/api/stats/orders` 兼容字段名
4. 确认 `app.include_router(stats_router)` 已挂载

**Verification:**

- `pytest admin/tests/test_routes_stats_dashboard.py -v`
- `curl http://127.0.0.1:8000/openapi.json | jq '.paths["/api/stats/dashboard"]'`

### Task 4: 交付 ECharts MVP 页面

**Objective:** 用最少前端代码完成可视化首屏。

**Files:**

- Create: `admin/templates/dashboard.html` 或 `admin/static/dashboard.html`
- Create: `admin/static/dashboard.js`
- Optional Modify: `admin/app.py`（若需挂静态文件）

**Steps:**

1. 写 3 卡片 + 4 图表容器骨架
2. 首屏只请求 `/api/stats/dashboard`
3. 将 `summary` 映射到卡片，将 `trends` 映射到折线图
4. 将 `by_status` / `by_source` / `by_service_version` 映射到柱状图
5. 增加 7d / 30d 切换按钮

**Verification:**

- 浏览器打开页面后能看到 3 卡片 + 4 图表
- 空库情况下图表正常渲染 0 值，不报错

### Task 5: 补文档与联调说明

**Objective:** 让后续实现者和 QA 有明确的启动与验收路径。

**Files:**

- Modify: `README.md`
- Modify: `docs/plans/T6-admin-mvp.md`
- Modify: `docs/plans/T6-2-dashboard-mvp.md`

**Steps:**

1. 写启动命令与环境变量说明
2. 写 JWT 登录后如何请求 dashboard
3. 写页面联调步骤
4. 写空库 / 有数据两种验收场景

**Verification:**

- 新人按文档可独立跑通接口与页面

## 8. 验收标准

MVP 完成判定：

- `/api/stats/dashboard` 返回完整 payload
- 页面能展示 3 张卡片
- 页面能展示 1 张趋势图 + 3 张分布图
- 空库时全部组件可渲染，不报错
- 趋势默认展示 7d，能切到 30d
- 不存在复杂筛选器与额外交互膨胀

## 9. 风险与降级策略

| 风险                       | 影响             | 降级策略                            |
| -------------------------- | ---------------- | ----------------------------------- |
| 订单历史数据稀疏           | 趋势图断裂/难看  | 强制 0 填充                         |
| admin_users 与 orders 分库 | 聚合口径不一致   | 在 `summary` 层显式区分两个 DB      |
| 收入口径争议               | 前后端展示不一致 | 在文档与代码常量里固定 4 个有效状态 |
| 前端实现超范围             | MVP 延误         | 禁止引入筛选面板、框架化重构        |

## 10. 最短闭环建议

必须先做：

1. 冻结响应契约
2. 落纯函数聚合层
3. 接路由
4. 再做 ECharts 页面

可以并行：

- 前端静态布局草图
- README 联调文档

可延后：

- 任意日期筛选
- 导出
- 渠道/版本联动筛选
- 首页缓存

## 11. 验证路径

最小验证顺序：

1. `pytest admin/tests/test_routes_stats_dashboard.py -v`
2. `pytest admin/tests -v`
3. 启动 `python3 -m admin.app --port 8000`
4. 登录拿 JWT
5. `curl /api/stats/dashboard`
6. 浏览器打开 dashboard 页面，验证空库 / 样例数据两种场景

## 12. 结论

T6.2 的正确 MVP 不是“做一个复杂 BI 系统”，而是：

- 后端提供一个稳定的一站式 dashboard payload
- 前端用 ECharts 把 3 张核心卡片、1 张趋势图、3 张分布图展示出来
- 保持无复杂筛选、无重前端框架、无额外依赖膨胀

这条路径最短、风险最低，也与当前 `admin/` 骨架和项目 README 描述保持一致。
