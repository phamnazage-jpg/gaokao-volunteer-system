# 实施计划

## v2.1 详细开发任务分解

**版本**: v2.1
**目标**: 实现AI审核、反扎堆检测、数据溯源、订单管理
**时间**: 2026年6月15日 - 7月15日（30天）
**方法**: TDD + 频繁提交

---

## 总览

### 4个核心开发任务

| 任务                           | 工时 | 优先级 | 状态 |
| ------------------------------ | :--: | :----: | :--: |
| T1: AI审核服务（49元版）⭐核心 | 10天 |   P0   |  📋  |
| T2: 反扎堆检测功能             | 5天  |   P0   |  📋  |
| T3: 数据溯源功能               | 5天  |   P1   |  📋  |
| T4: 订单管理基础               | 5天  |   P1   |  📋  |
| T5: 集成测试与发布             | 5天  |   P0   |  📋  |

**总工时**: 30天

---

## T1: AI审核服务（49元版）⭐核心

### 1.1 任务清单

#### T1.1 准备扎堆数据库结构

**目标**: 建立大厂AI推荐数据库的初始结构

**步骤**:

1. 创建 `data/crowd_db/` 目录
2. 创建 `data/crowd_db/.gitkeep`
3. 创建 `data/crowd_db/README.md` 说明数据格式
4. 创建 `data/crowd_db/hunan.json` 初始数据（手动整理）

**文件**:

- `data/crowd_db/README.md`
- `data/crowd_db/hunan.json`

**验收**:

- 目录结构存在
- JSON格式正确
- README说明清晰

#### T1.2 创建审核服务Skill

**目标**: 创建 gaokao-audit skill基础结构

**文件**:

- `skills/gaokao-audit/SKILL.md`
- `skills/gaokao-audit/scripts/__init__.py`
- `skills/gaokao-audit/templates/audit_report.html`
- `skills/gaokao-audit/examples/sample_audit.md`
- `skills/gaokao-audit/tests/__init__.py`
- `skills/gaokao-audit/tests/test_audit_service.py`

**内容**:

- SKILL.md 定义角色和接口
- 模板: 审核报告HTML
- 测试文件: 基础测试

#### T1.3 实现方案解析器

**目标**: 实现 plan_parser.py，支持PDF/文本/截图输入

**文件**:

- `skills/gaokao-audit/scripts/plan_parser.py`
- `skills/gaokao-audit/tests/test_plan_parser.py`

**功能**:

- PDF文本提取（pdfplumber）
- 文本直接解析
- 院校/专业/分数提取
- 格式标准化

**TDD流程**:

1. 写测试: 给定PDF文本，应能提取院校列表
2. 实现: 用正则表达式提取
3. 测试通过
4. 提交

#### T1.4 实现规范检查集成

**目标**: 调用现有 gaokao-spec-checker 检查方案

**文件**:

- `skills/gaokao-audit/scripts/checker_integration.py`
- `skills/gaokao-audit/tests/test_checker_integration.py`

**功能**:

- 导入 gaokao-spec-checker 模块
- 复用 PROVINCE_RULES
- 检查结果结构化

#### T1.5 实现扎堆检测器

**目标**: crowd_detector.py，检测方案中院校的扎堆风险

**文件**:

- `skills/gaokao-audit/scripts/crowd_detector.py`
- `skills/gaokao-audit/tests/test_crowd_detector.py`
- `data/crowd_db/loader.py` - 数据加载器

**功能**:

- 加载 crowd_db JSON
- 院校匹配（fuzzy match）
- 风险等级计算
- 替代方案推荐

**TDD流程**:

1. 测试: 给定院校列表和分数，应返回扎堆风险列表
2. 实现: 数据加载+匹配
3. 测试通过

#### T1.6 实现审核服务主类

**目标**: audit_service.py，主入口

**文件**:

- `skills/gaokao-audit/scripts/audit_service.py`
- `skills/gaokao-audit/tests/test_audit_service.py`

**接口**:

```python
def audit_plan(plan_content: str, plan_format: str) -> AuditResult:
    """审核方案主入口"""
```

**TDD流程**:

1. 写测试: 端到端测试
2. 实现: 组合各模块
3. 测试通过

