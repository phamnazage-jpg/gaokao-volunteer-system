# 架构设计（当前实现视角）

本文档描述 2026-06-13 当前仓库中已经落地、可验证的系统架构。

一句话定位：

- 这不是“完整用户端 Web 自助闭环产品”
- 这是一个“管理后台 + 订单/分享/渠道同步 + AI 审核链路”的可运行系统

---

## 1. 架构总览

```text
┌──────────────────────────────────────────────────────────────┐
│                      接入与交互层                            │
│  Hermes Skills   CLI Scripts   Admin FastAPI   Share Page   │
└───────────────┬───────────────┬───────────────┬──────────────┘
                │               │               │
┌───────────────▼──────────────────────────────────────────────┐
│                      应用服务层                              │
│  AI审核编排   订单服务/状态机   分享权限   渠道同步   统计聚合 │
└───────────────┬──────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────┐
│                       数据与持久化层                         │
│  SQLite(admin/orders/cases/share) + JSON crowd_db + 模板/静态 │
└──────────────────────────────────────────────────────────────┘
```

核心结论：

- 管理后台与人工服务交付链已经形成主链
- AI 审核从解析 → 规则检查 → 扎堆检测 → 报告输出已经形成统一入口
- 分享、渠道同步、订单状态机都已有独立模块与测试
- 用户端 Web 自助注册/下单/支付/资料填写/站内交付主链仍缺失

---

## 2. 分层设计

### 2.1 接入与交互层

当前存在 4 类入口：

1. Hermes Skills

- `skills/gaokao-college-advisor/`
- `skills/gaokao-spec-checker/`
- `skills/gaokao-audit/`

2. CLI

- `scripts/gaokao-quick-3min.py`
- `scripts/gaokao-order-manager`
- `scripts/gaokao-data-trace`
- `scripts/gaokao-channel-fallback`

3. 管理后台 HTTP API

- `admin/app.py`
- `admin/routes/*`

4. 极简页面

- `admin/static/dashboard.html`
- `GET /dashboard`
- `GET /s/{code}` 分享页

设计意图：

- 人工顾问/运营同学优先走后台与 CLI
- Hermes 对话场景优先走 Skills
- 对外公开访问当前仅限分享页，不等同于完整用户前台

---

### 2.2 应用服务层

#### A. AI 审核链路

主要模块：

- `skills/gaokao-audit/scripts/plan_parser.py`
- `skills/gaokao-audit/scripts/checker_integration.py`
- `skills/gaokao-audit/scripts/audit_service.py`
- `skills/gaokao-audit/scripts/report_generator.py`
- `skills/gaokao-audit/scripts/audit_cli.py`
- `data/crowd_db/crowd_detector.py`
- `data/crowd_db/risk_report.py`

处理链路：

```text
方案文本/PDF提取/OCR
  → 方案解析
  → 省份规则检查
  → 扎堆风险检测
  → 风险/问题聚合
  → HTML/PDF/JSON 报告输出
```

说明：

- 当前 AI 审核主链已经不是“只有零散脚本”
- `audit_cli.py` 是统一编排入口
- T5.1 已用端到端测试覆盖“输入方案 → 输出 PDF/JSON 审核报告”主链

#### B. 订单与交付链路

主要模块：

- `data/orders/models.py`
- `data/orders/dao.py`
- `data/orders/state_machine.py`
- `data/orders/cli.py`
- `admin/routes/orders.py`

职责拆分：

- `models.py`：订单数据模型
- `dao.py`：SQLite 持久化、查询、事务、历史记录
- `state_machine.py`：状态合法性约束
- `cli.py` / `routes/orders.py`：两种入口，共用同一底层规则

状态机：

```text
pending → paid → serving → delivered → completed
                    └──────────────→ refunded
```

关键原则：

- 不允许绕过状态机直接改状态
- HTTP 与 CLI 写路径都应落到 DAO + 状态机
- 敏感字段默认脱敏展示

#### C. 分享能力

主要模块：

- `data/share/short_link.py`
- `data/share/permission.py`
- `admin/share_page.py`
- `admin/routes/ui.py`

能力：

- 短链接生成与解析
- `read/comment/edit/admin` 权限模型
- 报告字段裁剪与脱敏
- 公开分享页渲染

设计定位：

- 服务于“人工交付后的分享/查看”
- 不是完整协作式前台产品

#### D. 渠道同步

主要模块：

- `data/channel_sync/webhook_server.py`
- `data/channel_sync/xianyu_adapter.py`
- `data/channel_sync/poller.py`
- `data/channel_sync/audit.py`
- `data/channel_sync/monitor.py`

能力：

- 闲鱼 webhook 接单
- poller 兜底补偿
- webhook 审计日志
- 渠道健康巡检与人工 fallback 模板

设计原则：

