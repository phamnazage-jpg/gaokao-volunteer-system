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

    name: str  # 院校名称
    major: str  # 专业
    frequency: int  # 推荐频次（0-4）
    platforms: List[str]  # 推荐平台列表
    predicted_increase: int  # 预测分数上涨
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
    # __file__ = <root>/data/crowd_db/loader.py
    # dirname x3 → project root, then join data/crowd_db
    DATA_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "crowd_db",
    )

    # 省份名 → JSON 文件名 映射（拼音风格）
    PROVINCE_FILE_MAP = {
        "湖南": "hunan",
        "浙江": "zhejiang",
        "湖北": "hubei",
        "广东": "guangdong",
        "北京": "beijing",
        "上海": "shanghai",
        "江苏": "jiangsu",
        "四川": "sichuan",
        "山东": "shandong",
        "河南": "henan",
        "全国": "national",
    }

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

        # 解析文件名：先查映射，缺失时尝试 province.json / {province}.json 两种命名
        candidates = []
        slug = self.PROVINCE_FILE_MAP.get(province)
        if slug:
            candidates.append(f"{slug}.json")
        candidates.append(f"{province}.json")

        for filename in candidates:
            file_path = os.path.join(self.data_dir, filename)
            if not os.path.exists(file_path):
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._cache[province] = data
                return data
            except (json.JSONDecodeError, IOError):
                continue

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
        self, province: str, school_name: str
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
        print(
            f"  - {rec['name']} {rec['major']} (频次:{rec['frequency']}, +{rec['predicted_increase']}分)"
        )
