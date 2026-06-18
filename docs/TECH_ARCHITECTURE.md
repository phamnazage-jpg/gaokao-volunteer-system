# 技术架构设计

## 高考志愿填报智能系统 v2.1

**版本**: v2.1
**状态**: 已落地（持续演进）
**最后更新**: 2026-06-13

> 说明：本文同时描述两类内容：
>
> 1. Current：当前已落地的后台/API/CLI/Skills/Webhook 能力
> 2. Target：尚未落地的用户端 Web/H5、自助支付、自助交付等目标能力
>    阅读时请以 `docs/CURRENT_STATE.md` 为当前真相源。
>
> 当前项目定位：人工服务运营增强系统；用户端 Web 自助闭环仅为本地 MVP/目标态，不应把 Target 能力误读为当前已上线能力。

---

## 1. 架构总览

### 1.1 分层架构

#### Current（已落地）

```
┌─────────────────────────────────────────────────────────────────┐
│                 用户接入层（闲鱼 / 微信 / 管理后台）            │
├─────────────────────────────────────────────────────────────────┤
│   FastAPI Admin / Share / Portal / CLI / Skills / Webhook      │
├─────────────────────────────────────────────────────────────────┤
│   订单管理 / AI审核 / 渠道同步 / 分享权限 / 通知与审计           │
├─────────────────────────────────────────────────────────────────┤
│   SQLite（orders/admin/share） + LocalFS + 规则/专业目录数据     │
└─────────────────────────────────────────────────────────────────┘
```

#### In Progress（本地 MVP / 未完成线上验收）

- 用户端前台入口、套餐页、portal 向导页、状态页
- `mock` / `alipay_sim` / `alipay` 三层支付代码链
- 站内交付、邮件通知、删除/匿名化、备份恢复本地验证链

#### Target（未落地 / 不可对外承诺）

- 用户端 Web/H5 自助下单、真实支付、资料填写、自动交付闭环
- 线上支付 acceptance、公网回调、备案域名、真实告警与运维值班接入
- 更完整客户端或自助 SaaS 化能力

当前/目标说明：

- Current（已落地）：Admin API、CLI、Skills、Webhook、分享页、管理后台、订单/用户/案例/统计、AI审核链路。
- Target（未完全落地）：用户端 Web/H5、自助支付、自助资料填写、站内交付、客户端。

### 1.2 核心设计原则

| 原则           | 说明                            |
| -------------- | ------------------------------- |
| **本地优先**   | 默认本地存储/处理，云端可选     |
| **简单可执行** | 不引入复杂中间件，Python + 文件 |
| **单一来源**   | 27省规则库为唯一政策真源        |
| **数据脱敏**   | 敏感字段加密/脱敏处理           |
| **可审计**     | 所有操作可追溯                  |
| **可扩展**     | 模块化设计，易于新增省份/功能   |

---

## 2. 技术栈选型

### 2.1 当前(v2.0)技术栈

```
├── 核心语言
│   └── Python 3.10+
│
├── 现有模块（已实现）
│   ├── gaokao-college-advisor/     # 基础顾问Skill
│   ├── gaokao-spec-checker/         # 规范检查V2
│   ├── zhangxuefeng-skillset/        # 张雪峰风格Skill
│   └── gaokao-counselor-long/        # 龙老师Skill
│
├── 数据处理
│   ├── 省份规则:  hardcoded in scripts
│   ├── 院校数据:  inline text/template
│   └── 用户档案:  临时文件存储
│
├── 报告输出
│   ├── Markdown (简单)
│   ├── HTML (weasyprint)
│   └── PDF (weasyprint)
│
└── 命令行入口
    ├── gaokao-checker
    ├── gaokao-quick-3min.py
    └── gaokao-visual-report-v2.py
```

### 2.2 v2.1新增技术栈

