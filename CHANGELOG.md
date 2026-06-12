# 变更日志

记录高考志愿填报智能系统的所有变更。

---

## v2.1 (开发中)

### 🚧 进行中

#### 新增（T1.3 已完成）

- ✨ **方案解析器 `plan_parser.py`**（`skills/gaokao-audit/scripts/plan_parser.py`，295 行）
  - 解析大厂AI志愿方案文本（纯文本/PDF提取/截图OCR）→ `ParsedPlan` dataclass
  - 字段提取：省份（27 省 + 别名）、分数、位次、选科、来源（千问/元宝/百度/豆包）、志愿列表
  - 志愿行识别支持 4 种行首编号格式：`1. xxx` / `1、xxx` / `1) xxx` / `1 xxx`（PDF 提取常见）
  - 学校/专业分隔支持 4 种风格：`学校 - 专业` / `学校：专业` / `学校（专业组）` / `学校 专业`（按大学/学院关键字兜底）
  - 健壮边界：空文本/无志愿/编号异常均返回 `ParsedPlan` 默认值，不抛异常
  - CLI：`python3 -m skills.gaokao-audit.scripts.plan_parser <file>` 输出 JSON
  - **10 个 pytest 单元测试全部通过**（基础解析/志愿列表/省份别名/选科/PDF 格式/空文本/无志愿/编号多样性/序列化/真实样本回归）
  - 真实样本回归 fixture：`tests/fixtures/sample_xianyu.txt`（百度AI方案）
- 🔒 **T1.2 review 闭环修复**（`skills/gaokao-audit/scripts/validate_template.py`）
  - 模板渲染 `Environment(autoescape=False)` → `autoescape=True`——修复用户派生字段（policy_errors/crowd_risks/data_issues）XSS 注入风险
  - 标签平衡检查：原 "(HTML5 void elements ignored)" 注释与实际行为不符（regex 未排除 void 元素），改为显式 `VOID_ELEMENTS` 集合减去空元素计数（103=103，7 void 元素正确排除）
  - T1.2 验证脚本仍 PASS（mock payload 全部 7 个 must_contain 字符串命中）
- 📝 **`docs/plans/T1-2-audit-skill-and-parser.md` 实施记录**：10/10 测试 ✓ · 真实样本解析正确 ✓ · 省份别名 27 省 ✓ · 编号格式 4 种 ✓

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

#### 新增（T11.2 已完成）

- ✨ **敏感字段展示脱敏工具 `data/orders/masking.py`**（127 行）
  - `mask_phone` / `mask_id_card` / `mask_name` / `mask_sensitive_dict` 四个纯函数
  - 手机号：11 位 → `138****1234`；支持 `+86` / `86` 国家码剥离、常见分隔符（空格 / 横杠）
  - 身份证：18 位 → `430102********1234`（保留前 6 行政区划 + 末 4 位）；15 位老版兼容；非 18/15 位且 ≥13 位的非标准输入也走"前 6 后 4"遮罩
  - 姓名：1 字原样 / 2 字 `张*` / 3 字 `张*丰` / 4+ 字 `张**`；非中日韩字符全遮 `*****`
  - 默认安全：None / 空串 / 非字符串均不抛错，统一返回 None / ""
  - `mask_sensitive_dict` 一键遮罩订单字典中所有已知 PII 字段（不动 \_enc / \_hash 等索引/密文字段）
- ✨ **`Order.to_dict` 扩展 `decrypt_sensitive` 三态策略**
  - `True` : 完整明文（权限内接口使用，如后台人工核对）
  - `False`: 完全移除明文（对外公开统计 / 审计日志）
  - `"mask"` (默认): 部分遮罩（列表 / 详情默认 — 推荐且默认安全）
  - 未知字符串策略值回退为 mask（防误传"plaintext"导致明文泄露）
- ✨ `data/orders/tests/test_masking.py` — 32 个 pytest 用例覆盖：手机号 11/12/带 +86 / 短串 / 非法输入、身份证 18/15/X 校验位 / 短串 / 13 位非标准、姓名 1/2/3/4+ 字 / 英文 / 混合、`mask_sensitive_dict` 不变性、Order.to_dict 三态与默认 mask
- ✅ **测试验证**：data/orders/tests 全套 112 用例通过（含原有 80 + 新增 32）；全仓 344/344 通过；`ruff check` 0 warning；`ruff format --check` 3 文件已规范
- 🔒 **与 T4.1 落盘加密的关系**：crypto.py 负责"落盘形态"（密文 + hash），masking.py 负责"展示形态"（部分遮罩），两者正交 — 落盘加密是底层保险，脱敏展示是上层最小特权

#### 新增（T8.1 已完成）

- ✨ **闲鱼 Webhook + poller 兜底同步**（`data/channel_sync/`）

