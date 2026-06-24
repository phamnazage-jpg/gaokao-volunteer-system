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

## 3. recommendations 元素

| 字段                 | 类型      | 必填 | 说明                               |
| -------------------- | --------- | ---- | ---------------------------------- |
| `name`               | str       | ✅   | 院校名称                           |
| `major`              | str       | ⚠️   | 专业；无专业聚合时填 `""`          |
| `frequency`          | int       | ✅   | 推荐频次（0-4）                    |
| `platforms`          | list[str] | ✅   | 推荐平台名（千问/元宝/百度/豆包）  |
| `predicted_increase` | int       | ⚠️   | 预测分数上涨分；无可靠预测可填 `0` |
| `alternatives`       | list      | ⚠️   | 替代院校推荐，可空                 |

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

## 6. 当前覆盖范围与全国化边界

### 当前代码兼容口径（27 省）

- 23省：河北、山西、辽宁、吉林、黑龙江、江苏、浙江、安徽、福建、江西、山东、河南、湖北、湖南、广东、海南、四川、贵州、云南、陕西、甘肃、青海、新疆
- 4直辖市：北京、上海、天津、重庆

### 当前未纳入 crowd_db loader 的地区

- 4 个自治区：内蒙古、广西、西藏、宁夏
- 港澳台

说明：

- 当前 `data/crowd_db/loader.py` 与相关 tests 只承认 27 省口径
- 如果要升级到真正“全国 31 省”口径，必须同时新增 4 个自治区 JSON、扩 loader 映射，并同步更新 README / tests / 文档真相源

## 7. 验证

```bash
python3 -c "import json,glob; [print(p, list(json.load(open(p)).keys())) for p in sorted(glob.glob('data/crowd_db/*.json'))]"
```

每个文件必须包含上述顶层 8 个字段中的至少 `province / last_updated / data_year / source_type / confidence / score_ranges` 6 个。