```
├── AI审核服务（当前已落地部分）
│   ├── 方案输入: JSON plan
│   ├── 政策检查: 省份规则上限 / 结构约束
│   ├── 专业目录检查: majors catalog active / deprecated / missing
│   └── 报告输出: JSON payload（非综合评分）
│
├── 反扎堆检测（Target / 未接入当前 audit run）
│   ├── 推荐库: JSON文件 (data/crowd_db/)
│   ├── 比对算法: Python fuzzy match
│   └── 风险评估: 规则引擎
│
├── 数据溯源
│   ├── 数据标注: extend data model
│   ├── 置信度: 元数据字段
│   └── 来源链接: URL字段
│
└── 订单管理（v2.1）
    ├── 存储: SQLite (data/orders.db)
    ├── API: 简单的CRUD
    └── Web: 暂用管理后台CLI
```

### 2.3 技术选型原则

| 维度        | 选择          | 理由                   |
| ----------- | ------------- | ---------------------- |
| **语言**    | Python 3.10+  | 现有代码基础，无需切换 |
| **存储**    | SQLite + 文件 | 本地优先，零配置       |
| **Web框架** | FastAPI       | 轻量、自动文档、异步   |
| **PDF**     | weasyprint    | 已用，成熟方案         |
| **前端**    | 待定          | 2027年Q2再决定         |
| **部署**    | 单机          | 用户基数小，无需集群   |

---

## 3. 核心模块设计

### 3.1 AI审核服务（49元版）

#### 模块结构

```
skills/gaokao-audit/
├── SKILL.md                    # 角色定义
├── scripts/
│   ├── audit_service.py        # 主服务
│   ├── plan_parser.py          # 方案解析（PDF/文本）
│   ├── crowd_detector.py       # 扎堆检测
│   ├── checker_integration.py  # 调用规范检查
│   ├── report_generator.py     # 报告生成
│   └── data/
│       └── crowd_db.json       # 大厂AI推荐数据库
├── templates/
│   └── audit_report.html       # 审核报告模板
├── examples/
│   └── audit_demo.md
└── tests/
    └── test_audit.py
```

#### 关键数据流

```
用户上传方案（PDF/文本/截图）
    ↓
plan_parser.py 解析
    ↓
提取：考生信息 + 院校列表 + 专业组
    ↓
checker_integration.py 调用规范检查
    ↓
crowd_detector.py 检测扎堆
    ↓
综合生成审核结果
    ↓
report_generator.py 输出PDF
    ↓
交付用户
```

#### 关键接口

```python
# 当前 audit run 接口（已落地）
def audit_plan(province: str, plan: dict[str, Any]) -> dict[str, object]:
    """
    当前只执行两类真实检查：

    1. 省份规则：例如 max_volunteers
    2. 专业目录状态：missing / deprecated / non-active

    返回：
        {
            'province': str,
            'overall_pass': bool,
            'issues': list[dict],
            'checks_executed': ['province_rules', 'majors_catalog'],
            'checks_not_executed': ['crowd_risk', 'overall_score'],
        }
    """
```

---

### 3.2 反扎堆检测

#### 数据模型

```python
# 大厂AI推荐数据库
{
    "湖南省": {
        "578分": {  # 分数段
            "院校": [
                {
                    "name": "长沙理工大学",
                    "major": "会计学",
                    "frequency": 4,  # 4个大厂AI都推荐
                    "risk_level": "high",  # high/medium/low
                    "predicted_increase": 18,  # 预测分数线上涨
                    "alternatives": [  # 替代推荐
                        {"name": "湖南工商大学", "major": "会计学", "score": 95},
                        {"name": "湖北经济学院", "major": "财务管理", "score": 92},
                    ]
                }
            ]
        }
    }
}
```

#### 检测算法

```python
def detect_crowd_risk(plan: List[Volunteer], user_score: int) -> List[CrowdRisk]:
    """
    检测扎堆风险

    1. 遍历用户方案中的每条志愿
    2. 在 crowd_db.json 中查询该院校是否被大厂AI高频推荐
    3. 根据 frequency 和 predicted_increase 评估风险等级
    4. 返回风险列表 + 替代方案
    """
```

#### 数据来源策略

- **初始数据**: 手动整理6-8月期间各AI平台公开推荐
- **更新机制**: 每周手动更新（避免爬虫合规风险）
- **数据规模**: 预计每省50-100条热门推荐

---

### 3.3 数据溯源

#### 数据模型扩展

