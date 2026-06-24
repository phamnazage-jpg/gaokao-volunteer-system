# 全国高信任 crowd_db 建设计划

> For Hermes: 后续执行使用 `swarm-task-decomposition` + `subagent-driven-development`。按省份批次并行，每个子代理只负责一个清晰边界的子任务，不跨 3 个以上文件，不承担全局汇总。

最后更新: 2026-06-23
适用仓库: `/home/long/project/gaokao-volunteer-system`
真相源: `docs/CURRENT_STATE.md`

## 1. Goal

把当前“湖南 1 省 high、其余 26 省 skeleton”的 crowd_db，升级为“全国可用、重点省份高信任、其余省份至少 usable 且有明确可信来源与复核链”的数据体系。

这里的“全国”分两层解释，必须先定口径：

- 口径 A（当前代码兼容口径）: 先把 `data/crowd_db/loader.py` 已支持的 27 省全部建设到位。
- 口径 B（真正全国口径）: 在 27 省基础上，再补 4 个当前未进入 crowd_db 的自治区：`内蒙古 / 广西 / 西藏 / 宁夏`，形成 31 个省级行政区覆盖。

建议执行口径：先完成 A，再推进 B。原因：当前 rules/checker 已有更广省份支持，但 crowd_db loader 仍只支持 27 省，直接喊“全国完成”会产生能力漂移。

## 2. 当前事实基线（2026-06-23 实测）

来自当前运行统计，而不是旧文档复述：

- 当前 `data/crowd_db/*.json` 实存 27 个文件
- 当前 `data/crowd_db/loader.py` 仅支持 27 省（23 省 + 4 直辖市）
- 当前 live 质量分布：`HIGH=4 / USABLE=3 / LOW=20`
- 高信任白名单: 湖南 / 广东 / 江苏 / 山东（均已达到 `confidence=0.85`、8 段、40 recommendations、80 alternatives）
- 3 个 usable: 福建 / 河北 / 浙江（`confidence=0.65`，8 段 / 24 recommendations / 24 alternatives）
- 其余 20 省仍为 skeleton（当前 `confidence=0.45`）
- 高价值大省中，河南 / 湖北 / 四川 / 北京 / 上海 仍是骨架，仍属后续优先升级对象
- 27 省已统一补齐 `trusted_sources=3` 与 `quality_note`
- 当前测试 `data/crowd_db/tests/test_crowd_db_data_quality.py` 已切换为显式 high 白名单机制

这说明：

1. 当前项目并没有“全国高信任数据”，只有“全国骨架 + 湖南高信任样板”。
2. 现阶段最大缺口不是 schema，而是“逐省内容密度、来源复核、质量升级流程”。
3. 要做成全国高信任，必须先修改质量门禁与分层验收方式，不能靠手工把 confidence 改高。

## 3. 非目标（这轮不要混入）

1. 不在本轮把 crowd_db 扩展成真实录取数据库。
2. 不在本轮补“院校代码/专业代码/录取位次原始表”全量事实库。
3. 不把大厂 AI 推荐摘要伪装成官方录取结论。
4. 不把“已补 trusted_sources”误报成“已完成高信任建设”。
5. 不要求 31 省一次性同时到 high；必须分层推进。

## 4. 高信任定义（新的分层验收标准）

当前只有 high / usable / skeleton 三层，但缺少“如何升级”的硬门槛。后续执行必须按下面标准推进。

### 4.1 skeleton（骨架）

定义：

- 有基础 schema
- 有可信来源入口
- 有最少量推荐示例
- `confidence < 0.5`

允许用途：

- UI 占位
- provenance 展示
- 告知“该省数据仍待人工补完”

不允许用途：

- 驱动反扎堆强结论
- 对外说“高信任推荐”

### 4.2 usable（可用）

建议门槛：

- `confidence >= 0.65`
- 至少 6 个 score_ranges
- 至少 24 条 recommendations
- 至少 24 条 alternatives
- 至少 1 个省级官方来源入口完成年度复核（不再是空 URL）
- `quality_note` 明确“可用但未达 high”

允许用途：

- 普通省份的基础反扎堆分析
- 用户侧展示“中等信任/待进一步复核”标签

### 4.3 high（高信任）

