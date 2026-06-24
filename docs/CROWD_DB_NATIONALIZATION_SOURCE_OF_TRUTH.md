# CROWD_DB_NATIONALIZATION_SOURCE_OF_TRUTH

最后更新: 2026-06-23
状态词: 全国高信任建设已启动（Phase 0 收口中，Batch 1 样板省准备执行）
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

### Phase 0 / Batch 0

- 收口 README / SCHEMA / CURRENT*STATE / ACTIVE*\* 的边界表述
- 建立新的高信任分层口径

### Batch 1 样板省

- 广东
- 江苏
- 山东

当前进展（2026-06-23）:

- 广东 / 江苏 / 山东 / 浙江 / 河北 / 福建 六省 `trusted_sources` 已完成省级官方入口复核（`province_official`）
- 山东/广东/江苏 已升级为 high：`confidence=0.85`、`score_ranges=8`、`recommendations=40`、`alternatives=80`
- 河北 已升级为 high：`confidence=0.85`、`score_ranges=8`、`recommendations=40`、`alternatives=80`
- 3 个 usable: 浙江 / 福建 / （后续仍在推进的 skeleton 省份暂不列）
- 当前 high 已扩展为 5 省：湖南 / 广东 / 江苏 / 山东 / 河北；其余 2 个可用省仍为 usable

目标：

- 跑通“来源核验 → 内容扩充 → 交叉复核 → 定级 → 测试同步”的省级流水线
- 不要求本批结束前就宣称全国完成

## 5. 禁止表述

禁止：

- “全国高信任数据已建立”
- “27 省都已是高信任推荐”
- “已补 trusted_sources = 已完成高信任建设”

允许：

- “全国高信任建设已启动”
- “当前湖南 high，其余省份仍在 skeleton → usable/high 升级过程中”
- “广东/江苏/山东为第一批高价值样板省”