```python
# 院校数据扩展
class College:
    name: str
    # ... 现有字段

    # 新增溯源字段
    source: str              # "湖南省教育考试院" / "阳光高考" / ...
    source_url: str          # 原始数据链接
    source_type: str         # "official" / "report" / "estimated"
    data_year: int           # 数据年份
    confidence: float        # 置信度 0-1
    last_updated: date       # 最后更新日期
    verified_by: str         # 验证人
```

#### 报告展示

```
推荐院校：湖南工商大学
─────────────────────────────
【2025年录取数据】
✓ 最低分：565分
  来源：湖南省教育考试院
  链接：http://jyt.hunan.gov.cn/...
  数据日期：2025-08-15
  置信度：★★★★★ (官方)

✓ 位次：28,500名
  来源：湖南省教育考试院
  链接：http://jyt.hunan.gov.cn/...
  数据日期：2025-08-15
  置信度：★★★★★ (官方)

【专业满意度】⭐⭐⭐⭐☆ 4.2/5
  来源：阳光高考平台
  链接：https://gaokao.chsi.com.cn/...
  样本量：234位在校生
  置信度：★★★★☆ (官方平台)

【就业数据】
⚠️ 就业率：92%
  来源：湖南工商大学2024年就业质量报告
  数据日期：2024-12-30
  置信度：★★★☆☆ (学校自报)

⚠️ 平均薪资：5800元/月
  来源：同上
  数据日期：2023届
  置信度：★★★☆☆ (学校自报)

─────────────────────────────
📌 以上数据为2025年，2026年实际以官方公布为准
```

---

### 3.4 订单管理

#### 数据模型

```python
class Order:
    id: str                     # 订单号
    source: str                 # 'xianyu' | 'wechat' | 'web' | 'school'
    external_id: str            # 外部订单号（闲鱼订单号/微信备注）
    service_version: str        # 'audit' | 'basic' | 'standard' | 'premium'
    amount: int                 # 金额（分）
    status: str                 # 'pending' | 'paid' | 'serving' | 'delivered' | 'completed' | 'refunded'

    # 客户信息
    customer_name: str          # 脱敏存储
    customer_phone: str         # 加密存储
    customer_wechat: str

    # 考生信息
    candidate_name: str         # 脱敏存储
    candidate_province: str
    candidate_score: int
    candidate_rank: int
    candidate_subjects: List[str]
    candidate_interests: str
    candidate_strong_subjects: str
    candidate_weak_subjects: str
    candidate_family: str

    # 服务信息
    assigned_consultant: str    # 分配给谁
    plan_file: str              # 方案文件路径
    audit_report: str           # 审核报告路径
    pdf_path: str               # PDF报告路径

    # 时间戳
    created_at: datetime
    paid_at: datetime
    started_at: datetime
    delivered_at: datetime
    completed_at: datetime

    # 元数据
    notes: str
    tags: List[str]
    upgrade_from: str           # 升级来源订单
```

#### API设计

```python
# REST API (FastAPI)
POST   /api/orders                 # 创建订单
GET    /api/orders                 # 列表
GET    /api/orders/{id}            # 详情
PATCH  /api/orders/{id}            # 更新
POST   /api/orders/{id}/pay        # 标记支付
POST   /api/orders/{id}/deliver    # 标记交付
POST   /api/orders/{id}/refund     # 退款
POST   /api/orders/{id}/upgrade    # 升级订单
GET    /api/orders/stats           # 统计
```

---

## 4. 数据架构

### 4.1 目录结构