#### T1.7 实现报告生成器

**目标**: report_generator.py，生成审核报告PDF

**文件**:

- `skills/gaokao-audit/scripts/report_generator.py`
- `skills/gaokao-audit/tests/test_report_generator.py`

**功能**:

- 加载HTML模板
- 填充审核数据
- weasyprint生成PDF
- 保存到指定路径

#### T1.8 创建命令行入口

**目标**: gaokao-audit 可执行脚本

**文件**:

- `scripts/gaokao-audit` (软链接到 skills/gaokao-audit/scripts/audit_cli.py)
- `skills/gaokao-audit/scripts/audit_cli.py`

**功能**:

- 接受文件路径参数
- 调用审核服务
- 输出PDF报告路径

#### T1.9 集成到龙老师Skill

**目标**: 在 gaokao-counselor-long 中支持审核场景

**文件**:

- `skills/gaokao-counselor-long/SKILL.md` (更新)
- `skills/gaokao-counselor-long/references/quick-guide.md` (更新)

**变更**:

- 添加审核场景说明
- 添加调用 gaokao-audit 的指令

#### T1.10 审核服务集成测试

**目标**: 端到端测试，验证完整流程

**文件**:

- `tests/test_audit_integration.py`

**测试场景**:

- 上传大厂AI方案文本
- 解析 → 检查 → 扎堆检测 → 生成报告
- 验证报告内容

---

## T2: 反扎堆检测功能

### 2.1 任务清单

#### T2.1 整理大厂AI推荐数据

**目标**: 手动整理湖南省大厂AI热门推荐数据

**文件**:

- `data/crowd_db/hunan.json`

**数据来源**:

- 千问/元宝/百度/豆包公开推荐
- 6月15-30日期间手动整理
- 50-100条热门推荐

**数据结构**:

```json
{
  "provinces": {
    "湖南": {
      "score_ranges": [
        {
          "range": [560, 580],
          "recommendations": [
            {
              "name": "长沙理工大学",
              "major": "会计学",
              "frequency": 4,
              "platforms": ["千问", "元宝", "百度", "豆包"],
              "predicted_increase": 18,
              "alternatives": [...]
            }
          ]
        }
      ]
    }
  }
}
```

#### T2.2 实现数据加载器

**目标**: 加载 crowd_db JSON

**文件**:

- `data/crowd_db/loader.py`
- `data/crowd_db/tests/test_loader.py`

**功能**:

- 读取JSON
- 验证格式
- 提供查询接口

#### T2.3 实现扎堆检测算法

**目标**: 检测方案的扎堆风险

**文件**:

- `skills/gaokao-audit/scripts/crowd_detector.py` (同T1.5)
- `scripts/gaokao-crowd-detector` (CLI入口)

**算法**:

```python
def detect_crowd_risk(plan, user_score, province):
    """
    1. 加载对应省份的crowd_db
    2. 遍历用户方案的每条志愿
    3. 在crowd_db中查找匹配
    4. 返回风险列表
    """
```

#### T2.4 创建扎堆报告展示

**目标**: 在方案生成结果中集成扎堆提示

**文件**:

- `skills/gaokao-college-advisor/SKILL.md` (更新)
- `skills/gaokao-college-advisor/scripts/report_integration.py` (新)

**功能**:

- 方案生成后自动检测扎堆
- 在报告中标注风险等级
- 给出替代建议

#### T2.5 扎堆检测单元测试

**目标**: 完整测试覆盖

**文件**:

- `tests/test_crowd_detection.py`

**测试用例**:

- 高风险院校识别
- 替代方案推荐
- 跨省份处理
- 数据加载异常

---

## T3: 数据溯源功能

### 3.1 任务清单

#### T3.1 扩展院校数据模型

**目标**: 院校数据增加溯源字段

**文件**:

- `data/colleges/hunan.json` (示例)
- `data/colleges/.gitkeep`
- `data/colleges/README.md`

**数据模型**:

```json
{
  "name": "湖南工商大学",
  "score_2025": 565,
  "rank_2025": 28500,
  "source": "湖南省教育考试院",
  "source_url": "http://jyt.hunan.gov.cn/...",
  "source_type": "official",
  "data_year": 2025,
  "confidence": 0.95,
  "last_updated": "2025-08-15"
}
```

