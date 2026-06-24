# 大厂AI推荐数据库 (Crowd Detection Database)

## 用途

存储大厂AI（千问/元宝/百度/豆包）的高频推荐院校，
用于反扎堆检测功能。

## 数据格式

按省份组织，每个JSON文件包含该省的推荐数据 + 溯源元数据（T3.1 schema）：

```json
{
  "province": "湖南",
  "last_updated": "2026-06-12",
  "data_year": 2025,
  "source": "千问/元宝/百度/豆包 公开推荐汇总（手动整理）",
  "source_url": "https://github.com/phamnazage-jpg/gaokao-volunteer-system/blob/main/data/crowd_db/hunan.json",
  "source_type": "manual_summary",
  "confidence": 0.85,
  "score_ranges": [
    {
      "range": [560, 580],
      "note": "一本中段",
      "recommendations": [
        {
          "name": "长沙理工大学",
          "major": "会计学",
          "frequency": 4,
          "platforms": ["千问", "元宝", "百度", "豆包"],
          "predicted_increase": 18,
          "alternatives": [
            { "name": "湖南工商大学", "major": "会计学", "score": 95 },
            { "name": "湖北经济学院", "major": "财务管理", "score": 92 }
          ]
        }
      ]
    }
  ]
}
```

## 字段说明

### 顶层溯源字段（T3.1）

| 字段           | 类型      | 必填 | 说明                                                                  |
| -------------- | --------- | ---- | --------------------------------------------------------------------- |
| `province`     | str       | ✅   | 省份中文名                                                            |
| `last_updated` | str (ISO) | ✅   | 文件最后更新日期 `YYYY-MM-DD`                                         |
| `data_year`    | int       | ✅   | 数据参考年份（如 `2025` 代表基于 2025 高考数据）                      |
| `source`       | str       | ✅   | 数据来源描述（人类可读）                                              |
| `source_url`   | str       | ⚠️   | 数据源 URL；无则填空串                                                |
| `source_type`  | str enum  | ✅   | `manual_summary` / `official_release` / `platform_scrape` / `derived` |
| `confidence`   | float     | ✅   | 数据可信度 `[0.0, 1.0]`；`< 0.5` 视为骨架，loader 打印 UserWarning    |
| `score_ranges` | list      | ✅   | 分数段列表；骨架文件允许 `[]`                                         |

### 分数段与推荐

| 字段                 | 说明                         |
| -------------------- | ---------------------------- |
| `range`              | 分数区间 [min, max]          |
| `note`               | 段名/批次说明                |
| `recommendations`    | 推荐条目列表                 |
| `frequency`          | 4个大厂AI中有几个推荐（0-4） |
| `platforms`          | 具体推荐了哪些AI             |
| `predicted_increase` | 预测2026年分数线上涨分       |
| `alternatives`       | 替代院校推荐                 |

完整 schema 见 [SCHEMA.md](SCHEMA.md)。

## 当前覆盖边界（2026-06-23 真相）

当前 `crowd_db` 的代码与文件口径是 27 省（23 省 + 4 直辖市）：

- 23省：`hebei / shanxi / liaoning / jilin / heilongjiang / jiangsu / zhejiang / anhui / fujian / jiangxi / shandong / henan / hubei / hunan / guangdong / hainan / sichuan / guizhou / yunnan / shaanxi / gansu / qinghai / xinjiang`
- 4直辖市：`beijing / shanghai / tianjin / chongqing`

当前**不含** 4 个尚未接入 crowd_db loader 的自治区：`内蒙古 / 广西 / 西藏 / 宁夏`，也不含港澳台。

因此：

- 当前可以说：`27 省 crowd_db 已建基础骨架`
- 当前不能说：`全国 31 省高信任数据已完成`

如需进入真正“全国”口径，必须同步补：

1. 新增 4 个省级 JSON
2. 更新 `data/crowd_db/loader.py` 的 `PROVINCE_FILE_MAP`
3. 更新 README / SCHEMA / provenance / loader tests

## 数据来源

- 手动整理大厂AI公开推荐
- 高考季后期的实际数据
- 不爬虫、不抓取（合规考虑）
- 高信任白名单（当前 controller 允许进入 high 的省份）: 湖南 / 广东 / 江苏 / 山东
- 其余 3 个已可用省份（河北 / 浙江 / 福建）当前仍为 usable
- 20 个省仍为 skeleton

## 质量分层口径（2026-06-23 起）

### skeleton

- `confidence < 0.5`
- 只可用于占位、来源展示、提示“待补完”

### usable

- `confidence >= 0.65`
- 至少 6 个 `score_ranges`
- 至少 24 条 `recommendations`
- 至少 24 条 `alternatives`
- 至少 1 个省级官方来源入口完成年度复核

### high

- `confidence >= 0.80`
- 至少 8 个 `score_ranges`
- 至少 40 条 `recommendations`
- 至少 60 条 `alternatives`
- 必须覆盖高/中/低至少三层分数带
- 必须完成省级官方来源复核 + 交叉复核

## 更新频率

每周更新一次，高考季（6-7月）每周两次

## Loader 接口（T3.1）

```python
from data.crowd_db.loader import CrowdDBLoader

loader = CrowdDBLoader()

# 1) 取推荐
recs = loader.find_recommendations("湖南", score=575)

# 2) 仅取溯源元数据
meta = loader.load_metadata("湖南")
# → {province, last_updated, data_year, source, source_url, source_type, confidence, record_count}

# 3) 列出全部支持的省份（27 个）
all_p = loader.list_supported_provinces()

# 4) 列出实际存在的省份元数据
existing = loader.list_provinces()
```

完整数据生成脚本（含 27 省份 schema 校验）位于：
`/home/long/.hermes/kanban/workspaces/t_71bdee07/gen_provinces.py`

详见 [docs/plans/T1-1-crowd-db-setup.md](../../docs/plans/T1-1-crowd-db-setup.md)
