# API 参考（当前真相）

本文档描述 2026-06-13 当前仓库中已落地、可验证的接口与命令行入口。

适用范围：

- 管理后台 FastAPI API
- 已交付 CLI（审核 / 订单 / 数据溯源）
- 关键数据契约与鉴权约定

不包含：

- 旧版 `spec_checker_v2.py` 的逐函数说明
- 尚未落地或未完成线上验收的用户端 Web 自助下单/支付/资料填写闭环

---

## 1. 当前接口面

### 1.1 HTTP / FastAPI

服务入口：`python3 -m admin.app --port 8000`

基础约定：

- 健康检查：`GET /health`
- 登录：`POST /api/auth/login`
- Bearer 鉴权：除 `/health`、`/dashboard`、`/s/{code}` 外，管理 API 默认需要 JWT
- OpenAPI：`GET /openapi.json`
- Swagger：`GET /docs`

### 1.2 CLI

当前仓库内已落地的主要 CLI：

- `python3 -m skills.gaokao-audit.scripts.audit_cli <input>`
- `python3 scripts/gaokao-order-manager ...`
- `python3 scripts/gaokao-data-trace <school_name>`
- `python3 scripts/gaokao-quick-3min.py`
- `python3 scripts/gaokao-channel-fallback ...`

---

## 2. 管理后台 HTTP API

### 2.1 健康检查

#### `GET /health`

用途：进程/配置级健康检查。

响应示例：

```json
{
  "status": "ok"
}
```

---

### 2.2 认证 API

#### `POST /api/auth/login`

用途：管理员登录，获取 Bearer JWT。

请求体：

```json
{
  "username": "admin",
  "password": "admin123"
}
```

成功响应：

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "...",
    "username": "admin",
    "role": "admin"
  }
}
```

使用方式：

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```

#### `GET /api/auth/me`

用途：获取当前登录管理员信息。

请求头：

```text
Authorization: Bearer <token>
```

---

### 2.3 元数据 API

#### `GET /api/meta`

用途：返回后台前端使用的枚举/元信息。

典型用途：

- 订单状态枚举
- 来源渠道枚举
- 服务版本枚举
- 案例审核状态等

---

### 2.4 用户 API（T6.3）

#### `GET /api/users`

用途：分页列出用户，默认返回脱敏字段。

常见查询参数：

- `limit`
- `offset`
- 其他筛选项以 OpenAPI 为准

#### `GET /api/users/{user_key}`

用途：查看单个用户详情。

说明：`user_key` 可为内部 id 或路由支持的用户标识。

---

### 2.5 订单 API（T6.4）

#### `GET /api/orders`

用途：分页列出订单。

常见查询参数：

- `status`
- `source`
- `limit`
- `offset`

说明：

- 列表默认走脱敏输出
- 不应依赖该接口获取完整明文手机号/身份证号

#### `GET /api/orders/export`

用途：导出订单 CSV。

说明：

- 当前导出路径复用后台查询条件
- 输出仍遵循后台脱敏边界
- 如需对外发送报表，建议二次审核 CSV 内容

#### `GET /api/orders/{order_id}`

用途：查看订单详情与状态历史。

#### `POST /api/orders`

用途：手工录单。

典型字段：

```json
{
  "source": "xianyu",
  "service_version": "audit",
  "amount_cents": 4900,
  "customer_name": "王家长",
  "customer_phone": "13800001234",
  "candidate_name": "李明",
  "candidate_province": "湖南",
  "candidate_score": 578,
  "candidate_rank": 26800
}
```

说明：

- `external_id` 可留空，支持人工补录
- 写路径复用 `OrdersDAO` 状态机与落库逻辑

#### `PATCH /api/orders/{order_id}`

用途：更新订单业务字段、推进状态、处理退款。

说明：

- 非法状态流转会被拒绝
- 订单状态机为：`pending -> paid -> serving -> delivered -> completed`，另有 `refunded`
- 文档应以 OpenAPI 和 `data/orders/state_machine.py` 为最终事实源

---

### 2.6 案例 API（T6.5）

#### `GET /api/cases`

用途：案例列表。

#### `POST /api/cases`

用途：创建案例。

#### `GET /api/cases/{case_id}`

用途：查看案例详情。

#### `PATCH /api/cases/{case_id}`

用途：更新案例。

#### `POST /api/cases/{case_id}/review`

用途：案例审核。

#### `DELETE /api/cases/{case_id}`

用途：删除案例。

---

### 2.7 统计 API（T6.2）

#### `GET /api/stats/dashboard`

用途：一站式仪表盘数据。

响应结构：

- `summary`
- `by_status`
- `by_source`
- `by_service_version`
- `trends`
- `generated_at`

关键口径：

- 收入 = `paid / serving / delivered / completed` 四态订单的 `amount_cents` 累计值
- `pending`、`refunded` 不计入收入
- 趋势桶粒度为天（UTC）
- 空日期补 0，前端得到稠密序列
- 统计路径不读取 PII

#### `GET /api/stats/orders`

用途：兼容订单统计接口；字段名沿用早期 stub 版本，但已接真实 SQL 聚合。

