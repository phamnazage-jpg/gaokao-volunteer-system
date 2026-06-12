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
  "score_ranges": [
    {
      "range": [560, 580],
      "recommendations": [
        {
          "name": "长沙理工大学",
          "major": "会计学",
          "frequency": 4,
          "platforms": ["千问", "元宝", "百度", "豆包"],
          "predicted_increase": 18
        }
      ]
    }
  ]
}
```

详见 docs/plans/T1-1-crowd-db-setup.md
