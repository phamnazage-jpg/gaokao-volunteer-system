# T9 错误处理体系 — 详细设计

**状态**: v0.3 实施设计（T9.1 + T9.2 + T9.3 已落地，T9.4 待办）
**最后更新**: 2026-06-12
**关联文档**: [IMPLEMENTATION_PLAN_v2.md](../IMPLEMENTATION_PLAN_v2.md)
**关联任务**: T9.1 错误码体系 / T9.2 用户友好提示 / T9.3 日志记录 / T9.4 异常捕获装饰器

---

## 0. 变更日志

| 版本 | 日期       | 变更                                                      |
| ---- | ---------- | --------------------------------------------------------- |
| 0.1  | 2026-06-12 | 起草 T9.1 错误码体系 + T9.2 用户友好提示设计              |
| 0.2  | 2026-06-12 | 复盘: HTTP 422 兼容回退、`is_registered` 注册守卫         |
| 0.3  | 2026-06-12 | 新增 T9.3 结构化 JSON 日志设计（contextvars + formatter） |

---

## 1. 设计目标

### 1.1 总目标

为 admin 后台提供生产可观测的 **统一错误处理 + 结构化日志** 体系：

- 用户看到的永远是中文 message + 可执行 suggestion
- 运营 / 排障人员在日志里看到的是结构化 JSON，能按 `code`、`path`、`request_id` 聚合
- 错误码与 HTTP 状态码解耦，新增业务码不需要改 HTTP 语义
- 业务码注册守卫：`codes.py` 声明 + `registry.py` 翻译 + CI 校验三者必须一致

### 1.2 非目标

- ❌ 完整 ELK / Loki 集成（MVP 阶段写 stdout JSON 即可，由部署层收集）
- ❌ 分布式 trace（无 user_id 串联、单进程 MVP；contextvars 占位方便后续接入 OpenTelemetry）
- ❌ 多语言（i18n 资源包只放 zh-CN，结构上预留 en-US 入口）
- ❌ 异步日志队列（`QueueHandler` 后续 T11 性能加固再做）

### 1.3 关键原则

| 原则               | 说明                                                                |
| ------------------ | ------------------------------------------------------------------- |
| **零第三方运行时** | 日志 / 错误处理全部 stdlib；不引 `python-json-logger` / `structlog` |
| **关注点分离**     | 错误码 `codes.py` / 翻译 `registry.py` / 渲染 `exceptions.py` 三分  |
| **可测试性**       | 单元测试只读 `LogRecord` 不走 formatter，集成测试才走 JSON 编码     |
| **不回溯破坏**     | T9.3 不改 T9.2 既有响应体契约，仅替换日志输出形态                   |

---

## 2. 错误码体系 (T9.1)

### 2.1 码点结构

```
E AA BBB
| |   +-- 段内顺序号 (001-999, 零填充 3 位)
| +----- 段号 (2 位)
+-------- 字面量 'E' 固定前缀
```

| 段号  | 段名   | 范围          | 含义                         |
| ----- | ------ | ------------- | ---------------------------- |
| 01    | 用户   | E01001-E01199 | 输入、格式、必填等客户端错误 |
| 02    | 业务   | E02001-E02199 | 业务规则违反、状态机非法     |
| 03    | 数据   | E03001-E03199 | 数据访问、持久化失败         |
| 04    | 第三方 | E04001-E04199 | 上游服务 / 渠道故障          |
| 05    | 系统   | E05001-E05099 | 内部错误、资源耗尽、配置缺失 |
| 90-99 | 保留   | -             | 不分配给业务                 |

### 2.2 子域位（段内第 2 位 `xx?xx` 中的 `?`）

| 位  | 含义      | 典型场景           |
| --- | --------- | ------------------ |
| 0   | 通用      | 跨段兜底           |
| 1   | 凭证      | 登录、token、密码  |
| 2   | 会话/速率 | 限流、刷新、过期   |
| 3   | 权限/状态 | RBAC、订单状态机   |
| 4   | 设备/并发 | 同一账号多端、抢锁 |
| 5   | 配额/迁移 | 余额、迁移、灰度   |

### 2.3 强制规则

- **5xx 系统错误严禁落到非 05 段**（防兜底掩盖），由单元测试守门
- `FALLBACK_CODE = E05099` 是兜底码，未注册的业务异常统一映射到它
- 字面量前缀 `E` 用于日志链路快速定位业务错误
- 与 HTTP 状态码 **解耦** — 同一 HTTP 状态可对应不同业务码（如 401 = `E01101` 凭证错 / `E01102` 账号禁用）

---

## 3. 用户友好提示 (T9.2)

### 3.1 翻译注册表

`admin/errors/registry.py` 维护 `MESSAGES_ZH_CN: Dict[str, Message]`，每个 `Message` 包含：