建议门槛：

- `confidence >= 0.80`
- 至少 8 个 score_ranges
- 至少 40 条 recommendations
- 至少 60 条 alternatives
- 覆盖高/中/低至少三层分数带，而不是只覆盖头部段
- 省级官方入口已完成年度复核
- 至少一次 cross-source 交叉审核通过
- 有对应测试明确从 usable 升级到 high，不允许静默升级

说明：

- 湖南当前是 high 样板，但不要求其它省必须完全复制湖南数据形态；要求是达到“可解释、可复核、可回归”的同等级可信度。

## 5. 推荐建设目标（分阶段，不一次性虚报）

### Phase 0：边界收口

目标：明确这轮是“27 省升级”还是“31 省全国化”。

交付：

- 更新 `data/crowd_db/README.md`
- 更新 `data/crowd_db/SCHEMA.md`
- 补一份当前真相文档，明确：
  - 当前 loader 只支持 27 省
  - 若要宣称“全国”，需补 4 个自治区到 crowd_db loader 与测试

验收：

- 文档中不再混淆“全国”和“当前 27 省支持”

### Phase 1：先把 8 个高价值省份升到 high

优先省份（建议第一批）：

- 广东
- 江苏
- 山东
- 河南
- 湖北
- 四川
- 北京
- 上海

原因：

- 用户量/业务价值高
- 当前仍是骨架，风险最高
- 一旦补齐，产品“全国可用”的核心观感会大幅改善

目标：

- 8 省全部从 skeleton 升到 high
- 测试不再锁死“仅湖南为 high”，改为显式 high 白名单

### Phase 2：第二梯队升到 usable，其中 3-5 省继续冲 high

建议第二批：

- 浙江
- 河北
- 福建
- 安徽
- 江西
- 辽宁
- 陕西
- 重庆
- 天津
- 海南

目标：

- 第二梯队全部至少 usable
- 从中选择 3-5 省继续升到 high（按实际数据密度）

### Phase 3：长尾省份全部脱离 skeleton

建议第三批：

- 山西
- 吉林
- 黑龙江
- 甘肃
- 青海
- 云南
- 贵州
- 新疆
- 其余新增的 4 个自治区（若执行口径 B）

目标：

- 所有支持省份至少 usable
- 不再存在 `confidence < 0.5` 的省份

### Phase 4：真实全国口径闭环

仅当要对外说“全国高信任数据已建立”时才可进入本阶段。

目标：

- crowd_db 覆盖 31 个省级行政区
- 至少 12 个高价值省份达 high
- 其余省份全部 usable
- 文档、测试、UI 文案、CURRENT_STATE 同步完成

## 6. 多子代理执行架构（Swarm）

### 6.1 角色设计

1. Orchestrator（主控）
   - 维护执行板、批次、依赖、验收状态
   - 不直接编内容，负责汇总与最终入库

2. Province Source Verifier（来源核验代理）
   - 逐省确认省级考试院/招生考试机构年度入口
   - 输出可信来源 URL、年度入口状态、复核说明

3. Province Content Builder（内容构建代理）
   - 以现有 JSON 为底稿，补 score_ranges / recommendations / alternatives
   - 不负责最终 confidence 定级

4. Cross-Source Reviewer（交叉复核代理）
   - 审查该省数据是否只覆盖头部、是否段位失衡、是否 alternatives 过少
   - 给出 high/usable/skeleton 建议等级

5. Test & Contract Guard（测试门禁代理）
   - 更新/新增测试
   - 锁死 high 白名单、usable 最低标准、31 省覆盖（如进入 B 口径）

6. Final Integrator（集成代理）
   - 合并 JSON、README、SCHEMA、测试、当前状态文档
   - 运行完整验证并准备提交

### 6.2 单省标准流水线

每个省必须按这 5 步走，不允许跳步：

1. 来源核验
   - 找到国家级入口 + 省级入口
   - 写入 `trusted_sources`

2. 内容扩充
   - 补足 score_ranges / recommendations / alternatives

3. 交叉复核
   - 检查是否只覆盖头部段
   - 检查 recommendations / alternatives 是否达到升级门槛

4. 质量定级
   - 给出建议 confidence 与 quality_note
   - 不允许人工直接“拍脑袋升 high”

