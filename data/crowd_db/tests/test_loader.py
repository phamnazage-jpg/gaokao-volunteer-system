"""数据加载器测试"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

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
    # 575分应该在 560-580 范围内
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
        alternatives=[],
    )
    assert rec.frequency == 4
    assert rec.risk_level == "high"  # frequency=4 应该是高风险