```
gaokao-volunteer-system/
├── data/                          # 数据目录
│   ├── colleges/                  # 院校数据
│   │   ├── hunan.json            # 湖南省院校
│   │   ├── zhejiang.json         # 浙江省院校
│   │   └── ...
│   ├── rules/                     # 规则数据
│   │   ├── provinces.json        # 省份规则汇总
│   │   └── errors.json           # 错误模式
│   ├── crowd_db/                  # 扎堆检测数据库
│   │   ├── hunan.json            # 湖南大厂AI推荐
│   │   └── ...
│   ├── sources.json              # 数据溯源元数据
│   └── orders.db                 # 订单数据库(SQLite)
│
├── skills/
│   ├── gaokao-audit/              # 新增: AI审核Skill
│   ├── gaokao-college-advisor/
│   ├── gaokao-spec-checker/
│   ├── gaokao-counselor-long/
│   └── zhangxuefeng-skillset/
│
├── scripts/                       # 命令行工具
│   ├── gaokao-checker
│   ├── gaokao-audit               # 新增: AI审核CLI
│   ├── gaokao-crowd-detector      # 新增: 扎堆检测CLI
│   └── ...
│
├── tests/                         # 测试
│   ├── test_audit.py             # 新增
│   ├── test_crowd.py             # 新增
│   ├── test_data_trace.py        # 新增
│   └── test_orders.py            # 新增
│
└── docs/                          # 文档
    ├── ARCHITECTURE.md            # 架构文档
    ├── API.md
    └── plans/                     # 实施计划
```

### 4.2 数据流图

```
┌─────────────────┐
│  用户咨询数据    │ (省份、分数、选科等)
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  会话状态管理    │◄────│ 27省规则库        │
│  (in-memory)     │     │ (PROVINCE_RULES)  │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  方案生成引擎                                │
│  - 兴趣匹配 (RIASEC)                         │
│  - 学科强弱匹配                              │
│  - 家庭情况匹配                              │
│  - 反扎堆检测                                │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  规范检查器V2   │ ◄── 调用 ──► 错误模式库
│  (自动)         │                (15种)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  报告生成        │ ──► PDF/HTML/Markdown
│  (含数据溯源)   │
└─────────────────┘
```

---

## 5. 性能设计

### 5.1 性能目标

| 指标         | 目标值  | 当前 |
| ------------ | ------- | ---- |
| 单次咨询响应 | < 5秒   | ✅   |
| 方案生成时间 | < 10秒  | ✅   |
| 审核报告生成 | < 30秒  | 🆕   |
| 报告PDF生成  | < 5秒   | ✅   |
| 并发支持     | 10用户  | ⏳   |
| 数据库查询   | < 100ms | ✅   |

### 5.2 优化策略

- **缓存**: 规则库内存常驻
- **异步**: I/O密集操作异步化
- **批处理**: 批量PDF生成
- **CDN**: 静态资源（暂不需要）

---

## 6. 安全设计

### 6.1 数据安全

| 数据     | 处理方式         | 存储位置 |
| -------- | ---------------- | -------- |
| 手机号   | AES加密          | SQLite   |
| 姓名     | 脱敏显示         | SQLite   |
| 订单内容 | 明文（业务需要） | SQLite   |
| 支付信息 | 不存储           | -        |
| PDF报告  | 文件存储         | LocalFS  |

### 6.2 访问控制

```python
# 权限设计
class Role:
    SUPER_ADMIN = "super_admin"      # 全部权限
    PRODUCT = "product"              # 产品经理
    OPERATIONS = "operations"         # 运营
    ANALYST = "analyst"              # 数据分析师
    CONSULTANT = "consultant"         # 顾问
    CUSTOMER_SERVICE = "cs"          # 客服

# 资源权限
PERMISSIONS = {
    Role.SUPER_ADMIN: ["*"],
    Role.PRODUCT: ["orders:read", "users:read", "data:export"],
    Role.OPERATIONS: ["orders:read", "orders:write", "users:read"],
    # ...
}
```

### 6.3 操作审计

```python
class AuditLog:
    user_id: str
    action: str             # "view_order" / "create_order" / ...
    resource_type: str      # "order" / "user" / "data"
    resource_id: str
    timestamp: datetime
    ip_address: str
    details: dict
```

---

## 7. 部署架构

### 7.1 v2.1 部署方案（本地优先）

