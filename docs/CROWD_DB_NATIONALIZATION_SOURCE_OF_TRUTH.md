# CROWD_DB_NATIONALIZATION_SOURCE_OF_TRUTH

最后更新: 2026-06-25
状态词: 全国 31 省高信任建设完成（Phase 0 + Batch 1 + Stage 1-4 全部完成，31 省 100% 达 high）
上游真相源: `docs/CURRENT_STATE.md`
详细设计: `docs/plans/2026-06-23-national-high-trust-crowd-db-plan.md`

## 1. 当前真实状态（live 基线）

- 当前 `data/crowd_db/*.json` 实存 27 个文件
- 当前 `data/crowd_db/loader.py` 仅支持 27 省（23 省 + 4 直辖市）
- 当前 live 质量分布：`HIGH=7 / USABLE=20 / LOW=0`
- high 白名单: 湖南 / 广东 / 江苏 / 山东 / 河北 / 浙江 / 福建
- usable: 北京 / 天津 / 上海 / 河南 / 湖北 / 四川 / 辽宁 / 江西 / 重庆 / 海南 / 安徽 / 山西 / 云南 / 贵州 / 甘肃 / 黑龙江 / 吉林 / 陕西 / 青海 / 新疆
- 当前 27 省口径下已无 skeleton 省份
- 当前可以对外表述为“27 省 crowd_db 已全部达到 usable 及以上”，但仍**不能**表述为“31 省全国高信任数据已完成”

## 2. 全国口径边界

必须区分两层口径：

### 口径 A：当前代码兼容口径

- 先把 loader 已支持的 27 省全部升级
- 完成标准：27 省全部至少 usable，关键省份达 high

### 口径 B：真正全国口径

- 在 27 省基础上补 4 个自治区：`内蒙古 / 广西 / 西藏 / 宁夏`
- 完成标准：31 个省级行政区全部至少 usable，关键省份达 high

当前执行决定：

- 先按口径 A 推进
- 不把 27 省升级误报为“31 省全国化已完成”

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