5. 测试锁定
   - 若省份升级到 usable/high，必须更新测试白名单与阈值断言

### 6.3 并行约束

为防止冲突，按“每省 2 代理 + 1 汇总代理”的方式执行：

- 并行代理 A：来源核验
- 并行代理 B：内容构建
- 串行代理 C：交叉复核 + 合并

不要让多个代理同时改同一个省文件。
不要让多个代理同时改 `test_crowd_db_data_quality.py`。

## 7. 批次拆分（推荐的实际执行顺序）

### Batch 0：基线收口（1 个主代理）

任务：

- 明确 27 vs 31 省目标口径
- 设计新的分层验收标准
- 改写 README / SCHEMA / CURRENT_STATE 相关表述

涉及文件：

- `data/crowd_db/README.md`
- `data/crowd_db/SCHEMA.md`
- `docs/CURRENT_STATE.md`
- `docs/ACTIVE_REMEDIATION_2026-06-20.md`
- `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`

### Batch 1：已 usable 省份继续冲 high（建议 2 轮并发）

Round 1:

- 广东
- 江苏
- 山东

Round 2:

- 浙江
- 河北
- 福建

每轮输出：

- 省文件更新
- 省级复核摘要
- 是否达到 high 的证据
- 若未达 high，明确仍缺项（范围/推荐数/alternatives/交叉复核）

### Batch 2：高价值 skeleton 省份先脱骨架（建议 3 轮并发）

Round 1:

- 河南
- 湖北
- 四川

Round 2:

- 北京
- 上海
- 天津

Round 3:

- 安徽
- 辽宁

目标：

- 先全部升到 usable
- 为后续冲 high 建立第一轮可信来源与内容密度基础

### Batch 3：其余 skeleton 省份升 usable（建议 4 轮并发）

Round 1:

- 江西
- 重庆
- 海南

Round 2:

- 山西
- 吉林
- 黑龙江

Round 3:

- 陕西
- 甘肃
- 云南

Round 4:

- 贵州
- 青海
- 新疆

### Batch 4：补 4 个自治区（仅当采用 31 省全国口径）

- 内蒙古
- 广西
- 西藏
- 宁夏

这批必须同时修改：

- `data/crowd_db/loader.py`
- `data/crowd_db/README.md`
- `data/crowd_db/SCHEMA.md`
- 相关 provenance / quality tests

## 8. 需要修改/新增的文件

### 核心数据文件

- `data/crowd_db/*.json`

### 核心逻辑与契约

- `data/crowd_db/loader.py`
- `data/crowd_db/README.md`
- `data/crowd_db/SCHEMA.md`
- `data/crowd_db/quality_summary.py`

### 测试门禁

- `data/crowd_db/tests/test_crowd_db_data_quality.py`
- `data/crowd_db/tests/test_provenance.py`
- `data/crowd_db/tests/test_loader.py`
- 如进入 31 省口径，还需补覆盖 31 省的断言

### 文档真相同步

- `docs/CURRENT_STATE.md`
- `docs/ACTIVE_REMEDIATION_2026-06-20.md`
- `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`
- 新增建议：`docs/CROWD_DB_NATIONALIZATION_SOURCE_OF_TRUTH.md`

## 9. 测试与验收策略

### 9.1 数据级验收

每省必须验证：

- JSON schema 合法
- `confidence` 与 `quality_note` 一致
- `trusted_sources` 至少包含国家级 + 省级来源
- `score_ranges` 不是头部单段伪扩容
- `recommendations` / `alternatives` 数量达到目标层级

### 9.2 仓库级验收

必须新增/改造测试：

1. `test_crowd_db_data_quality.py`
   - 从“仅湖南 high”改为“high 白名单显式枚举”
   - usable / high 各有最低门槛断言
   - 若采用 31 省口径，省份总数从 27 改为 31

2. `test_provenance.py`
   - 每个升级到 usable/high 的省必须有省级官方入口 URL

3. `test_loader.py`
   - 若新增 4 个自治区，`list_supported_provinces()` 必须同步变 31

4. 新增建议：`test_high_trust_thresholds.py`
   - 专门锁 high/usable 的阈值，防止 future drift

### 9.3 业务级验收