| 字段         | 类型    | 约束                            |
| ------------ | ------- | ------------------------------- |
| `code`       | str     | 6 字符码点                      |
| `message`    | str     | ≤ 30 字，一句话讲清楚发生了什么 |
| `suggestion` | str     | ≤ 50 字，具体到下一步动作       |
| `severity`   | Literal | `info` / `warn` / `error`       |
| `retryable`  | bool    | 前端/SDK 可据此决定自动重试策略 |

### 3.2 注册守卫

- `is_registered(code) -> bool` — CI 校验 `codes.py` 声明的每个常量都在 `MESSAGES_ZH_CN` 中存在
- `MessageNotFoundError` — 运行时 `get_message` 找不到时抛，handler 自动映射到 `FALLBACK_CODE`
- 单元测试覆盖每个声明的码点都有中文翻译（防散落字符串）

### 3.3 响应体契约

```json
{
  "code": "E01101",
  "message": "用户名或密码错误",
  "suggestion": "请检查后重试，3 次失败将锁定 5 分钟",
  "severity": "warn",
  "retryable": false,
  "detail": { "fields": [...] }   // 可选，调试上下文
}
```

`detail` 在生产环境按 `include_detail` 开关脱敏；目前默认未启用。

### 3.4 FastAPI handler 矩阵

| 异常类型                 | 业务码映射               | HTTP 状态         | 日志级别  |
| ------------------------ | ------------------------ | ----------------- | --------- |
| `BusinessError`          | `exc.code`               | `http_status_for` | warning   |
| `HTTPException`          | `FALLBACK_CODE`          | `exc.status_code` | warning   |
| `RequestValidationError` | `DATA_VALIDATION_FAILED` | 422               | info      |
| `Exception` (兜底)       | `SYS_INTERNAL_ERROR`     | 500               | exception |

---

## 4. 结构化日志 (T9.3)

### 4.1 目标

让 `admin.*` logger 在生产模式下输出 **单行 JSON**，每条日志可被 ELK / Loki / `jq` 直接消费。

### 4.2 输出 schema

```json
{
  "ts": "2026-06-12T16:30:01.234Z",
  "level": "warning",
  "logger": "admin.errors",
  "msg": "BusinessError code=E01101 path=/api/auth/login method=POST status=401",
  "ctx": {
    "request_id": "req_8d3a...",
    "code": "E01101",
    "path": "/api/auth/login",
    "method": "POST"
  },
  "exc": {
    // 可选，异常时才有
    "type": "BusinessError",
    "message": "E01101",
    "traceback": "Traceback (most recent call last):\n  ..."
  }
}
```

### 4.3 设计要点

| 决策                                                     | 理由                                                                           |
| -------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **stdlib `logging.Formatter` 子类**                      | 不引第三方；与 uvicorn 自带 logger 兼容                                        |
| **`contextvars` 绑定 per-request 上下文**                | FastAPI 异步安全；不影响并发请求之间的污染                                     |
| **`log_event(logger, level, event, **fields)` helper\*\* | 业务代码一行写结构化事件，避免拼字符串 + extra dict                            |
| **不替换标准 `logger.info("msg %s", x)` 调用形态**       | 最小侵入；现有 `admin.errors` handler 的 4 处 `logger.*` 自动享受 JSON         |
| **测试隔离**                                             | 单元测试不安装 formatter，直接断言 `LogRecord`；集成测试才验 JSON              |
| **traceback 脱敏**                                       | 不在 JSON 里去掉 traceback（排障需要），但生产环境如果走 secret 字段要二次过滤 |

### 4.4 ContextVar 设计

```python
# admin/logging_utils.py
_request_ctx: ContextVar[Dict[str, Any]] = ContextVar("request_ctx", default={})

def bind_request_context(**fields) -> Token: ...
def clear_request_context(token) -> None: ...
def current_context() -> Dict[str, Any]: ...
```

- `bind_request_context` 在 FastAPI middleware 进入时调用，写入 `request_id` / `path` / `method`
- `clear_request_context` 在 middleware 退出时调用 `reset(token)`，避免泄漏到下一个请求
- `JsonLogFormatter.format()` 在编码前 `ctx.update(current_context())` 合并

### 4.5 与既有 handler 的集成

`admin/errors/exceptions.py` 现有 4 处 `logger.*` 调用改为：

```python
# 之前
logger.warning("BusinessError code=%s path=%s method=%s status=%d",
               code_str, request.url.path, request.method, http_status)

# 之后（等价输出，但 ctx 字段在 JSON 里可单独 grep）
log_event(logger, logging.WARNING, "business_error",
          code=code_str, path=request.url.path, method=request.method,
          status=http_status)
```

`log_event` 内部 `logger.log(level, msg, extra={"ctx": fields, "event": event_name})`，formatter 把 `extra["ctx"]` 提升到顶层 `ctx` 字段。

### 4.6 测试策略

