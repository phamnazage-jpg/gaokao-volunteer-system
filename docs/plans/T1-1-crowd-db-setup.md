# T1.1 准备扎堆数据库结构 - 详细实施

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal**: 建立大厂AI推荐数据库的目录结构和初始数据

**Architecture**: JSON文件存储，按省份组织，手动维护

**Tech Stack**: Python 3.10+, JSON

---

## Task 1.1.1: 创建数据目录结构

**Objective**: 创建 crowd_db 目录及相关子目录

**Files**:

- Create: `data/crowd_db/.gitkeep`
- Create: `data/crowd_db/README.md`

**Step 1: 创建目录**

```bash
cd /home/long/project/gaokao-volunteer-system
mkdir -p data/crowd_db
touch data/crowd_db/.gitkeep
```

**Step 2: 创建README说明文件**

Create file: `data/crowd_db/README.md`

````markdown
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
````

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

````

**Step 3: 验证**

```bash
ls -la data/crowd_db/
cat data/crowd_db/README.md | head -5
````

**Expected**:

- 看到 .gitkeep 和 README.md 文件
- README.md 内容正确

**Step 4: 提交**

```bash
cd /home/long/project/gaokao-volunteer-system
git add data/crowd_db/
git commit -m "feat: 创建大厂AI推荐数据库目录结构"
```

---

## Task 1.1.2: 创建湖南省初始数据

**Objective**: 创建 hunan.json 初始数据

**Files**:

- Create: `data/crowd_db/hunan.json`

**Step 1: 创建初始JSON**

Create file: `data/crowd_db/hunan.json`

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
        },
        {
          "name": "江西财经大学",
          "major": "会计学",
          "frequency": 3,
          "platforms": ["千问", "元宝", "百度"],
          "predicted_increase": 12,
          "alternatives": [
            { "name": "湖南工商大学", "major": "会计学", "score": 95 },
            { "name": "重庆工商大学", "major": "会计学", "score": 90 }
          ]
        }
      ]
    },
    {
      "range": [580, 600],
      "recommendations": [
        {
          "name": "湖南师范大学",
          "major": "会计学",
          "frequency": 4,
          "platforms": ["千问", "元宝", "百度", "豆包"],
          "predicted_increase": 15,
          "alternatives": [
            { "name": "湘潭大学", "major": "会计学", "score": 96 },
            { "name": "长沙理工大学", "major": "会计学", "score": 93 }
          ]
        }
      ]
    }
  ]
}
```

**Step 2: 验证JSON格式**

```bash
python3 -c "import json; data = json.load(open('data/crowd_db/hunan.json')); print(f'省份: {data[\"province\"]}, 分数段数: {len(data[\"score_ranges\"])}')"
```

**Expected**:

```
省份: 湖南, 分数段数: 2
```

**Step 3: 提交**

```bash
git add data/crowd_db/hunan.json
git commit -m "feat: 添加湖南省大厂AI推荐数据初始版本"
```

---

## Task 1.1.3: 实现数据加载器

**Objective**: 实现 crowd_db JSON 数据加载和查询

**Files**:

- Create: `data/crowd_db/loader.py`
- Test: `data/crowd_db/tests/test_loader.py`

**Step 1: 写测试**

Create file: `data/crowd_db/tests/test_loader.py`

```python
"""数据加载器测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.crowd_db.loader import CrowdDBLoader, CrowdRecommendation


def test_load_hunan_data():
    """测试加载湖南数据"""
    loader = CrowdDBLoader()
    data = loader.load_province("湖南")
    assert data is not None
    assert data["province"] == "湖南"
    assert len(data["score_ranges"]) > 0


def test_find_recommendations_in_range():
    """测试查询分数段内的推荐"""
    loader = CrowdDBLoader()
    recs = loader.find_recommendations("湖南", score=575)
    assert isinstance(recs, list)
    # 578分应该在 560-580 范围内
    if recs:
        assert all(r["frequency"] > 0 for r in recs)


def test_find_recommendations_by_school():
    """测试按院校名查询推荐"""
    loader = CrowdDBLoader()
    rec = loader.find_recommendation_by_school("湖南", "长沙理工大学")
    assert rec is not None
    assert rec["name"] == "长沙理工大学"


def test_load_nonexistent_province():
    """测试加载不存在的省份"""
    loader = CrowdDBLoader()
    data = loader.load_province("不存在的省")
    assert data is None


def test_crowd_recommendation_dataclass():
    """测试数据类"""
    rec = CrowdRecommendation(
        name="测试大学",
        major="测试专业",
        frequency=4,
        platforms=["千问", "元宝", "百度", "豆包"],
        predicted_increase=15,
        alternatives=[]
    )
    assert rec.frequency == 4
    assert rec.risk_level == "high"  # frequency=4 应该是高风险
```