对每个升 high 的省，至少抽 3 个分数段做 smoke：

- 头部段
- 中段
- 保底段

验证：

- `find_recommendations()` 返回非空
- `load_metadata()` 反映正确 confidence / trusted_sources_count / record_count
- 风险报告可生成，不出现“空壳高信任”

## 10. 建议的子代理任务模板

### 模板 A：省级来源核验代理

目标：

- 核实指定省份的国家级/省级可信来源入口

输入：

- 省份名
- 当前 JSON 路径

输出：

- `trusted_sources` 建议值
- 省级入口 URL
- 年度复核说明
- 不直接改 confidence

### 模板 B：省级内容构建代理

目标：

- 扩充指定省份的 score_ranges / recommendations / alternatives

输入：

- 省份名
- 当前 JSON 路径
- 目标层级（usable 或 high）

输出：

- 更新后的省文件
- 数量统计（ranges / recs / alts）
- 自评是否达到目标层级

### 模板 C：省级交叉复核代理

目标：

- 审核该省是否真的达到目标层级

输出：

- 结论：pass / downgrade-to-usable / reject
- 原因：覆盖不足 / alternatives 不足 / 只覆盖头部 / 来源未复核

### 模板 D：测试门禁代理

目标：

- 把本轮升级同步到测试与质量摘要脚本

输出：

- 更新测试文件
- 提供新增 high/usable 断言

## 11. 推荐执行节奏

### 第 1 周

- 完成 Batch 0
- 完成 Batch 1 Round 1（广东/江苏/山东）

### 第 2 周

- 完成 Batch 1 Round 2 + Round 3
- 把 high 白名单从 `湖南` 扩成 `湖南 + 第一批达标省份`

### 第 3 周

- 完成 Batch 2
- 第二梯队至少全部 usable

### 第 4 周

- 完成 Batch 3
- 若用户确认追求真正全国，再开始 Batch 4 的 4 个自治区扩展

## 12. 风险与防漂移规则

1. 风险：静默升级
   - 防线：任何新 high 省份都必须改测试白名单

2. 风险：只补来源不补内容
   - 防线：来源核验与内容构建拆成两个代理，交叉复核单独执行

3. 风险：只补头部学校，伪装成高信任
   - 防线：high 必须覆盖至少三层分数带

4. 风险：27 省文档说成全国
   - 防线：先完成 Phase 0 边界文档收口

5. 风险：多个代理同时改测试导致冲突
   - 防线：测试门禁只允许一个汇总代理写入

## 13. 推荐的第一批落地任务（最短闭环路径）

### Task 1

明确口径：本轮先做 27 省升级，还是直接补到 31 省。

### Task 2

重写 crowd_db 分层标准与测试策略。

### Task 3

先拿广东、江苏、山东做第一轮 high 升级样板。

### Task 4

同步更新 `test_crowd_db_data_quality.py`，把“仅湖南 high”切换成显式白名单。

### Task 5

更新 `CURRENT_STATE.md` / `ACTIVE_REMEDIATION` / `ACTIVE_EXECUTION_BOARD`，把 Q-A 从“可信来源已补齐”提升为“全国高信任建设计划已启动，已进入第 1 批省份执行”。

## 14. 完成定义

只有满足以下条件，才能说“全国高信任数据已建立”：

- 若采用 27 省口径：27 省全部至少 usable，且 8-12 个关键省份达 high
- 若采用 31 省口径：31 省全部至少 usable，且 12 个左右关键省份达 high
- 测试、loader、quality_summary、CURRENT_STATE、执行板全部同步
- UI/对外文案不再出现与真实质量等级冲突的描述

在此之前，只能说：

- “全国高信任建设计划已启动”
- “第 N 批省份已升级到 usable/high”
- 不能说“全国高信任已完成”

## 15. 推荐下一步

下一步不是直接开 26 省大并发，而是先做一个可验证的样板批：

1. Phase 0 边界收口
2. 广东 / 江苏 / 山东 三省样板升级
3. 测试门禁改造
4. 再按批次放大到全国

理由：

- 这样可以先把“升级标准、测试契约、子代理协作模式”打磨稳定
- 避免一次性铺 26 省，最后发现 high 定义、测试门槛、文档口径全部要返工