---

### 2.8 UI 路由

#### `GET /dashboard`

用途：极简后台仪表盘页面。

说明：

- 页面本身可公开访问
- 数据请求仍依赖登录态/JWT

#### `GET /s/{code}`

用途：分享页短链接访问入口。

说明：

- 由 `data/share/short_link.py` 与 `admin/share_page.py` 提供能力
- 权限控制支持 `read/comment/edit/admin`

---

## 3. CLI 接口

### 3.1 AI 审核 CLI

入口：`python3 -m skills.gaokao-audit.scripts.audit_cli`

命令格式：

```bash
python3 -m skills.gaokao-audit.scripts.audit_cli plan.txt \
  --output plan.audit.pdf \
  --format text \
  --json
```

参数：

- `input`：方案文件路径
- `--output`：PDF 输出路径；默认 `<input>.audit.pdf`
- `--format`：`text | pdf_text | screenshot_ocr`
- `--json`：额外输出审核结果 JSON

标准输出包含：

- 输入文件路径
- 识别省份
- 综合评分
- PDF 报告路径
- 可选 JSON payload

主链能力：

- 方案解析
- 规范检查集成
- 扎堆风险检测
- HTML/PDF 报告输出

---

### 3.2 订单管理 CLI

入口：`python3 scripts/gaokao-order-manager`

通用参数：

- `--db <path>`：订单库路径，默认 `data/orders.db`
- `--human`：终端友好文本输出；默认 JSON
- `--actor`：操作者标识

已落地子命令：

- `create`
- `list`
- `show`
- `update`
- `pay`
- `deliver`
- `upgrade`
- `stats`
- `export`

示例：

```bash
python3 scripts/gaokao-order-manager --db data/orders.db create \
  --source xianyu \
  --service-version audit \
  --amount-cents 4900 \
  --customer-name 王家长 \
  --customer-phone 13800001234 \
  --candidate-name 李明 \
  --candidate-province 湖南 \
  --candidate-score 578
```

```bash
python3 scripts/gaokao-order-manager --db data/orders.db pay <order_id>
python3 scripts/gaokao-order-manager --db data/orders.db deliver <order_id>
python3 scripts/gaokao-order-manager --db data/orders.db export --output orders.csv
```

行为约束：

- 详情默认返回状态历史
- `update` 仅允许业务字段，`status` 不允许直接硬改
- 状态流转必须走状态机
- 默认输出经过 `Order.to_dict()` 脱敏处理

---

### 3.3 数据溯源 CLI

入口：`python3 scripts/gaokao-data-trace`

命令格式：

```bash
python3 scripts/gaokao-data-trace "中南大学"
python3 scripts/gaokao-data-trace "中南大学" --human
```

参数：

- `school_name`：院校名称，支持包含匹配
- `--human`：终端友好输出；默认 JSON

输出字段：

- `province`
- `school`
- `major`
- `frequency`
- `platforms`
- `predicted_increase`
- `alternatives`
- `score_range`
- `data_year`
- `source`
- `source_url`
- `source_type`
- `confidence`
- `last_updated`

用途：

- 查询某院校/专业推荐的来源信息
- 向审核报告补充“为什么这样推荐”的数据依据

---

## 4. 关键数据契约

### 4.1 订单状态机

当前文档级约定：

- `pending`
- `paid`
- `serving`
- `delivered`
- `completed`
- `refunded`

注意：

- 直接写状态属于越界使用
- HTTP 与 CLI 都应复用 `OrdersDAO.transition_status()`

### 4.2 订单隐私边界

默认脱敏字段包括但不限于：

- 手机号
- 身份证号
- 部分姓名

明文敏感数据不应通过普通列表接口、CSV 报表或分享页直接暴露。

### 4.3 统计口径

仪表盘与统计接口共享以下前提：

- `GAOKAO_DB_PATH`：admin 用户库
- `GAOKAO_ORDERS_DB_PATH`：订单库
- 收入统计只看订单金额和状态，不读取 PII

---

## 5. 环境变量

常用运行变量：

- `GAOKAO_ENV`
- `GAOKAO_DB_PATH`
- `GAOKAO_ORDERS_DB_PATH`
- `GAOKAO_JWT_SECRET`
- `GAOKAO_ADMIN_USER`
- `GAOKAO_ADMIN_PASS`
- `GAOKAO_ORDERS_FERNET_KEY`

最低要求：

- 生产环境必须提供高熵 `GAOKAO_JWT_SECRET`
- 订单/用户相关路径需要 `GAOKAO_ORDERS_FERNET_KEY`
- 生产环境不得使用默认弱口令 `admin123`

---

## 6. 验证建议

查看最新 API 真相：

```bash
python3 -m admin.app --port 8000
curl http://127.0.0.1:8000/openapi.json
```

验证 T5 主链测试：

```bash
python3 -m pytest tests/test_t5_e2e_workflows.py tests/test_t5_performance.py -q
```

如本文与代码不一致，优先级顺序为：

1. 代码与实跑结果
2. OpenAPI / CLI `--help`
3. 本文档