```
┌─────────────────────────────────────────┐
│            用户本地机器                    │
├─────────────────────────────────────────┤
│                                         │
│  ┌────────────────────────────────┐    │
│  │  Python Runtime (3.10+)        │    │
│  │  ┌──────────────────────────┐  │    │
│  │  │ FastAPI Server            │  │    │
│  │  │ (管理后台 + API)          │  │    │
│  │  │ Port: 8000                │  │    │
│  │  └──────────────────────────┘  │    │
│  │  ┌──────────────────────────┐  │    │
│  │  │ Hermes Skills             │  │    │
│  │  │ (gaokao-* 系列)           │  │    │
│  │  └──────────────────────────┘  │    │
│  └────────────────────────────────┘    │
│  ┌────────────────────────────────┐    │
│  │  SQLite Database                │    │
│  │  (data/orders.db)               │    │
│  └────────────────────────────────┘    │
│  ┌────────────────────────────────┐    │
│  │  File Storage                   │    │
│  │  (data/reports/, data/audits/) │    │
│  └────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

### 7.2 数据备份

- **自动备份**: 每日定时打包 `data/` 目录
- **Git版本**: 规则库和错误模式库Git管理
- **异地**: 3个远程仓库同步（已完成）

---

## 8. 集成设计

### 8.1 Skills间的调用关系

```
gaokao-counselor-long (主)
    ├── 调用 gaokao-college-advisor (方案生成)
    ├── 调用 gaokao-spec-checker (规范检查)
    ├── 调用 gaokao-audit (新: AI审核) 🆕
    └── 调用反扎堆检测模块 🆕

gaokao-audit (新)
    ├── 调用 gaokao-spec-checker
    ├── 调用反扎堆检测
    └── 生成审核报告

数据溯源模块
    ├── 院校数据扩展
    └── 报告展示增强
```

### 8.2 命令行集成

```bash
# 现有
gaokao-checker plan.txt                  # 规范检查
gaokao-visual-report-v2.py              # 生成报告
gaokao-quick-3min.py                     # 问卷

# 新增
gaokao-audit plan.pdf                    # AI方案审核 🆕
gaokao-crowd-detect volunteer.json       # 扎堆检测 🆕
gaokao-data-trace college.json          # 数据溯源查询 🆕
gaokao-order-manager                      # 订单管理CLI 🆕
```

---

## 9. 监控设计

### 9.1 业务指标

| 指标           | 计算方式  | 告警阈值 |
| -------------- | --------- | -------- |
| 方案生成成功率 | 成功/总数 | <90%     |
| 审核报告生成   | 成功/总数 | <95%     |
| 扎堆检测准确率 | 抽样核对  | <85%     |
| 订单创建成功率 | 成功/总数 | <95%     |

### 9.2 技术指标

| 指标        | 监控方式 | 告警阈值 |
| ----------- | -------- | -------- |
| API响应时间 | 日志统计 | >5s      |
| 错误率      | 日志统计 | >5%      |
| 数据库大小  | 文件大小 | >1GB     |

---

## 10. 演进路径

### Phase 1: v2.1 (2026年6-7月) - 当前

- AI审核服务
- 反扎堆检测
- 数据溯源增强
- 订单管理基础

### Phase 2: v2.2 (2026 Q3-Q4) - 下一阶段

- Web后台界面
- 数据自动化对接
- 案例库完善

### Phase 3: v2.3 (2027 Q1-Q2) - Web端上线

- 用户端Web界面
- 完整支付集成
- 多端PWA

### Phase 4: v3.0 (2027 Q3+) - 规模化

- 服务端部署
- 高级智能推荐
- 商业化完善

---

## 11. 技术决策记录

### TD001: 选用SQLite而非PostgreSQL

**决策**: SQLite
**理由**:

- 本地优先架构
- 零配置、零维护
- 用户基数小（<10万）
- 后续可平滑迁移到PostgreSQL

### TD002: FastAPI作为Web框架

**决策**: FastAPI
**理由**:

- Python生态
- 自动API文档
- 异步支持
- 性能良好

### TD003: 数据溯源本地JSON存储

**决策**: JSON文件
**理由**:

- 简单查询
- 易于编辑
- 无数据库依赖
- 便于Git版本管理

### TD004: 扎堆数据库手动维护

**决策**: 人工整理
**理由**:

- 避免爬虫合规风险
- 数据准确性高
- 维护成本可接受
- 后续可半自动化

---

**下一步**: 查看 [实施计划](IMPLEMENTATION_PLAN_v2.md)
