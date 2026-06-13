"""扎堆报告生成器 (T2.4)

核心入口：build_crowd_risks(plan, user_score, province, loader=None) -> list[dict]

将 crowd_detector.detect_crowd_risk 返回的 RiskFinding 列表
转换为 templates/audit_report.html 模板所需的 crowd_risks 字典格式，
每条带 🔴/🟡/🟢 三色 emoji 标识（high/medium/low）。

模板期望字段（来自 templates/audit_report.html 第 191-202 行）：
    {
        "school": str,
        "major": str,
        "frequency": int,
        "predicted_increase": int,
        "risk_level": "high" | "medium" | "low",
        "risk_level_label": str,        # 中文标签 "高"/"中"/"低"
        "risk_emoji": str,              # 🔴/🟡/🟢
        "platforms": list[str],
        "alternatives": [
            {"school": str, "score": int|str},
            ...
        ],
    }

辅助能力：
- group_by_risk(findings) — 按风险等级分组返回 dict[level, list[dict]]
- format_risk_summary(crowd_risks) — 给报告顶部用的单行汇总
  （如"🔴1 🟡2 🟢3"）
- render_risk_table(crowd_risks) — 给不支持 Jinja 的命令行场景用的
  简易纯文本表格
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Protocol


SOURCE_TYPE_DISPLAY_META: Dict[str, Dict[str, str]] = {
    "official_release": {"icon": "✓", "label": "来源", "category": "official"},
    "manual_summary": {"icon": "⚠️", "label": "报告", "category": "report"},
    "platform_scrape": {"icon": "⚠️", "label": "报告", "category": "report"},
    "derived": {"icon": "📊", "label": "估算", "category": "estimated"},
}
PUBLIC_SOURCE_TYPE_DISPLAY_META: Dict[str, Dict[str, str]] = {
    "official": {"icon": "✓", "label": "来源", "category": "official"},
    "report": {"icon": "⚠️", "label": "报告", "category": "report"},
    "estimated": {"icon": "📊", "label": "估算", "category": "estimated"},
}


class _LoaderProtocol(Protocol):
    """loader 必须提供的方法（duck-typing，避免对 CrowdDBLoader 强依赖）。"""

    def find_recommendations(
        self, province: str, score: int
    ) -> List[Dict[str, Any]]: ...

    def load_metadata(self, province: str) -> Optional[Dict[str, Any]]: ...


LoaderLike = _LoaderProtocol

from data.crowd_db.crowd_detector import (  # noqa: E402
    PlanEntry,
    RiskFinding,
    detect_crowd_risk,
    plan_entry as _plan_entry,
)


# 风险等级 → emoji / 中文标签 映射
RISK_LEVEL_META: Dict[str, Dict[str, str]] = {
    "high": {"emoji": "🔴", "label": "高", "zh": "高风险"},
    "medium": {"emoji": "🟡", "label": "中", "zh": "中风险"},
    "low": {"emoji": "🟢", "label": "低", "zh": "低风险"},
}


def _alternative_to_template(alt: Dict[str, Any]) -> Dict[str, Any]:
    """把 crowd_db 中的 alternatives 项转为模板需要的 school/score 形态。

    crowd_db 原始：{"name": str, "major": str, "score": int}
    模板需要的字段名：school / score
    """
    school = alt.get("name") or alt.get("school") or ""
    score = alt.get("score", 0)
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0
    return {"school": school, "score": score, "major": alt.get("major", "")}


def _normalize_provenance(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    metadata = metadata or {}
    public_source_type = metadata.get("source_type") or "estimated"
    raw_source_type = (
        metadata.get("raw_source_type") or metadata.get("source_type") or "derived"
    )
    display = SOURCE_TYPE_DISPLAY_META.get(raw_source_type)
    if display is None:
        display = PUBLIC_SOURCE_TYPE_DISPLAY_META.get(
            public_source_type,
            PUBLIC_SOURCE_TYPE_DISPLAY_META["estimated"],
        )
    confidence = metadata.get("confidence")
    try:
        confidence = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None
    data_year = metadata.get("data_year")
    try:
        data_year = int(data_year) if data_year is not None else None
    except (TypeError, ValueError):
        data_year = None
    return {
        "source_type": display["category"],
        "raw_source_type": raw_source_type,
        "source_type_display": display["category"],
        "source_type_label": display["label"],
        "source_type_icon": display["icon"],
        "source": metadata.get("source", ""),
        "source_url": metadata.get("source_url", ""),
        "confidence": confidence,
        "last_updated": metadata.get("last_updated", ""),
        "data_year": data_year,
    }


def _load_provenance_metadata(
    loader: Optional[LoaderLike], province: str
) -> Dict[str, Any]:
    if loader is None:
        from data.crowd_db.loader import CrowdDBLoader

        loader = CrowdDBLoader()  # type: ignore[assignment]
    load_metadata = getattr(loader, "load_metadata", None)
    if callable(load_metadata):
        metadata = load_metadata(province)
        if isinstance(metadata, dict) or metadata is None:
            return _normalize_provenance(metadata)
    return _normalize_provenance(None)


def finding_to_risk_dict(
    finding: RiskFinding, provenance: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """RiskFinding → 模板所需的 crowd_risks 单条字典。

    若 risk_level 不在 RISK_LEVEL_META 中（crowd_detector 不会返回 none，
    因为 frequency=0 已被跳过），fallback 到 low + 🟢。
    """
    meta = RISK_LEVEL_META.get(finding.risk_level, RISK_LEVEL_META["low"])
    risk = {
        "school": finding.school,
        "major": finding.major or "",
        "frequency": int(finding.frequency),
        "predicted_increase": int(finding.predicted_increase),
        "risk_level": finding.risk_level,
        "risk_level_label": meta["label"],
        "risk_emoji": meta["emoji"],
        "platforms": list(finding.platforms),
        "alternatives": [_alternative_to_template(a) for a in finding.alternatives],
    }
    risk.update(_normalize_provenance(provenance))
    return risk


def build_crowd_risks(
    plan: Iterable[PlanEntry],
    user_score: int,
    province: str,
    loader: Optional[LoaderLike] = None,
) -> List[Dict[str, Any]]:
    """构建 crowd_risks 列表（直接喂给 audit_report.html 模板）。

    Args:
        plan: 用户志愿方案（dict / dataclass / tuple 的可迭代对象）
        user_score: 用户分数
        province: 招生省份
        loader: 可选注入的 CrowdDBLoader

    Returns:
        模板所需字典列表（已按 frequency 降序）。
        frequency=0 / 省份无数据 / 方案为空 → 返回空列表。
    """
    findings = detect_crowd_risk(plan, user_score, province, loader=loader)  # type: ignore[arg-type]
    provenance = _load_provenance_metadata(loader, province)
    return [finding_to_risk_dict(f, provenance=provenance) for f in findings]


def group_by_risk(
    crowd_risks: Iterable[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """把 crowd_risks 按风险等级分组。

    返回值总是包含 high/medium/low 三个 key（缺位为空列表），
    方便模板 / CLI 直接读取而不必判 None。
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {"high": [], "medium": [], "low": []}
    for r in crowd_risks:
        level = r.get("risk_level", "low")
        if level not in grouped:
            grouped[level] = []
        grouped[level].append(r)
    return grouped


