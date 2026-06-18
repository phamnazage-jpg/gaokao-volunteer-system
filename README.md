# 高考志愿填报智能系统

[![CI](https://github.com/phamnazage-jpg/gaokao-volunteer-system/actions/workflows/ci.yml/badge.svg)](https://github.com/phamnazage-jpg/gaokao-volunteer-system/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/phamnazage-jpg/gaokao-volunteer-system/graph/badge.svg)](https://codecov.io/gh/phamnazage-jpg/gaokao-volunteer-system)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)

> 一套面向人工服务运营的高考志愿填报系统：管理后台、订单/分享/渠道同步、AI 审核链路已成形；用户端 Web 自助闭环仍在推进中。
>
> 当前真相源：`docs/CURRENT_STATE.md`
> 最终完成报告：`docs/FINAL_COMPLETION_REPORT_2026-06-13.md`
>
> 当前项目定位：人工服务运营增强系统；用户端 Web 自助闭环仅为本地 MVP/目标态，不是完整用户端 Web 自助产品。

## 📋 项目简介

本项目旨在为高考考生提供**专业、准确、规范化**的志愿填报辅助，包括：

- 方案生成（基于霍兰德兴趣模型 + 学科评估 + 个性化推荐）
- 方案检查（基于各省2026年最新政策规范的自动检查）
- 可视化报告（HTML/PDF/Markdown多格式输出）
- 信息收集（1分钟/3分钟/7步三套问卷）
- 多省份支持（已支持27个省份自动适配）

## 🏗️ 目录结构

```
gaokao-volunteer-system/
├── README.md                 # 本文件（项目说明）
├── CHANGELOG.md              # 变更日志
│
├── docs/                     # 文档
│   ├── versions/             # 版本历史
│   ├── case-studies/         # 真实案例研究
│   └── optimization-log/     # 优化过程记录
│
├── rules/                    # 规则库
│   ├── provinces/            # 省份规则（按省份）
│   ├── years/                # 年度规则（按年份）
│   └── errors/               # 错误模式库
│
├── skills/                   # Hermes Skills
│   ├── gaokao-college-advisor/   # 高考志愿填报顾问
│   ├── gaokao-spec-checker/      # 规范检查员
│   └── zhangxuefeng-skillset/    # 张雪峰风格
│
├── scripts/                  # 独立脚本
│   ├── gaokao-visual-report-v2.py    # 可视化报告V2
│   ├── gaokao-quick-3min.py          # 3分钟问卷
│   ├── gaokao-collect-info.py        # 完整收集
│   ├── gaokao-checker                # 规范检查（多省份）
│   ├── gaokao-shortlink              # T7.1 分享短链接 CLI
│   └── legacy/                       # 历史版本
│
├── data/                     # 数据
│   ├── share/                # T7 分享能力（短链接/权限策略/测试）
│   ├── templates/            # 模板
│   └── examples/             # 示例
│
└── tests/                    # 测试
    └── cases/                # 测试用例
```

## 🎯 核心组件

### 1. gaokao-college-advisor（方案生成）

- **功能**：基于考生信息生成志愿填报方案
- **特点**：霍兰德兴趣测试 + 个性化匹配 + 2025年位次数据
- **位置**：`skills/gaokao-college-advisor/`

### 2. gaokao-spec-checker（方案检查）

- **功能**：自动检查志愿方案是否符合本省最新政策
- **特点**：多省份自动适配 + 致命/严重/警告三级分类
- **位置**：`skills/gaokao-spec-checker/`
- **已支持**：27个省份（详见 `rules/provinces/`）

### 3. zhangxuefeng-skillset（张雪峰风格）

- **功能**：以张雪峰风格推荐志愿
- **特点**：直接、接地气、注重就业导向
- **位置**：`skills/zhangxuefeng-skillset/`

### 4. 独立脚本（可选补充）

- **gaokao-visual-report-v2.py**：生成HTML/PDF/MD报告
- **gaokao-quick-3min.py**：3分钟快速问卷
- **gaokao-collect-info.py**：7步完整收集
- **gaokao-checker**：多省份规范检查

## 🚀 快速开始

### 在Hermes对话中使用（推荐）

```
/skill gaokao-college-advisor
# 生成方案

/skill gaokao-spec-checker
# 检查方案
```

### 命令行使用

```bash
# 规范检查
python3 ~/.local/bin/gaokao-checker plan.txt

# 生成报告
python3 ~/.local/bin/gaokao-visual-report-v2.py

# 显示问卷
python3 ~/.local/bin/gaokao-quick-3min.py
```

### T7 分享链路安全说明

- `data/share/short_link.py` 现已使用 **PBKDF2-HMAC-SHA256** 存储分享访问密码（16B salt + 200k iterations）
- 历史短链接若仍是旧的无盐 sha256，系统会在**密码校验成功后自动迁移**到新格式
- 分享权限页与短链接 payload 继续默认隐藏 `password_hash` 等内部字段

### T6.1 管理后台 FastAPI 骨架

管理后台代码位于 `admin/`。当前已落地：服务启动、JWT 登录/鉴权、Swagger/OpenAPI、T6.2 仪表盘、T6.3 用户管理，以及 T6.4 订单管理（手工录单 / 状态流转 / CSV 导出 / 退款）。当前更准确的项目标签是“运营后台 + 人工服务增强链路”，不是完整用户端 Web 自助产品。

```bash
# 安装管理后台依赖（与测试依赖分离）
pip install -r requirements-admin.txt -r requirements-dev.txt

# 启动服务
export GAOKAO_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
python3 -m admin.app --port 8000

# 验证 Swagger / OpenAPI
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/openapi.json
xdg-open http://127.0.0.1:8000/docs
```

默认会在空库 bootstrap 一个管理员账号；生产环境必须显式设置强密码 `GAOKAO_ADMIN_PASS`（禁止 `admin123`，至少 10 位且覆盖 3 类字符）与高熵 `GAOKAO_JWT_SECRET`。首次启动后应立即轮换默认管理员密码。

### 本地一键验证（X-06）

仓库已提供 `scripts/dev-verify.sh`，用于统一执行：

- 创建/复用 `.venv`
- 安装 `requirements-admin.txt` + `requirements-dev.txt`
- 运行 `pytest` + coverage gate
- 运行 `ruff` / `mypy`

```bash
# 完整执行（默认会安装/更新依赖）
bash scripts/dev-verify.sh

# 已有依赖时可跳过安装
GAOKAO_SKIP_INSTALL=1 bash scripts/dev-verify.sh
```

### T12 交付事件最小执行链

当前 `report_ready` 不再只停留在事件表：

- 事件表：`delivery_notifications`
- 执行器：`data.notifications.dispatcher.DeliveryDispatcher`
- CLI：`python3 scripts/gaokao-delivery-dispatch.py --channel station`
- watchdog：`python3 scripts/gaokao-delivery-watchdog.py --channel station`
- runbook：`docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- systemd/cron 样例：`deploy/systemd/gaokao-delivery-*.{service,timer}` / `deploy/cron/gaokao-jobs.crontab`

最小语义：

- 交付物齐全（HTML/PDF 存在）→ `ready -> validated`
- `station` 渠道停留在 `validated`；只有 `email` 渠道真实发送成功后才进入 `delivered`
- 交付物缺失 → `failed`，并写入 `failure_reason`
- watchdog 遇到失败事件返回 exit code `2`
- 当前 `validated` 才表示“站内交付物校验通过”，`delivered` 保留给真实外部发送成功

### 数据保留期清理

- dry-run：`python3 scripts/gaokao-retention-cleanup.py --cutoff <ISO8601> --dry-run`
- apply：`python3 scripts/gaokao-retention-cleanup.py --cutoff <ISO8601>`
- 定时模式：`python3 scripts/gaokao-retention-cleanup.py --retention-days 180`
- 兼容别名：`python3 scripts/gaokao_retention_cleanup.py --retention-days 180 --dry-run`
- runbook：`docs/DELIVERY_RETENTION_OPS_RUNBOOK.md`
- 当前语义：对超过保留期的 `completed/refunded` 订单执行匿名化清理

### 备份 / 恢复最小入口

- 生成快照：`bash scripts/backup_snapshot.sh /tmp/gaokao-backups`
- 校验快照：`bash scripts/backup_verify.sh --from-backup /tmp/gaokao-backups/backup-<UTC_TIMESTAMP>`
- 直接对当前 live 数据做一次恢复演练：`bash scripts/backup_verify.sh`
- runbook：`docs/BACKUP_AND_RECOVERY_PLAN.md`
- 定时接入口径：`ops/cron/gaokao-backup.crontab.example`、`ops/systemd/gaokao-backup*.service|timer`

### crowd_db 质量汇总

- `python3 -m data.crowd_db.quality_summary --human`
- 输出 27 省 province-level `quality_level / quality_label / confidence` 汇总

### T6.7 Docker Compose 一键启动

仓库根目录已提供 `Dockerfile`、`docker-compose.yml` 与 `.env.docker.example`。默认镜像会把运行数据写入容器外部卷 `/var/lib/gaokao`，避免覆盖仓库里的 Python 包 `data/`。默认 compose 只绑定 `127.0.0.1` 且以 `dev` 模式启动，适合本机自测；正式部署前请复制 `.env.docker.example` 到 `.env` 并替换密钥/密码。

```bash
# 可选：复制示例环境变量并替换生产密钥
cp .env.docker.example .env

# 构建并启动
docker compose up --build -d

# 查看健康状态
docker compose ps
curl http://127.0.0.1:8000/health

# 停止并保留数据卷
docker compose down
```

**关键环境变量**

- `GAOKAO_JWT_SECRET`：JWT 签名密钥；生产环境至少 32 字符
- `GAOKAO_ORDERS_FERNET_KEY`：订单敏感字段加密密钥；缺失会导致订单/用户相关路由不可用
- `GAOKAO_ADMIN_PASS`：默认管理员密码；生产环境禁止 `admin123`，首次启动后应立即替换
- `GAOKAO_ADMIN_BIND`：宿主机绑定地址；默认 `127.0.0.1`，生产环境如需对外暴露请显式改成 `0.0.0.0`
- `GAOKAO_ADMIN_PORT`：宿主机暴露端口，默认 `8000`

### T8.4 渠道失败兜底（巡检 + 人工补录）

当前巡检事实源以 `xianyu` 的 webhook/poller 表为准；其他渠道先视为“人工补录模板复用”。当 `xianyu` 链路异常时，先执行巡检，再决定是否走人工补录：

```bash
# 巡检（0=ok, 1=warn, 2=critical）
python3 scripts/gaokao-channel-fallback --db data/orders.db check --source xianyu --human

# 打印人工兜底模板
python3 scripts/gaokao-channel-fallback --db data/orders.db manual-template --source xianyu --human
```

完整值班流程见 `docs/T8-4-fallback-sop.md`。

### T6.2 仪表盘（一站式数据统计）

T6.1 阶段 `/api/stats/orders` 为占位端点（`_stub=True`）。T6.2 接入真实 SQL 聚合，并新增一站式仪表盘端点 `/api/stats/dashboard` 与极简页面 `/dashboard`。

**端点**

| 方法 | 路径                   | 鉴权 | 说明                                        |
| ---- | ---------------------- | ---- | ------------------------------------------- |
| GET  | `/api/stats/dashboard` | JWT  | 一站式仪表盘 payload（汇总 + 分布 + 趋势）  |
| GET  | `/api/stats/orders`    | JWT  | 订单维度统计（沿用 T6.1 stub 字段名）       |
| GET  | `/dashboard`           | 公开 | 极简仪表盘页面（登录后拉取 dashboard JSON） |

**配置**

| 环境变量                | 默认值                 | 说明                                      |
| ----------------------- | ---------------------- | ----------------------------------------- |
| `GAOKAO_DB_PATH`        | `data/orders/admin.db` | admin_users 所在 DB                       |
| `GAOKAO_ORDERS_DB_PATH` | `data/orders.db`       | orders 所在 DB（与 `data.orders.*` 共享） |

**关键口径**

- **收入 (revenue_cents)** = `paid` / `serving` / `delivered` / `completed` 四态订单的 `amount_cents` 累计值；`pending`（未付款）与 `refunded`（已退款）不计入。
- **趋势桶粒度** = 日（UTC，`YYYY-MM-DD`）。
- **0 填充** = 窗口内的"无订单日"也返回 0 点，前端拿到稠密序列。
- **不读 PII** = 统计路径只触碰 `amount_cents` / `status` / `source` / `service_version` / `created_at`。

**响应示例**（`/api/stats/dashboard`）

```json
{
  "summary": {
    "total_orders": 6, "total_revenue_cents": 100000, "total_users": 1,
    "orders_today": 3, "orders_7d": 4, "orders_30d": 5,
    "revenue_today_cents": 20000, "revenue_7d_cents": 70000, "revenue_30d_cents": 100000
  },
  "by_status":         {"pending": 2, "paid": 1, "serving": 1, "delivered": 0, "completed": 1, "refunded": 1},
  "by_source":         {"xianyu": 3, "wechat": 1, "web": 1, "school": 1},
  "by_service_version":{"audit": 0, "basic": 6, "standard": 0, "premium": 0},
  "trends": {
    "today": [{"date": "2026-06-12", "orders": 3, "revenue_cents": 20000}],
    "7d":    [{"date": "2026-06-06", "orders": 0, "revenue_cents": 0}, ... 共 7 个点 ...],
    "30d":   [{"date": "2026-05-14", "orders": 0, "revenue_cents": 0}, ... 共 30 个点 ...]
  },
  "generated_at": "2026-06-12T16:30:00+00:00"
}
```

**本地联调**

```bash
# 1) 启动 FastAPI 服务
export GAOKAO_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
python3 -m admin.app --port 8000

# 2) 验证 JSON 端点
curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'

# 3) 打开极简页面（页面内可直接登录并加载）
xdg-open http://127.0.0.1:8000/dashboard
```

### T6.3 用户管理（列表 / 详情 / 脱敏 / 搜索）

T6.3 在 `orders` 表之上补齐用户管理读路径：`/api/admin/users` 返回按用户聚合后的列表，`/api/admin/users/{user_key}` 返回该用户的订单详情。默认展示形态为脱敏字段，便于运营核对且不直接暴露完整 PII。

**端点**

| 方法 | 路径                          | 鉴权 | 说明                                             |
| ---- | ----------------------------- | ---- | ------------------------------------------------ |
| GET  | `/api/admin/users`            | JWT  | 用户列表；支持 `q` 搜索、`limit` / `offset` 分页 |
| GET  | `/api/admin/users/{user_key}` | JWT  | 用户详情；返回该用户的脱敏订单明细               |

**聚合口径**

- 优先按 `customer_phone_hash` 聚合同一用户；无手机号时退回 `customer_wechat` 指纹；再退回订单号，避免孤立记录丢失。
- 搜索支持姓名 / 手机号 / 微信 / 订单号等常见运营核对字段。
- 返回的 `customer_name` / `candidate_name` / `customer_phone` / `candidate_id_card` 默认走脱敏展示。

### T6.4 订单管理（录单 / 状态流转 / 导出 / 退款）

T6.4 在已有 `data/orders` DAO 与状态机之上补齐管理后台写路径。运营人员现在可以通过 FastAPI 直接手工录单、更新业务字段、推进状态、导出 CSV，以及将订单推进到 `refunded`。

**端点**

| 方法  | 路径                 | 鉴权 | 说明                                                    |
| ----- | -------------------- | ---- | ------------------------------------------------------- |
| GET   | `/api/orders`        | JWT  | 订单列表；支持 `status` / `source` / `limit` / `offset` |
| GET   | `/api/orders/export` | JWT  | CSV 导出；默认脱敏敏感字段                              |
| GET   | `/api/orders/{id}`   | JWT  | 订单详情；附带状态历史与可流转下一状态                  |
| POST  | `/api/orders`        | JWT  | 手工录单；`external_id` 可空                            |
| PATCH | `/api/orders/{id}`   | JWT  | 业务字段更新、状态流转、退款                            |

**约束**

- 写路径复用 `OrdersDAO`：业务字段更新走 `update()`，状态变化强制走 `transition_status()`，不绕过 6 态状态机。
- 导出默认脱敏：`customer_phone` / `candidate_id_card` 在 CSV 中也不返回明文，避免把完整 PII 直接写入浏览器下载文件。
- 退款不主动调用第三方渠道 API；管理后台只把本地订单推进为 `refunded`，与 `docs/CHANNEL_INTEGRATION.md` 的合规边界一致。

## 📊 已支持省份

| 模式       | 省份数 | 列表                                                                                 |
| ---------- | :----: | ------------------------------------------------------------------------------------ |
| 院校专业组 |   14   | 湖南、广东、湖北、安徽、江西、甘肃、黑龙江、江苏、福建、广西、北京、上海、天津、海南 |
| 专业+学校  |   8    | 浙江、山东、河北、重庆、辽宁、贵州、青海、吉林                                       |
| 传统       |   5    | 河南、四川、新疆、云南、西藏                                                         |

**总计27省，可自动识别省份并加载对应规则**

## 📝 开发规范

### 代码规范

- Python：PEP 8 + 中文注释
- Markdown：清晰标题层次
- 命名：lowercase-hyphen 或 lowercase_underscore

### 文档规范

- 每个组件有 README
- 关键决策记录到 `docs/case-studies/`
- 优化过程记录到 `docs/optimization-log/`
- 错误模式记录到 `rules/errors/`

### 测试规范

- 每个新功能要有测试用例
- 测试用例放在 `tests/cases/`
- 错误模式要加入 `rules/errors/`

## 🔄 持续优化

### 优化日志

详见 `docs/optimization-log/`，记录每次优化的：

- 优化点
- 改进效果
- 用户反馈
- 后续计划

### 已知不足

- 27省中的部分规则可能不准确
- 2026年招生计划待官方公布
- 部分省份特殊批次未覆盖
- 算法精度有待提高

### 未来规划

详见 `docs/optimization-log/future-plan.md`

## 📚 相关资源

- 阳光高考：https://gaokao.chsi.com.cn/
- 湖南省教育考试院：http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/
- 各省教育考试院（详见各省份规则文档）

## 📄 版权信息

本项目为个人开发项目，仅供学习参考使用。

实际志愿填报请以**各省教育考试院**官方信息为准。

---

**生成时间**：2026年6月11日  
**当前版本**：v2.0
