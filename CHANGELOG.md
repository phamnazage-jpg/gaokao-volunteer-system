# 变更日志

记录高考志愿填报智能系统的所有变更。

---

## v2.1 (开发中)

### 🚧 进行中

#### 新增（T1.2 已完成）

- ✨ **AI方案审核服务 Skill**（`skills/gaokao-audit/`）
  - `SKILL.md`（143 行）— 角色边界 + 49 元服务定价 + 四维审核框架 + 合规红线 + DoD
  - `templates/audit_report.html`（262 行，Jinja2）— 报告模板，含政策合规/扎堆风险/数据存疑/改进建议 4 区块 + 升级到 99 元完整方案卡片
  - `examples/sample_audit.md`（144 行）— 输入样例（大厂AI方案文本/PDF/截图）+ 输出报告样例 + 渲染数据契约表
  - `scripts/validate_template.py`（137 行）— 模板渲染校验器，16 个占位符 + 7 个渲染输出字符串断言
  - `tests/test_validate_template.py`（33 行）— pytest 入口，1 用例通过
  - 关键设计：T1.1 review 暴露的 4 个反模式（吞错、模糊 substring、vacuous 测试、缺失档位）已显式列入"对齐 T1.1 review 教训"表，由 T1.3 实施时强制规避
  - T1.2 测试套件：**1/1 通过**（含项目原有 6 个 spec_checker 测试 → 7/7 通过）

#### 新增（T7.1 已完成）

- ✨ **短链接生成**（`data/share/short_link.py` + `scripts/gaokao-shortlink`）
  - base62 短码生成（默认 6 位，4-16 位可配，加密随机 + 冲突重试）
  - SQLite 映射表 `share_links`（WAL 模式，code 主键 + report/owner/expires 三索引）
  - `ShortLinkService` 完整 API：`create / get / resolve / revoke / list_by_report / list_by_owner / get_stats / purge_expired`
  - 访问控制：`permission`（read/comment/edit/admin）+ 密码（sha256）+ `expires_at` + `revoked`
  - `route_short_link(code, password, base_url)` 路由辅助，可挂载任意 Web 框架的 `/s/<code>`
  - CLI：`create / resolve / revoke / list / stats / purge`，全部子命令 JSON 输出
  - 25 个 pytest 用例全部通过（base62 编解码、碰撞重试、TTL、密码、撤销、列表、统计、清理、路由）

#### 新增（T10.1 已完成）

- ✨ **GitHub Actions CI 流水线**
  - 自动化测试（push / pull_request 触发）
  - 多 Python 版本矩阵（3.10 / 3.11 / 3.12）
  - pytest + pytest-cov 覆盖率报告（XML 产物供 T10.2 codecov 集成）
  - pip 依赖缓存（加速运行）
- ✨ `requirements-dev.txt` — 测试依赖（pytest / pytest-cov / pytest-timeout / pytest-xdist）
- ✨ `pytest.ini` — 统一本地与 CI 测试发现配置
- ✨ README 顶部 CI 状态徽章

#### 新增（T10.2 已完成）

- ✨ **Codecov 覆盖率报告与徽章**
  - `.github/workflows/ci.yml` 集成 `codecov/codecov-action@v4`，3.11 单点上传 coverage.xml
  - `codecov.yml` 定义 project 目标 60% / 核心 skills 目标 80% / patch 目标 70%，与 T5.5 硬门槛对齐
  - `fail_ci_if_error: false`：codecov 不可达时不影响 CI 通过（适配多镜像仓库场景）
  - README 顶部新增 codecov 覆盖率徽章
- ✨ PR 浮动容忍 1%（project）/ 2%（core），避免噪声红灯

#### 新增（T2.3 已完成）

- ✨ **扎堆检测算法**（`data/crowd_db/crowd_detector.py`）
  - `detect_crowd_risk(plan, user_score, province) → list[RiskFinding]`：遍历方案每条志愿，匹配该分数段内的 crowd_db 记录，返回风险列表 + 替代方案
  - 风险等级映射：frequency ≥4 high / 2-3 medium / 1 low / 0 跳过
  - 院校模糊匹配（互相包含），专业可选（计划未指定专业时按院校命中）
  - 多种 plan 形态：dict / CrowdRecommendation / tuple / list
  - 支持注入 `loader` 便于测试，频率降序排序
  - 20 个单元测试覆盖：高/中风险识别、替代方案、分数段边界、模糊匹配、专业匹配、空/异常输入、部分命中、排序
- ✨ `data/crowd_db/tests/test_crowd_detector.py` — 20 个测试覆盖算法各分支

### 📅 计划中

- T10.3 多仓库同步脚本
- T5.5 覆盖率硬门槛（核心 ≥80% / 整体 ≥60%）

---

## v2.0 (2026-06-11)

### 🎉 重大变化

#### 新增

- ✨ **规范检查Skill V2**：支持27个省份自动适配
  - 院校专业组模式（14省）
  - 专业+学校模式（8省）
  - 传统模式（5省）
- ✨ 省份规则库（`rules/provinces/`）
- ✨ 错误模式库（`rules/errors/`）
- ✨ 真实案例库（`docs/case-studies/`）
- ✨ 优化日志（`docs/optimization-log/`）
- ✨ 完整项目目录结构

#### 修复

- 🐛 修正"院校专业组"概念（原错误为"45个学校"）
- 🐛 修正调剂规则（原错误为"全校调剂"）
- 🐛 修正投档后规则（原错误为"退到下个志愿"）
- 🐛 移除主观概率（原错误为"35%、80%"）
- 🐛 修正选科一刀切（原错误为"所有会计都要求物+化+生"）

#### 改进

- ⚡ 院校数据从2025年位次精确化
- ⚡ 风险提示前置
- ⚡ 数据来源明确标注
- ⚡ 强调"以官方为准"

### 📝 起源事故

- 真实用户咨询：湖南578分/物化生
- 原方案出现致命错误（院校专业组概念错误）
- 用户质疑"是否符合规范"触发自查
- 创建本检查Skill防止错误复发

---

## v1.0 (2026-06-10 → 2026-06-11)

### 初始版本

- gaokao-college-advisor Skill
- 可视化报告脚本
- 1分钟/3分钟/7步三套问卷
- 邮件发送功能

### 已知问题

- ❌ 政策理解停留在2024年水平
- ❌ 数据主观化严重
- ❌ 缺乏方案检查机制
- ❌ 部分细节不符合本省规范

### 用户反馈

- "符合今年对应区域志愿填报规范吗？" ← 触发v2.0创建

---

## 📊 版本对比

| 维度       | v1.0 | v2.0          |
| ---------- | ---- | ------------- |
| 省份支持   | 湖南 | 27个          |
| 检查机制   | 无   | 规范检查Skill |
| 错误模式库 | 无   | 8+种错误      |
| 数据精度   | 主观 | 基于2025位次  |
| 风险提示   | 后置 | 前置          |
| 项目结构   | 散落 | 集中          |
| 文档体系   | 简单 | 完善          |

---

## 🎯 下一步

- 添加更多省份（覆盖完整30+省）
- 完善数据自动化对接
- 增强算法精度
- 完善UI/UX

详见 `docs/optimization-log/future-plan.md`
