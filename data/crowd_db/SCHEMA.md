# Crowd DB 溯源数据 Schema (T3.1)

> **For Hermes:** 数据溯源 / provenance schema for `data/crowd_db/{province}.json`
>
> 配套 T3.1「扩展院校数据模型」：27省JSON含溯源字段。

## 1. 顶层（每个省份文件根节点）

| 字段              | 类型         | 必填 | 说明                                                                  |
| ----------------- | ------------ | ---- | --------------------------------------------------------------------- |
| `province`        | str          | ✅   | 省份中文名（如 `湖南`），需与 loader.PROVINCE_FILE_MAP 的 key 对齐    |
| `last_updated`    | str (ISO)    | ✅   | 本文件最后更新日期，格式 `YYYY-MM-DD`                                 |
| `data_year`       | int          | ✅   | 数据的参考年份（如 `2025` 表示基于 2025 高考数据）                    |
| `source`          | str          | ✅   | 数据来源描述（人类可读），如 `千问/元宝/百度/豆包 公开推荐汇总`       |
| `source_url`      | str          | ⚠️   | 主参考来源 URL；不得使用仓库自引用路径冒充来源证明                    |
| `source_type`     | str enum     | ✅   | `manual_summary` / `official_release` / `platform_scrape` / `derived` |
| `confidence`      | float        | ✅   | 数据可信度，区间 `[0.0, 1.0]`；0.5 以下视为不可用，触发人工复核提示   |
| `score_ranges`    | list         | ✅   | 分数段列表（结构见下节）；骨架文件允许 `[]` 表示待人工整理            |
| `trusted_sources` | list[object] | ⚠️   | 可信参考源数组；用于记录后续年度复核应优先使用的官方/权威来源         |
| `quality_note`    | str          | ⚠️   | 对当前省份数据可信度口径的人工说明（如“高置信人工整理”/“结构化骨架”） |

### source_type 枚举

- `manual_summary`：人工整理（最常见，T2.1 湖南数据走此路径）
- `official_release`：省考试院 / 教育部官方公告
- `platform_scrape`：从大厂AI公开页抽取（注意合规边界）
- `derived`：由其它数据派生（如 985/211 名单）

## 2. score_ranges 元素

| 字段              | 类型      | 必填 | 说明                           |
| ----------------- | --------- | ---- | ------------------------------ |
| `range`           | [int,int] | ✅   | 分数区间 `[min, max]`，闭区间  |
| `note`            | str       | ⚠️   | 段名/批次说明（如 `一本中段`） |
| `recommendations` | list      | ✅   | 推荐条目列表，可空             |

## 2.1 score_distribution（一分一段表，顶层）

> 2026-06-25 Phase A 新增：用于存放官方公布的一分一段表/位次数据。

```json
{
  "score_distribution": {
    "data_year": 2026,
    "source_url": "https://www.hneeb.cn/...",
    "source_type": "official_release",
    "last_updated": "2026-06-25",
    "subjects": {
      "物理": {
        "benchmarks": [
          {"score": 700, "cumulative_count": 17},
          {"score": 690, "cumulative_count": 80},
          {"score": 600, "cumulative_count": 6580}
        ],
        "score_line_at_600": 18876,
        "total_above_bachelor_line": 82444,
        "bachelor_score_line": 340
      },
      "历史": {
        "benchmarks": [
          {"score": 670, "cumulative_count": 15},
          {"score": 600, "cumulative_count": 857}
        ],
        "score_line_at_600": 2139,
        "total_above_bachelor_line": 21417,
        "bachelor_score_line": 385
      }
    }
  }
}
```

说明：
- `score_distribution` 为可选顶层字段，未接入一分一段表的省份省略
- `subjects` 分物理类/历史类（新高考省份）或理科/文科（旧高考省份）
- `benchmarks` 为关键分数段锚点（从一分一段表采样）
- `score_line_at_600` 为 600 分以上考生总数
- `total_above_bachelor_line` 为本科线上累计人数
- `bachelor_score_line` 为本科分数线

## 3. recommendations 元素

| 字段                 | 类型      | 必填 | 说明                               |
| -------------------- | --------- | ---- | ---------------------------------- |
| `name`               | str       | ✅   | 院校名称                           |
| `major`              | str       | ⚠️   | 专业；无专业聚合时填 `""`          |
| `subject_requirements` | object/null | ⚠️ | 新高考省份选科要求；历史推荐不填时为 `null` |
| `program_type`       | str/null  | ⚠️   | 特殊类型（定向培养/专项计划/公费师范等）；无则为 `null` |
| `frequency`          | int       | ✅   | 推荐频次（0-4）                    |
| `platforms`          | list[str] | ✅   | 推荐平台名（千问/元宝/百度/豆包）  |
| `predicted_increase` | int       | ⚠️   | 预测分数上涨分；无可靠预测可填 `0` |
| `alternatives`       | list      | ⚠️   | 替代院校推荐，可空                 |