- 自动接单优先
- 审计留痕
- 异常时可回落到人工补录

#### E. 后台统计与运营视图

主要模块：

- `admin/stats.py`
- `admin/routes/stats.py`
- `admin/routes/users.py`
- `admin/routes/cases.py`
- `admin/routes/meta.py`

能力：

- 仪表盘汇总
- 订单/来源/服务版本分布
- 时间趋势
- 用户列表与案例管理
- 前端枚举元数据输出

---

### 2.3 数据与持久化层

#### SQLite

1. 管理后台库

- 默认：`data/orders/admin.db`
- 内容：管理员、后台业务表、cases 等

2. 订单库

- 默认：`data/orders.db`
- 内容：订单主表、状态历史、渠道同步相关辅助表

3. 分享/短链数据

- 由 `data/share/short_link.py` 管理，实际落在 SQLite

#### JSON / Markdown 数据

1. crowd_db

- 路径：`data/crowd_db/`
- 内容：院校推荐、来源、置信度、年份等

2. 规则与案例文档

- 路径：`rules/`、`docs/`、`product/`

#### 模板与静态资源

- 审核报告模板：`skills/gaokao-audit/templates/audit_report.html`
- 分享页/后台静态资源：`admin/static/*`

---

## 3. 核心运行链路

### 3.1 人工服务主链（当前已落地）

```text
渠道线索/人工录单
  → 订单入库
  → 顾问生成方案
  → AI审核
  → PDF/JSON/方案文件归档
  → 订单推进到 delivered/completed
  → 可选分享页分发
```

这是当前仓库最成熟、最贴近真实运行的主链。

### 3.2 后台运营主链（当前已落地）

```text
管理员登录
  → 查看仪表盘/用户/订单/案例
  → 人工录单或补录
  → 状态流转/退款/导出
  → 跟踪渠道与交付情况
```

### 3.3 数据溯源查询链（当前已落地）

```text
输入院校名
  → crowd_db 加载各省数据
  → 匹配学校/专业
  → 返回来源、年份、置信度、分数段、替代建议
```

### 3.4 性能验证链（T5.2 已落地）

```text
quick-3min 解析+总结+推荐
  → 100 次基准执行
  → 断言总耗时 < 5s

admin FastAPI
  → Locust 10 并发压测
  → 断言聚合成功率 > 95%
```

---

## 4. 当前未落地主链

以下能力仍不应被本文档误描述为“已完成”：

1. 用户端 Web 前台

- 用户注册/登录
- 用户自主下单/支付
- 站内资料填写
- 用户自助查看报告/订单进度

2. 完整产品化闭环

- 面向最终考生/家长的独立前端应用
- 完整邮件/站内消息交付系统
- 自助支付后的自动任务编排闭环

因此，当前系统真实定位应是：

- 内部运营与人工服务增强系统：已成形
- 面向最终用户的完整产品：未完成

---

## 5. 安全与边界

### 5.1 已有防护

- JWT 鉴权
- 生产环境 JWT 弱密钥阻断
- 管理员弱口令在 prod 阻断
- 订单敏感字段加密存储
- 默认脱敏输出
- 分享页权限分级

### 5.2 已知风险（截至当前评审）

- 渠道 webhook 的 `X-Forwarded-For` 信任边界仍需收紧
- 登录接口节流/锁定能力不足
- CI 不能完整代表 clean env 下的后台可构建性
- 类型门禁与覆盖率门禁仍未完全闭环

这些属于“工程质量与安全债”，不改变主链已存在的事实，但影响生产可交付性评级。

---

## 6. 部署形态

### 6.1 本地运行

```bash
pip install -r requirements-admin.txt -r requirements-dev.txt
export GAOKAO_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
python3 -m admin.app --port 8000
```

### 6.2 Docker Compose

已提供：

- `Dockerfile`
- `docker-compose.yml`
- `.env.docker.example`

适用场景：

- 本机自测
- 单机部署验证

不应误解为：

- 已具备完整云原生、多副本、自动扩缩容架构

---

## 7. 真相源优先级

当文档与实现冲突时，按以下顺序判断：

1. 代码与实跑结果
2. OpenAPI / CLI `--help`
3. 测试文件（尤其 `tests/test_t5_e2e_workflows.py`、`tests/test_t5_performance.py`）
4. README / CHANGELOG
5. 本文档
6. 历史评审/历史计划文档

---

## 8. 验证命令

### 8.1 启动后台

```bash
python3 -m admin.app --port 8000
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/openapi.json
```

### 8.2 复核 T5 主链

```bash
python3 -m pytest tests/test_t5_e2e_workflows.py tests/test_t5_performance.py -q
```

### 8.3 复核后台接口存在性

```bash
python3 -m pytest admin/tests/test_routes.py admin/tests/test_routes_orders.py admin/tests/test_routes_stats_dashboard.py -q
```
