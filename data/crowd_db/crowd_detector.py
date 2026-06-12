"""扎堆检测算法 (T2.3)

核心入口：detect_crowd_risk(plan, user_score, province) -> list[RiskFinding]

算法步骤：
1. 加载省份对应的 crowd_db（使用 CrowdDBLoader）
2. 遍历用户方案（plan）每条志愿
3. 在 crowd_db 的对应分数段中查找匹配
4. 风险等级根据 frequency 划分：
   - frequency >= 4: high
   - frequency 2-3 : medium
   - frequency 1   : low
   - frequency 0   : 跳过（不构成扎堆）
5. 返回 RiskFinding 列表（按 frequency 降序）+ 替代方案
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Optional, Union

from data.crowd_db.loader import CrowdDBLoader, CrowdRecommendation


# 兼容多种 plan 条目形态：dict / dataclass / tuple
PlanEntry = Union[Dict[str, Any], CrowdRecommendation, tuple, list]


def plan_entry(school: str, major: Optional[str] = None) -> Dict[str, Any]:
    """构造一条 plan 条目（dict 形态）。供调用方与测试使用。"""
    return {"school": school, "major": major}


@dataclass
class RiskFinding:
    """扎堆检测结果中的一条风险记录"""

    school: str
    major: Optional[str]
    frequency: int
    risk_level: str
    platforms: List[str] = field(default_factory=list)
    predicted_increase: int = 0
    alternatives: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _normalize_entry(entry: PlanEntry) -> Dict[str, Any]:
    """把各种形态的 plan 条目统一为 dict。

    支持：
    - dict（必须有 school，可选 major）
    - CrowdRecommendation（name -> school, major 保留）
    - tuple / list（[school, major] 或 [school]）
    """
    if isinstance(entry, dict):
        return {
            "school": entry.get("school") or entry.get("name") or "",
            "major": entry.get("major"),
        }
    if isinstance(entry, CrowdRecommendation):
        return {"school": entry.name, "major": entry.major}
    if isinstance(entry, (tuple, list)):
        if len(entry) >= 2:
            return {"school": entry[0], "major": entry[1]}
        if len(entry) == 1:
            return {"school": entry[0], "major": None}
    return {"school": str(entry), "major": None}


def _risk_level_from_frequency(frequency: int) -> str:
    """根据推荐频次计算风险等级。"""
    if frequency >= 4:
        return "high"
    if frequency >= 2:
        return "medium"
    if frequency >= 1:
        return "low"
    return "none"  # 0 不构成风险


def _school_matches(school_a: str, school_b: str) -> bool:
    """院校名模糊匹配：任一方向包含即视为匹配。"""
    if not school_a or not school_b:
        return False
    return school_a in school_b or school_b in school_a


def _major_matches(plan_major: Optional[str], rec_major: str) -> bool:
    """专业匹配规则：
    - 计划未指定专业（None / 空）：按院校命中即可
    - 计划指定专业：完全相等视为匹配
    """
    if not plan_major:
        return True
    if not rec_major:
        # 数据库中无专业信息时退化为按院校
        return True
    return plan_major.strip() == rec_major.strip()


def detect_crowd_risk(
    plan: Iterable[PlanEntry],
    user_score: int,
    province: str,
    loader: Optional[CrowdDBLoader] = None,
) -> List[RiskFinding]:
    """检测方案的扎堆风险。

    Args:
        plan: 用户志愿方案（dict / dataclass / tuple 的可迭代对象）
        user_score: 用户分数
        province: 招生省份
        loader: 可选注入的 CrowdDBLoader（便于测试）

    Returns:
        RiskFinding 列表，按 frequency 降序排序。
        - 方案为空 / 省份无数据 / 全部不命中：返回空列表
        - frequency=0 的记录会被跳过（不构成扎堆）
    """
    if not plan:
        return []

    if loader is None:
        loader = CrowdDBLoader()

    # 1) 取该分数段内的所有 crowd_db 记录
    recs = loader.find_recommendations(province, user_score)
    if not recs:
        return []

    findings: List[RiskFinding] = []

    # 2) 遍历 plan
    for raw_entry in plan:
        entry = _normalize_entry(raw_entry)
        school = entry["school"]
        major = entry["major"]
        if not school:
            continue

        # 3) 在该分数段 recs 中查找匹配
        for rec in recs:
            if not _school_matches(school, rec["name"]):
                continue
            if not _major_matches(major, rec.get("major", "")):
                continue
            freq = int(rec.get("frequency", 0))
            if freq <= 0:
                continue
            findings.append(
                RiskFinding(
                    school=rec["name"],
                    major=rec.get("major") or major,
                    frequency=freq,
                    risk_level=_risk_level_from_frequency(freq),
                    platforms=list(rec.get("platforms", [])),
                    predicted_increase=int(rec.get("predicted_increase", 0)),
                    alternatives=list(rec.get("alternatives", [])),
                )
            )
            break  # 一条 plan entry 命中一次即可

    # 4) 按风险等级排序（frequency 降序 → 等级高→低）
    findings.sort(key=lambda f: f.frequency, reverse=True)
    return findings


# ---------- 命令行测试入口 ----------

if __name__ == "__main__":
    # 演示用：575分湖南示例
    sample_plan = [
        plan_entry("长沙理工大学", "会计学"),
        plan_entry("湖南文理学院", "汉语言文学"),
        plan_entry("某某野鸡大学", "考古学"),
    ]
    findings = detect_crowd_risk(sample_plan, user_score=575, province="湖南")
    print(f"📊 575分湖南 方案扎堆检测：{len(findings)} 条风险")
    for f in findings:
        print(
            f"  - {f.school} {f.major or ''} "
            f"(频次:{f.frequency}, 风险:{f.risk_level}, "
            f"+{f.predicted_increase}分, 平台:{','.join(f.platforms)})"
        )
        for a in f.alternatives:
            print(f"      └ 替代: {a.get('name')} {a.get('major', '')}")