| 测试                           | 覆盖                                                                 |
| ------------------------------ | -------------------------------------------------------------------- |
| `TestJsonLogFormatter`         | 时间格式、级别、logger 名、ctx 提升、exc 序列化                      |
| `TestLogEvent`                 | 普通字段、嵌套字段、保留 key (`code`/`path`/`method`)                |
| `TestRequestContext`           | bind / clear 不污染并发、contextvars 隔离                            |
| `TestTracebackSanitization`    | 异常记录包含 `exc.type/msg/traceback`                                |
| `TestFastAPIHandlerStructured` | 端到端：触发 `BusinessError`，捕获 stderr 验证 JSON 含 `code`/`path` |
| `TestPlainTextMode`            | `LOG_FORMAT=plain` 时回退到原文本格式（开发友好）                    |

### 4.7 配置开关

| 环境变量           | 取值         | 默认 | 含义                               |
| ------------------ | ------------ | ---- | ---------------------------------- |
| `ADMIN_LOG_FORMAT` | `json`       | json | 单行 JSON 输出                     |
| `ADMIN_LOG_FORMAT` | `plain`      | -    | 原 `%(asctime)s %(levelname)s ...` |
| `ADMIN_LOG_LEVEL`  | 任意合法级别 | info | 全局日志级别                       |

`admin/app.py::create_app` 不再调用 `logging.basicConfig`；由 `main()` 在启动 uvicorn **前**安装 formatter，测试中通过 `monkeypatch` 注入。

### 4.8 风险与缓解

| 风险                                       | 缓解                                                           |
| ------------------------------------------ | -------------------------------------------------------------- |
| uvicorn 自带 access logger 仍走 plain      | 文档说明：用 `--log-config` 切换；MVP 不强制统一               |
| 业务代码 `logger.info("x=%s", x)` 仍是文本 | 接受：纯文本也能 grep；但鼓励用 `log_event` 走结构化           |
| 异常 traceback 体积过大                    | 限制 `exc.traceback` ≤ 4KB；超出截断并加 `truncated=true` 标记 |
| ContextVar 在同步代码里的行为              | Python 3.7+ ContextVar 同步代码同样工作，文档显式说明          |

---

## 5. 异常捕获装饰器 (T9.4 — 占位)

T9.4 计划提供 `@catch(code=..., reraise=False)` 装饰器，把函数内异常统一翻译为 `BusinessError`，并自动走 T9.3 日志。**本设计不在 T9.3 范围**，仅在 IMPLEMENTATION_PLAN_v2 占位。

---

## 6. DoD

### T9.1（已完成 v0.1）

- ✅ `codes.py` 定义 5 段 + 子域位
- ✅ `ErrorCode.of(str)` 双向反解
- ✅ 5xx 守门测试

### T9.2（已完成 v0.2）

- ✅ `MESSAGES_ZH_CN` 注册 17 个码点
- ✅ `BusinessError` + FastAPI 4 类 handler
- ✅ HTTP 422 兼容回退到 `_HTTP_422` 常量
- ✅ 集成测试 26/26 + ruff 0 warning

### T9.3（本次任务）

- ☐ `admin/logging_utils.py` 实现 `JsonLogFormatter` + `log_event` + `bind_request_context`
- ☐ `admin/app.py` 集成 JSON 输出（CLI 默认 plain，MVP json）
- ☐ `admin/errors/exceptions.py` 4 处 `logger.*` 迁移到 `log_event`
- ☐ `admin/tests/test_logging.py` 单元 + 集成测试全通过
- ☐ `admin` 全量测试 27+/27+ 通过
- ☐ `ruff check admin/logging_utils.py admin/tests/test_logging.py` 0 warning
- ☐ CHANGELOG 记录 T9.3 落地
- ☐ 提交并推送到三个 remote

### T9.4（后续）

- ☐ `@catch` 装饰器 + 测试

---

## 7. 关联文件清单

| 文件                          | 状态        | 责任                                        |
| ----------------------------- | ----------- | ------------------------------------------- |
| `admin/errors/codes.py`       | ✅ 已存在   | 码点声明 / 段与子域枚举                     |
| `admin/errors/registry.py`    | ✅ 已存在   | zh-CN 文案 + 守卫函数                       |
| `admin/errors/exceptions.py`  | ✅ 已存在   | `BusinessError` + FastAPI handler           |
| `admin/errors/__init__.py`    | ✅ 已存在   | 公共 API re-export                          |
| `admin/logging_utils.py`      | ☐ T9.3 新增 | JSON formatter + context 绑定 + helper      |
| `admin/tests/test_logging.py` | ☐ T9.3 新增 | formatter / event / context 测试            |
| `admin/app.py`                | 🔧 改       | main() 安装 JSON formatter，添加 middleware |
| `admin/tests/test_errors.py`  | ✅ 已有     | T9.1+T9.2 既有 26 测试                      |
| `CHANGELOG.md`                | 🔧 改       | 记录 T9.3                                   |