#### T3.2 实现溯源数据加载器

**目标**: 加载院校数据 + 溯源元数据

**文件**:

- `data/colleges/loader.py`
- `data/colleges/tests/test_loader.py`

**功能**:

- 加载JSON
- 验证溯源字段
- 提供查询接口

#### T3.3 实现溯源报告生成

**目标**: 报告模板中集成溯源展示

**文件**:

- `skills/gaokao-college-advisor/templates/report_with_trace.html` (新)
- `skills/gaokao-college-advisor/scripts/report_traced.py` (新)

**功能**:

- 加载院校时附带溯源信息
- 在报告中展示
- 标注置信度

#### T3.4 数据溯源CLI

**目标**: 提供数据查询CLI

**文件**:

- `scripts/gaokao-data-trace`

**功能**:

- 输入：院校名称
- 输出：完整数据 + 溯源

---

## T4: 订单管理基础

### 4.1 任务清单

#### T4.1 设计数据模型

**目标**: 设计订单表结构

**文件**:

- `data/orders.db` (新建，SQLite)
- `data/orders_schema.sql`

**Schema**:

```sql
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    external_id TEXT,
    service_version TEXT NOT NULL,
    amount INTEGER NOT NULL,
    status TEXT NOT NULL,
    customer_name TEXT,
    customer_phone_encrypted TEXT,
    customer_wechat TEXT,
    candidate_info_json TEXT,
    assigned_consultant TEXT,
    plan_file TEXT,
    audit_report TEXT,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    delivered_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    tags TEXT
);
```

#### T4.2 实现数据访问层

**目标**: orders_dao.py，数据库CRUD

**文件**:

- `data/orders_dao.py`
- `data/tests/test_orders_dao.py`

**功能**:

- 创建订单
- 查询订单
- 更新状态
- 统计查询

#### T4.3 实现订单管理CLI

**目标**: 命令行订单管理

**文件**:

- `scripts/gaokao-order-manager`

**子命令**:

- create: 创建订单
- list: 列表
- show: 详情
- update: 更新
- pay: 标记支付
- deliver: 标记交付
- stats: 统计

#### T4.4 实现升级订单流程

**目标**: 49元→99元补差价升级

**文件**:

- `data/orders_dao.py` (扩展)
- `scripts/gaokao-order-manager` (扩展)

**流程**:

1. 原订单标记"已升级"
2. 创建新订单，关联 upgrade_from
3. 金额 = 新版本价格 - 原版本价格
4. 用户支付差价

---

## T5: 集成测试与发布

### 5.1 任务清单

#### T5.1 端到端测试

**目标**: 完整业务流测试

**文件**:

- `tests/test_e2e.py`

**测试场景**:

1. 用户咨询 → 方案生成
2. AI审核 → 报告生成
3. 闲鱼订单 → 管理后台录入 → 服务交付
4. 升级订单流程
5. 数据溯源展示

#### T5.2 性能测试

**目标**: 验证性能指标

**测试**:

- 100次连续方案生成
- 50次审核报告生成
- 数据库查询性能

**指标**:

- 响应时间 < 5秒
- 成功率 > 95%

#### T5.3 文档更新

**目标**: 更新所有相关文档

**文件**:

- `docs/API.md` - 添加新API
- `docs/ARCHITECTURE.md` - 更新架构图
- `skills/gaokao-audit/SKILL.md` - 完善文档
- `CHANGELOG.md` - 添加v2.1变更

#### T5.4 发布准备

**目标**: 准备v2.1发布

**任务**:

- [ ] Git tag v2.1
- [ ] 推送到3个仓库
- [ ] 整理发布说明
- [ ] 备份关键数据

---

## 详细任务时间表

### 第1周 (6/15-6/21)

