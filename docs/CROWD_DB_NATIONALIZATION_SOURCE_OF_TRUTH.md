# CROWD_DB_NATIONALIZATION_SOURCE_OF_TRUTH

最后更新: 2026-06-25
状态词: 全国 31 省高信任建设完成（Phase 0 + Batch 1 + Stage 1-4 全部完成，31 省 100% 达 high）
上游真相源: `docs/CURRENT_STATE.md`
详细设计: `docs/plans/2026-06-23-national-high-trust-crowd-db-plan.md`

## 1. 当前真实状态（live 基线）

- 当前 `data/crowd_db/*.json` 实存 31 个文件
- 当前 `data/crowd_db/loader.py` 已支持全国 31 省级行政区（23 省 + 4 直辖市 + 4 自治区）
- 当前 live 质量分布：`HIGH=31 / USABLE=0 / LOW=0 / SKELETON=0`
- 当前 31 省全部达到 high；其中 7 省达到 S 级（湖南 / 广东 / 江苏 / 山东 / 河北 / 浙江 / 福建），其余 24 省为 A 级 high
- 当前可以对外表述为“crowd_db 全国 31 省口径已全部达到 high”，但仍**不能**表述为“已具备真实录取位次/真实官方录取数据全量接入”

## 2. 全国口径边界

必须区分两层口径：

### 口径 A：数据覆盖与 high 质量门槛

- 31 省文件存在，loader 可加载，quality_summary 判定全部为 high
- 完成标准：`python -m data.crowd_db.quality_summary --human` 显示 `high=31 / usable=0 / skeleton=0`

### 口径 B：真实录取数据深度

- 当前仍以 `manual_summary` + 可信来源校核为主
- 但 2026-06-26 最新实测已从 **27 省** 提升到 **29 省** 接入 `score_distribution`
- 新增完成：**广西 / 宁夏** 已接入 2026 官方一分一档 / 一分段统计与本科线
- 当前尚未接入 `score_distribution` 的只剩 **新疆 / 西藏**
- 尚未达到“31 省真实录取位次/真实官方录取数据全量接入”
- 因此可以说“31 省 high coverage 完成，29/31 省一分一段深度接入完成”，不能说“31 省真实录取数据建设完成”

当前执行决定：

- 31 省 high coverage 已完成
- 29 省 `score_distribution` 已完成，剩余 2 省待官方稳定来源/可提取结构补齐
- 后续如继续推进，应聚焦数据深度升级而非 coverage 补洞

## 3. 新的质量分层标准

### skeleton

- `confidence < 0.5`
- 只允许占位/来源展示
- 不允许驱动强反扎堆结论

### usable

- `confidence >= 0.65`
- `score_ranges >= 6`
- `recommendations >= 24`
- `alternatives >= 24`
- 至少 1 个省级官方来源入口已年度复核

### high

- `confidence >= 0.80`
- `score_ranges >= 8`
- `recommendations >= 40`
- `alternatives >= 60`
- 必须覆盖高/中/低至少三层分数带
- 必须有省级官方来源入口与交叉复核证据

## 4. 当前执行顺序

### Phase 0 / Batch 0 — ✅ 已完成

- 收口 README / SCHEMA / CURRENT*STATE / ACTIVE*\* 的边界表述
- 建立新的高信任分层口径（含综合门槛判定）

### Batch 1 样板省 — ✅ 已完成

**当前真实状态**（2026-06-25 实测）：

- **31 省 100% 达 high**（confidence≥0.82、score_ranges≥8、recommendations≥40、alternatives≥80、覆盖高/中/低三层分数带）
- usable = 0 省 / skeleton = 0 省
- 详细质量分布见 `docs/CURRENT_STATE.md` 顶部状态词与 `python -m data.crowd_db.quality_summary --human`

**历史执行轨迹**（仅供审计）：

- 6/20 基线：4 high + 3 usable + 20 skeleton
- 6/23：升级到 5 high（+河北）
- 6/24：升级到 7 high（+浙江/福建）/ 20 usable / 0 skeleton
- 6/25 门槛硬化：质量判定从"仅看 confidence"升级为综合门槛
- 6/25 Stage 1：升级到 12 high（+河南/四川/湖北/北京/上海）/ 15 usable / 0 skeleton
- 6/25 Stage 2：27 省 100% 达 high（15 省批量扩容完毕）/ 0 usable / 0 skeleton
- 6/25 Stage 3：7 省 S 级（湖南基线）/ 24 省 A 级（广东/江苏/山东/河北/浙江/福建 升 S）
- 6/25 Stage 4：全国 31 省口径完成（新增内蒙古/广西/西藏/宁夏）/ 31 high / 0 usable / 0 skeleton

目标：

- 跑通"来源核验 → 内容扩充 → 交叉复核 → 定级 → 测试同步"的省级流水线
- 不要求本批结束前就宣称全国完成

## 5. 当前口径边界（2026-06-25 Stage 4 后）

### 全国 31 省口径已建立

- 31 省（23 省 + 4 直辖市 + 4 自治区）全部达 high
- 7 省（湖南/广东/江苏/山东/河北/浙江/福建）达 S 级（湖南基线）
- 24 省达 A 级（high 达标）
- 仍可继续推进的：深化内容质量、增加真实录取位次、扩 alts 池

### 港澳台仍未纳入

- 港澳台地区暂未纳入 crowd_db loader（与大陆招生体系不同）

### 禁止表述（已不适用，保留为历史参考）

历史禁止的"全国高信任数据已建立"在 6/25 Stage 4 后已可正式表述。
但"已具备真实录取位次"等仍不可表述，当前数据仍是 manual_summary 类型。
