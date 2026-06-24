# crowd_db 全国高信任建设 - 子代理派工单（2026-06-24）

真相源:

- `docs/CURRENT_STATE.md`
- `docs/CROWD_DB_NATIONALIZATION_SOURCE_OF_TRUTH.md`
- `docs/ACTIVE_REMEDIATION_2026-06-20.md`
- `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`
- `docs/plans/2026-06-23-national-high-trust-crowd-db-plan.md`

## 1. 当前 live 基线

- 27 省 crowd_db 文件已存在：`27/27`
- 真正全国口径仍缺 4 个自治区：内蒙古 / 广西 / 西藏 / 宁夏
- 当前质量分布：`HIGH=7 / USABLE=6 / LOW=14`
- high：湖南 / 广东 / 江苏 / 山东 / 河北 / 浙江 / 福建
- usable：北京 / 天津 / 上海 / 河南 / 湖北 / 四川
- skeleton：安徽 / 重庆 / 甘肃 / 贵州 / 海南 / 黑龙江 / 江西 / 吉林 / 辽宁 / 青海 / 陕西 / 山西 / 新疆 / 云南

## 2. 目标边界

### Goal-A（当前 goal，先执行）

把 loader 当前支持的 27 省全部推进到：

- 至少 usable
- 重点省份尽量 high
- 文档/测试/契约口径同步

### Goal-B（后续可选）

在 Goal-A 完成后，再补 4 个自治区，形成真正 31 省口径。

## 3. 并行执行总原则

1. 一个子代理不要同时改同一个省文件。
2. 一个子代理不要直接改共享测试文件，测试统一由 controller / test guard 合并。
3. 研究类与写入类尽量分离：
   - 子代理优先做来源核验 / 分批建议 / 学校池候选 / 分数带锚点研究
   - controller 负责省文件写入、真相源文档、测试门禁、最终合并
4. 任何省份升级到 usable/high 后，都必须回写到测试门禁与状态文档。
5. 子代理完成声明一律不可信，必须经过 controller 二次验收：
   - 读取目标文件
   - 重算 `confidence / ranges / recs / alts`
   - 查看 `git diff --stat`
   - 运行共享测试
6. 从 2026-06-24 起，后续新发 crowd_db 子代理默认使用 Hermes delegation 配置：`provider=openai-zhongzhuan`、`model=gpt-5.4`、`reasoning_effort=medium`。
7. **执行策略调整（强制）**：由于本主线已多次出现“子代理口头完成、文件未落地/未达门槛/超时”问题，后续 crowd_db 省文件升级默认改为：
   - 子代理：只做 research-only 辅助（来源 URL、锚点、学校池、建议 bucket）
   - controller：直接写目标 JSON，并统一收口测试与真相源
   - 不再把写文件成败寄托给子代理 summary

## 4. 当前并行批次（已加入 goal）

### Lane A：usable → high 候选批

目标：让已 usable 的 6 省分两批冲 high。

#### A1

- 广东
- 江苏
- 山东

#### A2

- 浙江
- 河北
- 福建

子代理输出要求：

- 省级官方来源入口复核结果
- `score_ranges` / `recommendations` / `alternatives` 计数
- high 缺口清单（若未达标）

### Lane B：skeleton → usable 第一批（高价值省份）

目标：先把最关键 skeleton 省份脱骨架。

#### B1

- 河南
- 湖北
- 四川

#### B2

- 北京
- 上海
- 天津

#### B3

- 安徽
- 辽宁

子代理输出要求：

- usable 所需的最小内容扩充方案
- 省级官方入口是否已可用
- 是否满足 `confidence >= 0.65 / ranges>=6 / recs>=24 / alts>=24`

### Lane C：skeleton → usable 第二批（长尾省份）

#### C1

- 江西
- 重庆
- 海南

#### C2

- 山西
- 吉林
- 黑龙江

#### C3

- 陕西
- 甘肃
- 云南

#### C4

- 贵州
- 青海
- 新疆

子代理输出要求：

- 与 Lane B 相同，但优先追求“usable 脱骨架”，不追求 high

### Lane D：契约与真相源维护（controller 独占）

- `docs/CURRENT_STATE.md`
- `docs/CROWD_DB_NATIONALIZATION_SOURCE_OF_TRUTH.md`
- `docs/ACTIVE_REMEDIATION_2026-06-20.md`
- `docs/ACTIVE_EXECUTION_BOARD_2026-06-20.md`
- `data/crowd_db/README.md`
- `data/crowd_db/SCHEMA.md`
- `data/crowd_db/tests/*`

## 5. 子代理上下文模板（强化版）

后续发省级子代理时，统一带以下上下文骨架，减少“口头完成、实际没落地”：

### 5.1 单省 usable 升级模板

- 你只能修改一个文件：`data/crowd_db/<province>.json`
- 不允许修改 tests / README / SCHEMA / docs / 执行板
- 必须满足：
  - `confidence >= 0.65`
  - `recommendations >= 24`
  - `alternatives >= 24`
  - `last_updated = 2026-06-24`
- 必须覆盖高/中/低分数带
- 必须把 `quality_note` 改成“已完成官方入口与年度锚点复核”的 usable 口径
- 交付时必须返回：
  - `last_updated`
  - `confidence`
  - `ranges`
  - `recs`
  - `alts`
  - 每个 bucket 的 rec/alts 数量

### 5.2 单省 high 升级模板

- 你只能修改一个文件：`data/crowd_db/<province>.json`
- 不允许修改 tests / README / SCHEMA / docs / 执行板
- 必须满足：
  - `confidence >= 0.80`
  - `score_ranges >= 8`
  - `recommendations >= 40`
  - `alternatives >= 60`
  - `last_updated = 2026-06-24`
- `quality_note` / `source` 文案不得再写“仅 usable，不升 high”
- 交付时必须返回：
  - `last_updated`
  - `confidence`
  - `ranges`
  - `recs`
  - `alts`
  - 具体改了哪些 bucket

### 5.3 controller 验收硬门槛

子代理 summary 只作为线索，不作为事实。controller 必须验证：

1. `read_file(target.json)`
2. 统计脚本重算 `ranges/recs/alts/confidence`
3. `git diff --stat -- target.json`
4. 若影响共享口径，再跑：
   - `test_crowd_db_data_quality.py`
   - `test_provenance_query.py`
   - `admin/tests/test_web_public_content_pages.py`

## 6. 验收门禁

### usable

- `confidence >= 0.65`
- `score_ranges >= 6`
- `recommendations >= 24`
- `alternatives >= 24`
- 至少 1 个省级官方来源入口完成年度复核

### high

- `confidence >= 0.80`
- `score_ranges >= 8`
- `recommendations >= 40`
- `alternatives >= 60`
- 覆盖高/中/低至少三层分数带
- 省级官方入口 + 交叉复核证据齐全

## 6. 当前已启动的并行子代理

- `deleg_3ac27bcf`：批次拆分与执行顺序研究
- `deleg_d6500725`：live 省份质量分布与完成率核验
- `deleg_b3748b00`：真相源文档最小改动面分析

## 7. controller 下一步

1. 等待上述 3 个子代理返回结构化建议
2. 将建议折叠进 Lane A/B/C/D 的最终工作单
3. 启动真正的省级写入子代理（每个子代理只负责一个清晰省组）
4. controller 合并测试、文档、状态板
5. 跑 crowd_db 定向测试与统计复核