| 日期      | 任务                          | 工时 |
| --------- | ----------------------------- | :--: |
| 6/15 (一) | T1.1 准备数据, T1.2 创建Skill |  8h  |
| 6/16 (二) | T1.3 实现plan_parser          |  8h  |
| 6/17 (三) | T1.3 继续 + 测试              |  8h  |
| 6/18 (四) | T1.4 checker_integration      |  8h  |
| 6/19 (五) | T1.5 crowd_detector           |  8h  |
| 6/20 (六) | T1.6 audit_service主类        |  8h  |
| 6/21 (日) | T1.7 report_generator         |  4h  |

### 第2周 (6/22-6/28)

| 日期      | 任务                          | 工时 |
| --------- | ----------------------------- | :--: |
| 6/22 (一) | T1.8 CLI入口, T1.9 集成龙老师 |  8h  |
| 6/23 (二) | T1.10 集成测试                |  8h  |
| 6/24 (三) | T2.1 整理大厂AI数据           |  6h  |
| 6/25 (四) | T2.2 数据加载器, T2.3 算法    |  8h  |
| 6/26 (五) | T2.4 报告集成                 |  8h  |
| 6/27 (六) | T2.5 扎堆测试                 |  6h  |
| 6/28 (日) | T3.1 扩展数据模型             |  4h  |

### 第3周 (6/29-7/5)

| 日期      | 任务                      | 工时 |
| --------- | ------------------------- | :--: |
| 6/29 (一) | T3.2 溯源加载器           |  8h  |
| 6/30 (二) | T3.3 溯源报告             |  8h  |
| 7/1 (三)  | T3.4 数据溯源CLI          |  6h  |
| 7/2 (四)  | T4.1 订单schema, T4.2 DAO |  8h  |
| 7/3 (五)  | T4.3 订单CLI              |  8h  |
| 7/4 (六)  | T4.4 升级订单流程         |  8h  |
| 7/5 (日)  | T5.1 端到端测试           |  6h  |

### 第4周 (7/6-7/12)

| 日期      | 任务                       | 工时 |
| --------- | -------------------------- | :--: |
| 7/6 (一)  | T5.1 端到端测试（续）      |  8h  |
| 7/7 (二)  | T5.2 性能测试              |  8h  |
| 7/8 (三)  | T5.3 文档更新              |  6h  |
| 7/9 (四)  | T5.3 文档更新（续）        |  6h  |
| 7/10 (五) | T5.4 发布准备              |  6h  |
| 7/11 (六) | T5.4 发布（Git tag, 推送） |  4h  |
| 7/12 (日) | 收尾、复盘                 |  4h  |

**总工时**: 约30天

---

## 验收标准

### 每个Task的DoD (Definition of Done)

- [ ] 代码已实现
- [ ] 单元测试已写且通过
- [ ] 集成测试通过（如适用）
- [ ] 文档已更新
- [ ] 已提交到Git
- [ ] 已推送到3个仓库

### 整个v2.1的DoD

- [ ] AI审核服务可运行（49元版）
- [ ] 反扎堆检测可运行
- [ ] 数据溯源在报告中可见
- [ ] 订单管理可工作
- [ ] 端到端测试100%通过
- [ ] 3个仓库代码同步
- [ ] 文档完整
- [ ] 已通过闲鱼承接2+大厂AI用户

---

## 风险与应对

| 风险                       | 可能性 | 影响 | 应对措施                |
| -------------------------- | ------ | ---- | ----------------------- |
| **大厂AI推荐数据收集困难** | 中     | 高   | 手动整理+用户案例补充   |
| **扎堆预测不准**           | 中     | 中   | 保守估计+明确标注"预测" |
| **数据溯源链接失效**       | 中     | 低   | 定期检查+多源备份       |
| **订单管理SQLite并发**     | 低     | 中   | 写入锁+后续可升级       |
| **进度延期**               | 中     | 中   | 砍T3.4/4.4等P1功能      |

---

## 相关文档

- [PRD](../product/PRD.md) - 产品需求
- [TECH_ARCHITECTURE](TECH_ARCHITECTURE.md) - 技术架构
- [BUSINESS_SCENE](BUSINESS_SCENE.md) - 业务场景
- [COMPETITIVE_ANALYSIS](COMPETITIVE_ANALYSIS.md) - 竞品分析

---

**版本**: v1.0
**最后更新**: 2026-06-11
**下次评审**: 任务完成后