### `subject_requirements` 结构

```json
{
  "preferred_subject": "物理",
  "reselect_subject": ["化学", "生物"],
  "note": "首选物理，再选化学/生物"
}
```

说明：
- `preferred_subject`: 首选科目（物理/历史）
- `reselect_subject`: 再选科目组合，可为空 list
- `note`: 人类可读说明
- 旧高考省份或选科要求未整理时填 `null`

### `program_type` 枚举

常见值：
- `定向培养`
- `国家专项`
- `地方专项`
- `高校专项`
- `中外合作办学`
- `公费师范生`
- `军校`
- `公安院校`
- `艺体类`
- `null`（普通专业）

## 4. `trusted_sources` 元素

推荐结构：

```json
{
  "name": "教育部阳光高考",
  "url": "https://gaokao.chsi.com.cn/",
  "kind": "national_official"
}
```

说明：

- `name`: 来源名称
- `url`: 入口 URL；如仅确认机构类型、尚未完成年度入口复核，可暂为空串
- `kind`: `national_official` / `province_official_pending_review` / 其他内部约定枚举

## 5. 骨架文件约定

未完整整理数据的省份，应输出符合顶层 schema 的骨架：

```json
{
  "province": "山东",
  "last_updated": "2026-06-12",
  "data_year": 2025,
  "source": "",
  "source_url": "",
  "source_type": "manual_summary",
  "confidence": 0.0,
  "score_ranges": []
}
```

骨架文件 `confidence=0.0`，loader 应在 `confidence < 0.5` 时打印 WARN 但不抛错（避免阻断运行）。

## 6. 质量等级门槛定义

质量等级判定采用**综合门槛**（confidence + score_ranges + recommendations + alternatives + 分数带覆盖），而非仅依赖 confidence。

门槛来源：`docs/plans/2026-06-23-national-high-trust-crowd-db-plan.md` §4

### 6.1 skeleton（骨架）

- `confidence < 0.5`
- 用途：UI 占位、provenance 展示、告知"该省数据仍待人工补完"
- **不允许**驱动反扎堆强结论

### 6.2 low（建设中）

- `confidence >= 0.5` 但未达 usable 门槛
- 或 `confidence >= 0.65` 但 recommendations / alternatives 不达标
- 用途：标识"已脱离骨架但未达可用"，区别于 skeleton

### 6.3 usable（可用）

必须**同时满足**：
- `confidence >= 0.65`
- `score_ranges >= 6` 个分数段
- `recommendations >= 24` 条
- `alternatives >= 24` 条
- 至少 1 个省级官方来源入口完成年度复核

用途：普通省份的基础反扎堆分析、用户侧展示"中等信任"标签

### 6.4 high（高置信）

必须**同时满足**：
- `confidence >= 0.80`
- `score_ranges >= 8` 个分数段
- `recommendations >= 40` 条
- `alternatives >= 60` 条
- 覆盖高/中/低**至少三层分数带**（而非只覆盖头部段）
- 省级官方入口已完成年度复核

用途：核心省份的反扎堆强结论、用户侧展示"高信任"标签

### 6.5 防静默升级

判定逻辑位于 `data/crowd_db/risk_report.py::_compute_quality_level`。

**禁止**仅修改 confidence 值就升级 quality_level；必须同时补齐 score_ranges / recommendations / alternatives。

## 7. 当前覆盖范围与全国化边界

### 当前代码兼容口径（31 省，2026-06-25 Stage 4 起全国化）

- 23省：河北、山西、辽宁、吉林、黑龙江、江苏、浙江、安徽、福建、江西、山东、河南、湖北、湖南、广东、海南、四川、贵州、云南、陕西、甘肃、青海、新疆
- 4直辖市：北京、上海、天津、重庆
- 4自治区（Stage 4 新增）：内蒙古、广西、西藏、宁夏

### 港澳台（未纳入）

- 港澳台地区暂未纳入 crowd_db loader

## 7. 验证

```bash
python3 -c "import json,glob; [print(p, list(json.load(open(p)).keys())) for p in sorted(glob.glob('data/crowd_db/*.json'))]"
```

每个文件必须包含上述顶层 8 个字段中的至少 `province / last_updated / data_year / source_type / confidence / score_ranges` 6 个。
