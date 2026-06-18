# PROJECT_PLANNING_REALIGNMENT_2026-06-16

最后更新: 2026-06-16
真相源: 本文件是 `docs/CURRENT_STATE.md` 之外的"规划/实现漂移审计"补充真相源。
本审计聚焦: 当前规划/设计文档与代码、规则、数据之间的真实不一致点。

> 2026-06-18 补充：`rules/provinces.md` 已完成入口化改造，当前不再承载逐省静态字段明细；`rules/_truth/province/*.yaml` 与 `rules/_evidence/` 才是现行规则真相源。本文对 `rules/provinces.md` 旧静态快照的批评保留为 2026-06-16 审计基线，不再代表当前实现。

---

## 1. 范围与方法

- 审计对象:
  - 产品规划: `product/PRD.md`、`product/ROADMAP.md`
  - 技术设计: `docs/TECH_ARCHITECTURE.md`、`docs/ADMIN_DESIGN.md`、`docs/SHARING_DESIGN.md`、`docs/PAYMENT_DOMAIN_DESIGN.md`
  - 实施计划: `docs/IMPLEMENTATION_PLAN_v2.md`
  - 规则真相源: `rules/provinces.md`、`rules/errors/ERRORS.md`、`skills/gaokao-spec-checker/SKILL.md`、`scripts/gaokao-checker`、`data/crowd_db/*.json`
  - Skill 定义: `skills/gaokao-spec-checker/SKILL.md`、`skills/gaokao-audit/SKILL.md`、`skills/gaokao-counselor-long/SKILL.md`、`skills/gaokao-college-advisor/SKILL.md`、`skills/zhangxuefeng-skillset/SKILL.md`
  - 实际代码: `admin/`、`data/`、`scripts/`
- 审计目标: 不重复 T12/支付/portal 已收口结论，只补"规划 vs 实现 vs 规则 vs 数据"的真实不一致。

---

## 2. 主要漂移与缺口

### 2.1 规则能力: 三处真相源口径不一致

- `rules/provinces.md`:
  - 院校专业组模式 14 省
  - 专业+学校模式 8 省
  - 传统模式 5 省
  - 合计 27 省
- `skills/gaokao-spec-checker/SKILL.md` frontmatter:
  - 列名宣称支持 27 省
  - 摘要中按 14/8/6 描述,与 `rules/provinces.md` 的传统模式数量(5) 不一致
- `scripts/gaokao-checker` 的 `PROVINCE_RULES`:
  - 实际定义 27 省
  - 与 `rules/provinces.md` 的 27 省口径一致
- 真实差距:
  - 文档对外宣称 27 省
  - 实际规则也是 27 省
  - 但 `gaokao-spec-checker` 摘要里的传统模式数仍写成 6,与 `rules/provinces.md` 的 5 不一致
- 风险:
  - 客服/智能体在文档与脚本之间会获得不同省份覆盖承诺
  - 后续任何"加省/删省"都会在三个真相源之间产生连锁漂移

### 2.2 规则证据链不足: 全国通用规则没有独立抽象

- 现状:
  - `gaokao-spec-checker` 的检查项是硬编码的省级字段(志愿数、专业组数、调剂范围等)
  - 没有"全国通用规则"独立层
  - 没有"省级差异规则"独立层
  - 规则来源只在 PROVINCE_RULES 的 `official_url` 字段里给一个官网链接,没有版本号、发布日期、收录人、证据文件
- 后果:
  - 任何省级规则更新,必须改 `gaokao-checker` 源码
  - 没有任何审计能告诉你"湖南 2026 规则 v1.2 是基于哪份官方文件"
  - 智能体调用 spec-checker 时无法解释"为什么这一条规则成立"

### 2.3 专业目录数据: 没有结构化真相源

- 现状:
  - 仓库内无 `data/majors/`、无 `data/majors_catalog/` 等目录
  - 现有 `data/crowd_db/hunan.json` 等只是"大厂AI热门推荐汇总",不是教育部本科专业目录
  - 院校专业组里的"专业名"散落在各 SKILL.md / rules / crowd_db / 报告中,无统一结构
  - 没有"专业是否存在 / 是否 2026 仍招生 / 是否已撤销"的元数据
- 后果:
  - 任何推荐、审核、报告都可能在引用:
    - 已经撤销的专业
    - 已经合并的专业
    - 近两年新设的目录外专业
  - 没有机制阻止"AI 生成方案里写了已经撤销的某专业"

### 2.4 数据溯源机制: 局部实现, 缺统一抽象

- 现状:
  - `data/crowd_db/hunan.json` 内有 `source / source_url / source_type / confidence` 字段
  - 但只是"这一份" crowd_db 数据的元数据
  - 没有任何代码层把这些元数据汇总到"整个项目的数据来源台账"
  - SKILL.md 之间的引用缺乏统一证据链
- 后果:
  - `data_trace` 脚本/能力只在 crowd_db 范围可用
  - 真实生产环境里"这份院校数据来自哪里"无法一键回答