- `webhook_server.py`：`POST /webhook/xianyu` + `/healthz`，覆盖签名校验、时间戳过期、重复 event、非法状态迁移、审计落库、单 IP 限流
- `poller.py`：共享 `upsert_by_external_id` 幂等链路，支持 cursor 推进与 `poller_state` / `poller_run` 运行记录
- `audit.py` + `dao_extension.py` + `xianyu_adapter.py` + `signature.py`：补齐渠道同步所需审计、适配、验签与订单写库能力
- `data/channel_sync/tests/test_xianyu_channel.py`：129 个 `data/orders + data/channel_sync` 测试通过；`data.channel_sync` 覆盖率 90%，`ruff check data/channel_sync` 0 warning
- 修复关键缺陷：Webhook server 预热 SQLite 连接原先在主线程创建，server 线程复用时触发 `sqlite3.ProgrammingError`，导致 accepted/duplicate/illegal-transition 路径误报 500 且拒绝审计落库失败；现改为 schema bootstrap 后以 `check_same_thread=False` 重新打开连接

#### 新增（T2.3 已完成）

- ✨ **扎堆检测算法**（`data/crowd_db/crowd_detector.py`）
  - `detect_crowd_risk(plan, user_score, province) → list[RiskFinding]`：遍历方案每条志愿，匹配该分数段内的 crowd_db 记录，返回风险列表 + 替代方案
  - 风险等级映射：frequency ≥4 high / 2-3 medium / 1 low / 0 跳过
  - 院校模糊匹配（互相包含），专业可选（计划未指定专业时按院校命中）

#### 新增（T3.1 已完成）

- ✨ **27 省院校数据模型扩展溯源字段**（`data/crowd_db/{province}.json` + `loader.py`）
  - 27 省 JSON 顶层新增 6 字段：`source` / `source_url` / `source_type` / `data_year` / `confidence` / `last_updated`
  - 现有 26 省骨架数据：confidence=0.45，source_type=`manual_summary`，data_year=2025
  - 湖南数据：confidence=0.85，含 68 条推荐（专科批→省外顶尖，10 段连续 440-690 覆盖）
  - `CrowdDBLoader` 扩展 `warn_low_confidence` / `load_metadata(province) → 8 字段` / `list_supported_provinces()` / `list_provinces()` / `load_province` 对 confidence<0.5 发 `UserWarning`
  - 新增 `data/crowd_db/SCHEMA.md`：顶层/分数段/推荐条目三表 schema + `source_type` 枚举（`manual_summary` / `official_release` / `platform_scrape` / `derived`）+ 骨架文件约定
  - 测试：`data/crowd_db/tests/test_provenance.py` 9 用例（27 存在性、顶层字段、score_range schema、confidence 区间、loader 27 报告、metadata 8 字段、低 confidence 警告、端到端匹配），T2.1/T2.2/T2.3 46 用例无回归
  - 与 T2.3 协同：`crowd_detector._risk_level_from_frequency` 与 `CrowdRecommendation.risk_level` 在 frequency 0-5 边界完全一致

#### 新增（T3.2 已完成）

- ✨ **溯源字段查询 + 验证 API**（`data/crowd_db/loader.py` + `tests/test_provenance_query.py`）
  - 新增 dataclass `ProvenanceValidation`：含 `ok` / `errors` / `warnings` / `is_usable` / `summary` 5 字段 + `to_dict()`
  - 类常量：`USABLE_CONFIDENCE_THRESHOLD = 0.5` / `VALID_SOURCE_TYPES`（4 枚举）/ `ISO_DATE_PATTERN` / `REQUIRED_PROVENANCE_FIELDS`（7 字段）
  - `validate_provenance(data, province) → ProvenanceValidation`（@classmethod，不需 loader 实例）：校验字段类型/范围/枚举/日期格式，区分硬错误与软警告
  - `validate_province(province) → ProvenanceValidation`：加载 + 校验一体化
  - `validate_all() → dict[province, ProvenanceValidation]`：27 省一次性扫描
  - `filter_provinces(*, source_type, min_confidence, max_confidence, data_year, updated_since, updated_before, only_usable) → list[province]`：多维溯源过滤，按 `PROVINCE_FILE_MAP` 顺序返回
  - `get_provenance_report(*, only_usable, source_type) → dict`：汇总 `total` / `usable_count` / `failed_count` / `by_source_type` / `items`
  - 27 省现状：全部 schema 校验通过（`failed=0`），仅湖南 1 省 `is_usable=True`（confidence=0.85），26 省 low_confidence warning
  - 测试：`data/crowd_db/tests/test_provenance_query.py` **33 用例全通过**，覆盖 validate_all/27、validate_province 单省、validate_provenance 边界（None/空 dict/confidence 越界/source_type 非法/data_year 类型错/date 格式错/empty source warning）、filter_provinces 9 维 + 组合、get_provenance_report 5 统计项、未知省份 load_failed、ProvenanceValidation.to_dict、load_metadata 兼容性、validate_provenance 不可变性
  - 不破坏既有 API：`load_province` / `find_recommendations` / `find_recommendation_by_school` / `load_metadata` 行为与契约完全不变；T2.x 46 用例 + T3.1 9 用例 + T3.2 33 用例 = **88/88 通过**
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
