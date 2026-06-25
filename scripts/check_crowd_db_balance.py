#!/usr/bin/env python3
"""crowd_db 均衡性检查（地域 + 专业热度）。

检查项：
1. 地域均衡性：省会院校占比不应过高（非直辖市省份 ≤70%）
2. 专业冷热均衡：热门专业占比不应过高（≤50%），冷门专业不应过低（≥5%）

用途：
- 诊断数据偏差
- 为后续人工审核提供清单
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 省会城市映射
PROVINCE_CAPITALS = {
    "湖南": "长沙",
    "广东": "广州",
    "江苏": "南京",
    "山东": "济南",
    "河北": "石家庄",
    "浙江": "杭州",
    "福建": "福州",
    "安徽": "合肥",
    "河南": "郑州",
    "湖北": "武汉",
    "四川": "成都",
    "陕西": "西安",
    "山西": "太原",
    "辽宁": "沈阳",
    "吉林": "长春",
    "黑龙江": "哈尔滨",
    "江西": "南昌",
    "云南": "昆明",
    "贵州": "贵阳",
    "甘肃": "兰州",
    "青海": "西宁",
    "海南": "海口",
    "新疆": "乌鲁木齐",
    "内蒙古": "呼和浩特",
    "广西": "南宁",
    "宁夏": "银川",
    "西藏": "拉萨",
    "北京": "北京",
    "天津": "天津",
    "上海": "上海",
    "重庆": "重庆",
}

# 专业热度关键词
HOT_MAJORS = [
    "计算机",
    "软件",
    "人工智能",
    "电气",
    "自动化",
    "电子",
    "通信",
    "金融",
    "会计",
    "经济",
    "临床医学",
    "口腔医学",
]

COLD_MAJORS = [
    "农学",
    "林学",
    "园艺",
    "植物保护",
    "动物科学",
    "地质",
    "测绘",
    "矿业",
    "冶金",
    "材料",
    "化工",
    "纺织",
    "轻工",
    "档案",
    "图书馆",
    "民族",
    "哲学",
    "历史",
    "考古",
]

STABLE_MAJORS = [
    "机械",
    "土木",
    "建筑",
    "环境",
    "水利",
    "能源",
    "交通",
    "物流",
    "管理",
    "法学",
    "教育学",
    "外语",
    "新闻",
    "体育",
    "艺术",
    "设计",
]


def classify_major(major: str) -> str:
    """分类专业热度"""
    major = major or ""
    for hot in HOT_MAJORS:
        if hot in major:
            return "热门"
    for cold in COLD_MAJORS:
        if cold in major:
            return "冷门"
    for stable in STABLE_MAJORS:
        if stable in major:
            return "稳健"
    return "其他"


def detect_city_type(school_name: str, province: str) -> str:
    """从院校名称推断所在城市类型。

    规则收紧：
    1. 只有显式命中省会城市名才算“省会”
    2. 不再把“省名/自治区名命中”直接判为省会（如西藏大学/宁夏大学会误判）
    3. 直辖市（北京/上海/天津/重庆）仍按直辖市主城区处理
    4. 含学院/职业/师范/理工/工业/农业/医科/财经/民族 等但不含省会名，按“地级市”或“其他”
    """
    capital = PROVINCE_CAPITALS.get(province, "")
    # 直辖市
    if province in {"北京", "上海", "天津", "重庆"} and capital in school_name:
        return "省会"
    # 只有显式命中省会城市名才算省会
    if capital and capital in school_name:
        return "省会"
    # 国家/区域级院校大多位于省会或核心城市，但不强制判省会
    if any(
        kw in school_name
        for kw in [
            "中国",
            "中央",
            "华中",
            "华东",
            "华北",
            "华南",
            "西南",
            "西北",
            "东北",
        ]
    ):
        return "省会"
    # 含明显高校/职业院校关键词，但未命中省会城市，默认按地级市处理
    if any(
        kw in school_name
        for kw in [
            "学院",
            "职业",
            "师范",
            "理工",
            "工业",
            "农业",
            "医科",
            "财经",
            "民族",
            "警官",
            "科技",
            "工程",
        ]
    ):
        return "地级市"
    return "其他"


def main() -> int:
    # 地域统计
    location_stats: dict[str, Counter] = defaultdict(Counter)
    # 专业热度统计
    major_stats: dict[str, Counter] = defaultdict(Counter)

    for path in sorted((ROOT / "data/crowd_db").glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        province = d.get("province", "")
        if not province:
            continue

        schools_seen = set()
        for sr in d.get("score_ranges", []):
            for rec in sr.get("recommendations", []):
                # 地域统计（去重院校）
                school = rec.get("name", "")
                if school not in schools_seen:
                    schools_seen.add(school)
                    city_type = detect_city_type(school, province)
                    location_stats[province][city_type] += 1

                # 专业热度统计
                major = rec.get("major", "")
                major_cat = classify_major(major)
                major_stats[province][major_cat] += 1

    issues = []

    # 检查地域均衡性（非直辖市省份）
    municipalities = {"北京", "上海", "天津", "重庆"}
    for province, stats in location_stats.items():
        if province in municipalities:
            continue
        total = sum(stats.values())
        if total > 0:
            capital_pct = stats["省会"] / total
            if capital_pct > 0.7:
                issues.append(
                    f"[地域均衡] {province} 省会院校占比过高: {capital_pct:.1%} (应 ≤70%)"
                )

    # 检查专业冷热均衡
    for province, stats in major_stats.items():
        total = sum(stats.values())
        if total > 0:
            hot_pct = stats["热门"] / total
            cold_pct = stats["冷门"] / total
            if hot_pct > 0.5:
                issues.append(
                    f"[专业均衡] {province} 热门专业占比过高: {hot_pct:.1%} (应 ≤50%)"
                )
            if cold_pct < 0.05:
                issues.append(
                    f"[专业均衡] {province} 冷门专业占比过低: {cold_pct:.1%} (应 ≥5%)"
                )

    # 输出
    if issues:
        print("❌ crowd_db 均衡性检查发现问题：")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("✅ crowd_db 均衡性检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