### 2.5 CLI 能力面: 多入口, 缺统一命令面

- 现状(部分清单):
  - `scripts/gaokao-checker` — 规范检查
  - `scripts/gaokao-audit` — 审核
  - `scripts/gaokao-order-manager` — 订单 CLI
  - `scripts/gaokao-shortlink` — 短链接
  - `scripts/gaokao-data-trace` — 数据溯源
  - `scripts/gaokao-channel-fallback` — 渠道兜底
  - `scripts/gaokao-delivery-*.py` — 交付相关
  - `scripts/backup_*` — 备份
  - `scripts/gaokao-retention-cleanup.py` — 数据保留
  - `scripts/payment_provider_doctor.py` — 支付 provider 健康检查
- 问题:
  - 命令命名风格不统一(`gaokao-` 前缀 vs 业务前缀)
  - 参数风格、输出格式、退出码各脚本不统一
  - 没有"统一 CLI 入口"能让客服/运营/智能体一句话调起全部能力
  - 智能体(尤其 gaokao-counselor-long)直接调 Python 模块,而不是稳定 CLI

### 2.6 智能体集成: Skill 之间耦合度高, 缺统一调度层

- 现状:
  - `gaokao-counselor-long` 通过 Python import 直接调 `skills/gaokao-audit/scripts/audit_service`
  - 文档化的"统一 CLI 入口"实际是 `python3 scripts/gaokao-audit <file> --json`
  - 没有"能力注册表 / agent capability catalog"层
- 后果:
  - 任何脚本目录结构改动都会破坏 smart body 调用
  - 跨 skill 协作靠约定,不靠契约
  - 运营/客服智能体无法在不读源码的情况下找到所有可用能力

### 2.7 PRD/TECH_ARCHITECTURE 与实现的脱节点

- `docs/TECH_ARCHITECTURE.md` 第 2.1 节明确说"省份规则: hardcoded in scripts":
  - 这是真实状态,但 TECH_ARCHITECTURE 写得像"目标态",不是真实态
- `docs/TECH_ARCHITECTURE.md` 列出"v2.0 已有 `gaokao-checker` 入口", 但 SKILL.md 与 plan 都没有把"gaokao-checker 是审核入口"这件事正式承认
- `product/PRD.md` 的 F020 "AI 方案审核" 标 ✅ 已完成, 但 `gaokao-audit` 现状只能本地 smoke + 文档化能力, 真实客服/智能体调用未走 prod 链路
- `docs/ADMIN_DESIGN.md` 描述的"案例管理 / 数据监控"在 `admin/routes/cases.py` `admin/routes/stats.py` 里, 但与 PRD 描述不完全一致(PRD 描述更"全栈", 实现是 admin 后台视角)

### 2.8 文档分层不统一

- 现状:
  - 设计文档(ADMIN_DESIGN / SHARING_DESIGN / TECH_ARCHITECTURE) 描述的是 v1.0 目标态
  - 计划文档(IMPLEMENTATION_PLAN_v2) 是 v2.0 实施态
  - 当前状态文档(CURRENT_STATE) 是 v2.1 已完成态
  - 没有任何文档明确说"哪一份是当前真相源"在每个维度上
- 后果:
  - 阅读者要自己在多份文档之间"挑最新"
  - AI 智能体引用时容易引用过期设计

---

## 3. 优先级判断

### P0 — 不修会直接影响生产可信度

- 规则三处真相源口径不一致(2.1)
- 专业目录数据没有结构化真相源(2.3)

### P1 — 不修会限制下一阶段能力建设

- 规则证据链不足, 无全国/省级规则分层(2.2)
- CLI 能力面不统一(2.5)
- 智能体集成无统一调度层(2.6)

### P2 — 不修会继续漂移但不立即影响生产

- 数据溯源机制缺统一抽象(2.4)
- PRD/TECH_ARCHITECTURE 与实现脱节(2.7)
- 文档分层不统一(2.8)

---

## 4. 下一阶段必须分两条线

- **可信化线(P0)**:
  - 规则真相源改造
  - 专业目录数据接入与版本化
- **能力层线(P1)**:
  - 统一审计引擎
  - 统一 CLI 命令面
  - 智能体能力注册表
- 文档/架构收敛(P2)放在可信化线和能力层线收口后, 一次性收敛

---

## 5. 与本轮新任务的对接

本审计直接回答用户最新提出的四个优化目标:

| 用户目标          | 对应审计结论 | 后续设计                  |
| ----------------- | ------------ | ------------------------- |
| 规则规范可信化    | 2.1, 2.2     | 规则四层模型              |
| 2026 官方专业目录 | 2.3, 2.4     | 专业目录数据模型 + 真相源 |
| 系统 CLI 能力层   | 2.5, 2.6     | 统一命令面 + 智能体调度   |
| 整体规划/实现优化 | 2.7, 2.8     | 文档分层 + 真相源索引     |

后续设计见: `docs/DESIGN_RULES_TRUSTED_CLI_2026-06-16.md`
