# 大厂AI推荐数据库 (Crowd Detection Database)

## 用途

存储大厂AI（千问/元宝/百度/豆包）的高频推荐院校，
用于反扎堆检测功能。

## 数据格式

按省份组织，每个JSON文件包含该省的推荐数据：

```json
{
  "province": "湖南",
  "last_updated": "2026-06-15",
  "data_year": 2025,
  "score_ranges": [
    {
      "range": [560, 580],
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

| 字段                 | 说明                         |
| -------------------- | ---------------------------- |
| `range`              | 分数区间 [min, max]          |
| `frequency`          | 4个大厂AI中有几个推荐（0-4） |
| `platforms`          | 具体推荐了哪些AI             |
| `predicted_increase` | 预测2026年分数线上涨分       |
| `alternatives`       | 替代院校推荐                 |

## 数据来源

- 手动整理大厂AI公开推荐
- 高考季后期的实际数据
- 不爬虫、不抓取（合规考虑）

## 更新频率

每周更新一次，高考季（6-7月）每周两次

## 文件命名

- `hunan.json` - 湖南省
- `zhejiang.json` - 浙江省
- `national.json` - 全国通用

详见 docs/plans/T1-1-crowd-db-setup.md
