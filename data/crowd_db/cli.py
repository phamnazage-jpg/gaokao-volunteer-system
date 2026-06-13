"""gaokao-data-trace CLI implementation (T3.4)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Iterable, Optional

from .loader import CrowdDBLoader
from .risk_report import SOURCE_TYPE_DISPLAY_META


DEFAULT_DATA_YEAR_LABEL = "未知年份"


def _error(message: str, code: int = 1) -> int:
    print(message, file=sys.stderr)
    return code


def _normalize_source_type(raw_source_type: str) -> dict[str, str]:
    meta = SOURCE_TYPE_DISPLAY_META.get(
        raw_source_type,
        SOURCE_TYPE_DISPLAY_META["derived"],
    )
    return {
        "source_type": meta["category"],
        "source_type_label": meta["label"],
        "source_type_icon": meta["icon"],
    }


def _build_match(
    *,
    province: str,
    provenance: dict[str, Any],
    score_range: dict[str, Any],
    recommendation: dict[str, Any],
) -> dict[str, Any]:
    score_bounds = score_range.get("range") or [None, None]
    normalized = _normalize_source_type(str(provenance.get("source_type") or "derived"))
    return {
        "province": province,
        "school": recommendation.get("name", ""),
        "major": recommendation.get("major", ""),
        "frequency": recommendation.get("frequency", 0),
        "platforms": list(recommendation.get("platforms", [])),
        "predicted_increase": recommendation.get("predicted_increase", 0),
        "alternatives": list(recommendation.get("alternatives", [])),
        "score_range": list(score_bounds),
        "score_range_note": score_range.get("note", ""),
        "data_year": provenance.get("data_year"),
        "source": provenance.get("source", ""),
        "source_url": provenance.get("source_url", ""),
        "source_type": normalized["source_type"],
        "raw_source_type": provenance.get("source_type") or "derived",
        "source_type_label": normalized["source_type_label"],
        "source_type_icon": normalized["source_type_icon"],
        "confidence": provenance.get("confidence"),
        "last_updated": provenance.get("last_updated", ""),
    }


def find_school_traces(
    school_name: str,
    *,
    loader: Optional[CrowdDBLoader] = None,
    provinces: Optional[Iterable[str]] = None,
) -> list[dict[str, Any]]:
    loader = loader or CrowdDBLoader(warn_low_confidence=False)
    provinces = list(provinces or loader.list_supported_provinces())
    matches: list[dict[str, Any]] = []

    for province in provinces:
        data = loader.load_province(province)
        if not data:
            continue
        provenance = loader.load_metadata(province) or {"province": province}
        for score_range in data.get("score_ranges", []):
            if not isinstance(score_range, dict):
                continue
            for recommendation in score_range.get("recommendations", []):
                if not isinstance(recommendation, dict):
                    continue
                candidate_name = str(recommendation.get("name", ""))
                if (
                    school_name not in candidate_name
                    and candidate_name not in school_name
                ):
                    continue
                matches.append(
                    _build_match(
                        province=province,
                        provenance=provenance,
                        score_range=score_range,
                        recommendation=recommendation,
                    )
                )

    return matches


def _score_range_label(match: dict[str, Any]) -> str:
    score_range = match.get("score_range") or []
    if len(score_range) != 2:
        return "未知分数段"
    note = match.get("score_range_note") or ""
    label = f"{score_range[0]}-{score_range[1]}"
    if note:
        return f"{label}（{note}）"
    return label


def _year_label(match: dict[str, Any]) -> str:
    data_year = match.get("data_year")
    if data_year in (None, ""):
        return DEFAULT_DATA_YEAR_LABEL
    return f"{data_year}年数据"


def _emit_human(payload: dict[str, Any]) -> None:
    print(f"query: {payload['query']}")
    print(f"match_count: {payload['match_count']}")
    for index, match in enumerate(payload["matches"], start=1):
        print("")
        print(
            f"[{index}] {match['province']} / {_year_label(match)} / {match['school']} / {match['major']}"
        )
        print(f"score_range: {_score_range_label(match)}")
        print(f"frequency: {match['frequency']}")
        print(f"predicted_increase: {match['predicted_increase']}")
        print(f"platforms: {', '.join(match['platforms'])}")
        print(
            "source_type: "
            f"{match['source_type']} ({match['source_type_icon']}{match['source_type_label']})"
        )
        print(f"source: {match['source']}")
        print(f"source_url: {match['source_url']}")
        print(f"confidence: {match['confidence']}")
        print(f"last_updated: {match['last_updated']}")


def _emit(payload: dict[str, Any], *, human: bool) -> None:
    if human:
        _emit_human(payload)
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gaokao-data-trace",
        description="高考志愿数据溯源查询 CLI (T3.4)",
    )
    parser.add_argument("school_name", help="院校名称，支持包含匹配")
    parser.add_argument(
        "--human",
        action="store_true",
        help="输出终端友好的文本格式（默认输出 JSON）",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    matches = find_school_traces(args.school_name)
    if not matches:
        return _error(f"未找到院校“{args.school_name}”的溯源数据", code=1)

    payload = {
        "query": args.school_name,
        "match_count": len(matches),
        "matches": matches,
    }
    _emit(payload, human=args.human)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