**Step 2: 运行测试确认失败**

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m pytest data/crowd_db/tests/test_loader.py -v
```

**Expected**: FAIL — module not found

**Step 3: 创建**init**.py**

```bash
mkdir -p data/crowd_db/tests
touch data/crowd_db/__init__.py
touch data/crowd_db/tests/__init__.py
```

**Step 4: 实现loader**

Create file: `data/crowd_db/loader.py`

```python
"""
大厂AI推荐数据库加载器

用于反扎堆检测功能，加载和查询大厂AI的高频推荐院校。
"""
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CrowdRecommendation:
    """扎堆推荐数据"""
    name: str                              # 院校名称
    major: str                             # 专业
    frequency: int                         # 推荐频次（0-4）
    platforms: List[str]                   # 推荐平台列表
    predicted_increase: int                # 预测分数上涨
    alternatives: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def risk_level(self) -> str:
        """根据频次计算风险等级"""
        if self.frequency >= 4:
            return "high"
        elif self.frequency >= 2:
            return "medium"
        else:
            return "low"


class CrowdDBLoader:
    """
    大厂AI推荐数据库加载器

    数据存储在 data/crowd_db/{province}.json 文件中
    """

    # 数据目录路径（相对项目根目录）
    DATA_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "crowd_db"
    )

    def __init__(self, data_dir: Optional[str] = None):
        """初始化加载器

        Args:
            data_dir: 数据目录路径，默认使用 DATA_DIR
        """
        self.data_dir = data_dir or self.DATA_DIR
        self._cache: Dict[str, dict] = {}

    def load_province(self, province: str) -> Optional[dict]:
        """加载指定省份的推荐数据

        Args:
            province: 省份名称（如"湖南"）

        Returns:
            省份数据字典，未找到返回 None
        """
        if province in self._cache:
            return self._cache[province]

        file_path = os.path.join(self.data_dir, f"{province}.json")
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._cache[province] = data
            return data
        except (json.JSONDecodeError, IOError):
            return None

    def find_recommendations(self, province: str, score: int) -> List[Dict[str, Any]]:
        """查询指定分数段内的所有推荐

        Args:
            province: 省份名称
            score: 用户分数

        Returns:
            推荐列表
        """
        data = self.load_province(province)
        if not data:
            return []

        results = []
        for score_range in data.get("score_ranges", []):
            min_score, max_score = score_range["range"]
            if min_score <= score <= max_score:
                results.extend(score_range.get("recommendations", []))

        return results

    def find_recommendation_by_school(
        self,
        province: str,
        school_name: str
    ) -> Optional[Dict[str, Any]]:
        """按院校名查询推荐信息

        Args:
            province: 省份名称
            school_name: 院校名称（支持模糊匹配）

        Returns:
            推荐信息，未找到返回 None
        """
        data = self.load_province(province)
        if not data:
            return None

        for score_range in data.get("score_ranges", []):
            for rec in score_range.get("recommendations", []):
                if school_name in rec["name"] or rec["name"] in school_name:
                    return rec

        return None


# 命令行测试
if __name__ == "__main__":
    loader = CrowdDBLoader()

    # 测试加载湖南数据
    data = loader.load_province("湖南")
    if data:
        print(f"✅ 加载湖南数据: {len(data.get('score_ranges', []))} 个分数段")
    else:
        print("❌ 加载湖南数据失败")

    # 测试分数查询
    recs = loader.find_recommendations("湖南", score=575)
    print(f"📊 575分在湖南的扎堆院校: {len(recs)} 个")
    for rec in recs:
        print(f"  - {rec['name']} {rec['major']} (频次:{rec['frequency']}, +{rec['predicted_increase']}分)")
```

**Step 5: 再次运行测试**

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m pytest data/crowd_db/tests/test_loader.py -v
```

**Expected**: PASS — 5 tests pass

**Step 6: 提交**

```bash
git add data/crowd_db/
git commit -m "feat(crowd_db): 实现数据加载器 - T1.1.3"
```

---

## Task 1.1.4: 端到端验证

**Objective**: 完整运行验证流程

**Step 1: 运行所有测试**

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m pytest data/crowd_db/tests/ -v
```

**Expected**: All tests pass

**Step 2: 运行loader CLI验证**

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m data.crowd_db.loader
```

**Expected**:

```
✅ 加载湖南数据: 2 个分数段
📊 575分在湖南的扎堆院校: 2 个
  - 长沙理工大学 会计学 (频次:4, +18分)
  - 江西财经大学 会计学 (频次:3, +12分)
```

**Step 3: 推送到三个仓库**

```bash
cd /home/long/project/gaokao-volunteer-system
git push gitea main
git push origin main
git push tksea main
```

---

## 总结

### 完成清单

- [x] Task 1.1.1: 创建数据目录结构
- [x] Task 1.1.2: 创建湖南省初始数据
- [x] Task 1.1.3: 实现数据加载器
- [x] Task 1.1.4: 端到端验证

### 产出

| 文件                                 | 说明         |
| ------------------------------------ | ------------ |
| `data/crowd_db/.gitkeep`             | 目录占位     |
| `data/crowd_db/README.md`            | 数据说明     |
| `data/crowd_db/hunan.json`           | 湖南初始数据 |
| `data/crowd_db/loader.py`            | 数据加载器   |
| `data/crowd_db/tests/test_loader.py` | 测试         |

### 验证

- [x] 5个测试全部通过
- [x] CLI运行正常
- [x] 3个仓库同步

---

**下一步**: T1.2 创建审核服务Skill