def format_risk_summary(crowd_risks: Iterable[Dict[str, Any]]) -> str:
    """生成报告顶部用的单行风险汇总。

    例：空 → "无扎堆风险"
        1 高 2 中 3 低 → "🔴 1 个高风险、🟡 2 个中风险、🟢 3 个低风险"
    """
    grouped = group_by_risk(crowd_risks)
    counts = {level: len(grouped.get(level, [])) for level in ("high", "medium", "low")}
    if sum(counts.values()) == 0:
        return "无扎堆风险"
    parts = []
    for level in ("high", "medium", "low"):
        n = counts[level]
        if n > 0:
            meta = RISK_LEVEL_META[level]
            unit = "个" + meta["zh"]
            parts.append(f"{meta['emoji']} {n} {unit}")
    return "、".join(parts)


def render_risk_table(crowd_risks: Iterable[Dict[str, Any]]) -> str:
    """生成纯文本版扎堆风险表格（CLI / 微信消息场景）。

    列：emoji  院校  专业  频次  预测  等级
    """
    risks = list(crowd_risks)
    if not risks:
        return "（无扎堆风险记录）"
    lines = ["扎堆风险报告：", ""]
    header = (
        f"{'等级':<4}  {'院校':<14}  {'专业':<12}  {'频次':<4}  {'预测上涨':<8}  平台"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for r in risks:
        lines.append(
            f"{r.get('risk_emoji', '🟢'):<4}  "
            f"{r.get('school', ''):<14}  "
            f"{r.get('major', ''):<12}  "
            f"{str(r.get('frequency', 0)) + '/4':<4}  "
            f"+{r.get('predicted_increase', 0)} 分".ljust(8)
            + "  "
            f"{','.join(r.get('platforms', []))}"
        )
        alts = r.get("alternatives") or []
        if alts:
            for a in alts:
                school = a.get("school", "")
                score = a.get("score", "")
                lines.append(f"      └ 替代: {school}（{score} 分）")
    return "\n".join(lines)


# ---------- 命令行测试入口 ----------

if __name__ == "__main__":
    sample_plan = [
        _plan_entry("长沙理工大学", "计算机科学与技术"),
        _plan_entry("湖南科技大学", "机械设计制造及其自动化"),
        _plan_entry("某某野鸡大学", "考古学"),
    ]
    risks = build_crowd_risks(sample_plan, user_score=575, province="湖南")
    print(f"📊 575分湖南 方案扎堆报告：{format_risk_summary(risks)}")
    print()
    print(render_risk_table(risks))
