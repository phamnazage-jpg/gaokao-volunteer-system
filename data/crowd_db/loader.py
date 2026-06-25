"""
大厂AI推荐数据库加载器

用于反扎堆检测功能，加载和查询大厂AI的高频推荐院校。
"""

from __future__ import annotations

import json
import os
import re
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


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
        """根据频次计算风险等级（与 crowd_detector._risk_level_from_frequency 一致）

        frequency == 0: 'none'（不构成扎堆风险）
        frequency 1:    'low'
        frequency 2-3:  'medium'
        frequency >= 4: 'high'
        """
        if self.frequency >= 4:
            return "high"
        if self.frequency >= 2:
            return "medium"
        if self.frequency >= 1:
            return "low"
        return "none"


@dataclass
class ProvenanceValidation:
    """T3.2 溯源字段验证结果。

    Attributes:
        ok: 是否通过 schema 校验（errors 为空且非加载失败）
        errors: schema 硬错误（缺字段、字段类型/取值非法、文件损坏等）
        warnings: 软警告（如低 confidence、source_url 为空）
        is_usable: confidence 是否达到 USABLE_CONFIDENCE_THRESHOLD
        summary: 关键溯源字段的扁平摘要（province/source_type/data_year/...）
    """

    province: str
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    is_usable: bool = False
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "province": self.province,
            "ok": self.ok,
            "is_usable": self.is_usable,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "summary": dict(self.summary),
        }


class CrowdDBLoader:
    """
    大厂AI推荐数据库加载器

    数据存储在 data/crowd_db/{province}.json 文件中。
    """

    DATA_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "crowd_db",
    )

    PROVINCE_FILE_MAP = {
        "北京": "beijing",
        "天津": "tianjin",
        "上海": "shanghai",
        "重庆": "chongqing",
        "河北": "hebei",
        "山西": "shanxi",
        "辽宁": "liaoning",
        "吉林": "jilin",
        "黑龙江": "heilongjiang",
        "江苏": "jiangsu",
        "浙江": "zhejiang",
        "安徽": "anhui",
        "福建": "fujian",
        "江西": "jiangxi",
        "山东": "shandong",
        "河南": "henan",
        "湖北": "hubei",
        "湖南": "hunan",
        "广东": "guangdong",
        "海南": "hainan",
        "四川": "sichuan",
        "贵州": "guizhou",
        "云南": "yunnan",
        "陕西": "shaanxi",
        "甘肃": "gansu",
        "青海": "qinghai",
        "新疆": "xinjiang",
        # Stage 4 (2026-06-25): 4 个自治区加入，全国 31 省口径
        "内蒙古": "neimenggu",
        "广西": "guangxi",
        "西藏": "xizang",
        "宁夏": "ningxia",
    }

    # T3.2 溯源查询/验证常量（与 SCHEMA.md 1/3 节保持一致）
    USABLE_CONFIDENCE_THRESHOLD: float = 0.5
    VALID_SOURCE_TYPES: Tuple[str, ...] = (
        "manual_summary",
        "official_release",
        "platform_scrape",
        "derived",
    )
    ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def __init__(
        self, data_dir: Optional[str] = None, warn_low_confidence: bool = True
    ):
        """初始化加载器。

        Args:
            data_dir: 数据目录路径，默认使用 DATA_DIR
            warn_low_confidence: 低置信度数据是否发出 UserWarning
        """
        self.data_dir = data_dir or self.DATA_DIR
        self.warn_low_confidence = warn_low_confidence
        self._cache: Dict[str, dict] = {}

    def _file_candidates(self, province: str) -> List[str]:
        slug = self.PROVINCE_FILE_MAP.get(province)
        candidates: List[str] = []
        if slug:
            candidates.append(f"{slug}.json")
        candidates.append(f"{province}.json")
        return candidates

    def _load_json_file(self, file_path: str) -> Optional[dict]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def load_province(self, province: str) -> Optional[dict]:
        """加载指定省份的推荐数据。"""
        if province in self._cache:
            return self._cache[province]

        for filename in self._file_candidates(province):
            file_path = os.path.join(self.data_dir, filename)
            if not os.path.exists(file_path):
                continue
            data = self._load_json_file(file_path)
            if not data:
                continue
            self._cache[province] = data
            confidence = data.get("confidence")
            if (
                self.warn_low_confidence
                and isinstance(confidence, (int, float))
                and confidence < 0.5
            ):
                warnings.warn(
                    f"{province} 数据置信度较低 ({confidence})，当前仅为骨架数据",
                    UserWarning,
                    stacklevel=2,
                )
            return data

        return None

    def load_metadata(self, province: str) -> Optional[dict]:
        """仅加载省份溯源元数据。"""
        data = self.load_province(province)
        if not data:
            return None

        trusted_sources = data.get("trusted_sources")
        if not isinstance(trusted_sources, list):
            trusted_sources = []

        return {
            "province": data.get("province", province),
            "last_updated": data.get("last_updated", ""),
            "data_year": data.get("data_year"),
            "source": data.get("source", ""),
            "source_url": data.get("source_url", ""),
            "source_type": data.get("source_type", ""),
            "confidence": data.get("confidence"),
            "quality_note": data.get("quality_note", ""),
            "trusted_sources": trusted_sources,
            "trusted_sources_count": len(trusted_sources),
            "record_count": sum(
                len(score_range.get("recommendations", []))
                for score_range in data.get("score_ranges", [])
                if isinstance(score_range, dict)
            ),
        }

    def list_supported_provinces(self) -> List[str]:
        """返回 loader 支持的省份列表。"""
        return list(self.PROVINCE_FILE_MAP.keys())

    def list_provinces(self) -> List[Dict[str, Any]]:
        """返回所有支持省份的存在性与元数据概览。"""
        provinces: List[Dict[str, Any]] = []
        for province in self.list_supported_provinces():
            file_path = self._resolve_file_path(province)
            data = (
                self._load_json_file(file_path)
                if file_path and os.path.exists(file_path)
                else None
            )
            provinces.append({
                "province": province,
                "file_name": os.path.basename(file_path) if file_path else None,
                "exists": data is not None,
                "last_updated": data.get("last_updated") if data else None,
                "data_year": data.get("data_year") if data else None,
                "source_type": data.get("source_type") if data else None,
                "confidence": data.get("confidence") if data else None,
                "record_count": sum(
                    len(score_range.get("recommendations", []))
                    for score_range in data.get("score_ranges", [])
                    if isinstance(score_range, dict)
                )
                if data
                else 0,
            })
        return provinces

    def _resolve_file_path(self, province: str) -> Optional[str]:
        for filename in self._file_candidates(province):
            file_path = os.path.join(self.data_dir, filename)
            if os.path.exists(file_path):
                return file_path
        return None

    def find_recommendations(self, province: str, score: int) -> List[Dict[str, Any]]:
        """查询指定分数段内的所有推荐。"""
        data = self.load_province(province)
        if not data:
            return []

        results: List[Dict[str, Any]] = []
        for score_range in data.get("score_ranges", []):
            if not isinstance(score_range, dict):
                continue
            score_bounds = score_range.get("range") or []
            if len(score_bounds) != 2:
                continue
            min_score, max_score = score_bounds
            if min_score <= score <= max_score:
                results.extend(score_range.get("recommendations", []))

        return results

    def find_recommendation_by_school(
        self, province: str, school_name: str
    ) -> Optional[Dict[str, Any]]:
        """按院校名查询推荐信息（支持模糊匹配）。"""
        data = self.load_province(province)
        if not data:
            return None

        for score_range in data.get("score_ranges", []):
            if not isinstance(score_range, dict):
                continue
            for rec in score_range.get("recommendations", []):
                if (
                    school_name in rec.get("name", "")
                    or rec.get("name", "") in school_name
                ):
                    return rec

        return None

    # ------------------------------------------------------------------ #
    # T3.2 溯源字段查询 + 验证
    # ------------------------------------------------------------------ #

    REQUIRED_PROVENANCE_FIELDS: Tuple[str, ...] = (
        "province",
        "last_updated",
        "data_year",
        "source",
        "source_type",
        "confidence",
        "score_ranges",
    )

    @classmethod
    def validate_provenance(
        cls, data: Optional[dict], province: Optional[str] = None
    ) -> ProvenanceValidation:
        """T3.2: 校验单省 JSON 顶层溯源字段是否符合 SCHEMA.md。

        Args:
            data: 已加载的省份 dict；为 None 表示加载失败
            province: 省份名（用于报告，省略时尝试从 data 取）

        Returns:
            ProvenanceValidation 实例，ok 表示 schema 硬错误列表为空
        """
        prov_name = province or (data.get("province") if data else "") or ""
        validation = ProvenanceValidation(province=prov_name, ok=False)

        if data is None:
            validation.errors.append("load_failed: 省份数据加载失败或文件不存在")
            return validation

        # 必填字段
        for key in cls.REQUIRED_PROVENANCE_FIELDS:
            if key not in data:
                validation.errors.append(f"missing_field: {key}")

        # province 字符串类型
        p = data.get("province")
        if "province" in data and not isinstance(p, str):
            validation.errors.append(
                f"type_error: province 应为 str, got {type(p).__name__}"
            )

        # last_updated ISO 日期（缺失已在 REQUIRED 检查报告）
        lu = data.get("last_updated")
        if "last_updated" in data and lu is not None:
            if not isinstance(lu, str) or not cls.ISO_DATE_PATTERN.match(lu):
                validation.errors.append(
                    f"format_error: last_updated 应为 YYYY-MM-DD, got {lu!r}"
                )
            elif lu == "":
                validation.warnings.append("empty_last_updated: last_updated 为空")

        # data_year 必须为 int（缺失已在 REQUIRED 检查报告）
        dy = data.get("data_year")
        if "data_year" in data and dy is not None and not isinstance(dy, int):
            validation.errors.append(
                f"type_error: data_year 应为 int, got {type(dy).__name__}"
            )

        # source 非空字符串
        src = data.get("source")
        if "source" in data and (src is None or src == ""):
            validation.warnings.append("empty_source: source 字段为空")

        # source_url 可空但须为字符串
        su = data.get("source_url")
        if "source_url" in data and su is not None and not isinstance(su, str):
            validation.errors.append(
                f"type_error: source_url 应为 str 或缺失, got {type(su).__name__}"
            )

        # source_type 必须是枚举之一（缺失已在 REQUIRED 检查报告）
        st = data.get("source_type")
        if (
            "source_type" in data
            and st is not None
            and st not in cls.VALID_SOURCE_TYPES
        ):
            validation.errors.append(
                f"enum_error: source_type {st!r} 不在 {list(cls.VALID_SOURCE_TYPES)} 内"
            )

        # confidence 数值 + 区间（缺失已在 REQUIRED 检查报告）
        c = data.get("confidence")
        if "confidence" in data and c is not None:
            if not isinstance(c, (int, float)) or not (0.0 <= c <= 1.0):
                validation.errors.append(
                    f"range_error: confidence 应在 [0,1], got {c!r}"
                )
            else:
                if c < cls.USABLE_CONFIDENCE_THRESHOLD:
                    validation.warnings.append(
                        f"low_confidence: confidence={c} < {cls.USABLE_CONFIDENCE_THRESHOLD}"
                    )
                validation.is_usable = c >= cls.USABLE_CONFIDENCE_THRESHOLD

        # score_ranges 必须是 list（缺失已在 REQUIRED 检查报告）
        sr = data.get("score_ranges")
        if "score_ranges" in data and sr is not None and not isinstance(sr, list):
            validation.errors.append(
                f"type_error: score_ranges 应为 list, got {type(sr).__name__}"
            )

        # source_url 空时记 warning（不影响 ok，但与人工复核流程相关）
        if isinstance(su, str) and su == "":
            validation.warnings.append("empty_source_url: source_url 为空")
        elif isinstance(su, str) and (
            "github.com" in su
            or "gaokao-volunteer-system/blob" in su
            or "localhost" in su
        ):
            validation.warnings.append(
                "self_reference_source_url: source_url 指向仓库/本地路径，不应作为可信来源证明"
            )

        # trusted_sources 可选，但若存在应为 list
        trusted_sources = data.get("trusted_sources")
        if trusted_sources is not None and not isinstance(trusted_sources, list):
            validation.errors.append(
                f"type_error: trusted_sources 应为 list, got {type(trusted_sources).__name__}"
            )

        # 摘要（仅在已加载且含核心字段时）
        if all(
            k in data for k in ("province", "source_type", "data_year", "confidence")
        ):
            validation.summary = {
                "province": data.get("province"),
                "source": data.get("source", ""),
                "source_url": data.get("source_url", ""),
                "source_type": data.get("source_type"),
                "data_year": data.get("data_year"),
                "last_updated": data.get("last_updated", ""),
                "confidence": data.get("confidence"),
            }

        validation.ok = not validation.errors
        return validation

    def validate_province(self, province: str) -> ProvenanceValidation:
        """T3.2: 加载并校验指定省份的溯源字段。

        不修改 self._cache 之外的状态；与 warn_low_confidence 兼容。
        """
        data = self.load_province(province)
        return self.validate_provenance(data, province=province)

    def validate_all(self) -> Dict[str, ProvenanceValidation]:
        """T3.2: 校验所有支持省份的溯源字段。

        Returns:
            {省份名: ProvenanceValidation}
        """
        results: Dict[str, ProvenanceValidation] = {}
        for province in self.list_supported_provinces():
            results[province] = self.validate_province(province)
        return results

    def filter_provinces(
        self,
        *,
        source_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        data_year: Optional[int] = None,
        updated_since: Optional[str] = None,
        updated_before: Optional[str] = None,
        only_usable: Optional[bool] = None,
    ) -> List[str]:
        """T3.2: 按溯源字段过滤支持省份。

        Args:
            source_type: 仅匹配指定 source_type（如 "manual_summary"）
            min_confidence: 最低 confidence（含）
            max_confidence: 最高 confidence（含）
            data_year: 仅匹配指定 data_year
            updated_since: YYYY-MM-DD 起始日期（含）
            updated_before: YYYY-MM-DD 截止日期（含）
            only_usable: True 仅返回 confidence >= 阈值的省份

        Returns:
            匹配条件的省份名列表（按 PROVINCE_FILE_MAP 顺序）

        Note:
            仅依据已加载的顶层溯源字段过滤；底层推荐条目不在过滤范围内。
        """
        results: List[str] = []
        for province in self.list_supported_provinces():
            data = self.load_province(province)
            if data is None:
                continue
            if source_type is not None and data.get("source_type") != source_type:
                continue
            c = data.get("confidence")
            if min_confidence is not None:
                if not isinstance(c, (int, float)) or c < min_confidence:
                    continue
            if max_confidence is not None:
                if not isinstance(c, (int, float)) or c > max_confidence:
                    continue
            if data_year is not None and data.get("data_year") != data_year:
                continue
            lu = data.get("last_updated")
            if updated_since is not None:
                if not isinstance(lu, str) or lu < updated_since:
                    continue
            if updated_before is not None:
                if not isinstance(lu, str) or lu > updated_before:
                    continue
            if only_usable is True:
                if not (
                    isinstance(c, (int, float))
                    and c >= self.USABLE_CONFIDENCE_THRESHOLD
                ):
                    continue
            results.append(province)
        return results

    def get_provenance_report(
        self,
        *,
        only_usable: bool = False,
        source_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """T3.2: 汇总各省份溯源字段 + 验证结果。

        Args:
            only_usable: True 时仅包含 confidence >= 阈值的省份
            source_type: 同时按 source_type 过滤

        Returns:
            报告 dict：包含 total/usable_count/failed_count/by_source_type/items
        """
        provinces = self.filter_provinces(
            source_type=source_type, only_usable=only_usable or None
        )
        items: List[Dict[str, Any]] = []
        for province in provinces:
            validation = self.validate_province(province)
            item = validation.to_dict()
            file_path = self._resolve_file_path(province)
            item["file_name"] = os.path.basename(file_path) if file_path else None
            items.append(item)

        by_source_type: Dict[str, int] = {}
        for item in items:
            st = (item.get("summary") or {}).get("source_type") or "unknown"
            by_source_type[st] = by_source_type.get(st, 0) + 1

        return {
            "total": len(items),
            "usable_count": sum(1 for i in items if i["is_usable"]),
            "failed_count": sum(1 for i in items if not i["ok"]),
            "by_source_type": by_source_type,
            "items": items,
        }


if __name__ == "__main__":
    loader = CrowdDBLoader()
    data = loader.load_province("湖南")
    if data:
        print(f"✅ 加载湖南数据: {len(data.get('score_ranges', []))} 个分数段")
    else:
        print("❌ 加载湖南数据失败")

    recs = loader.find_recommendations("湖南", score=575)
    print(f"📊 575分在湖南的扎堆院校: {len(recs)} 个")
    for rec in recs:
        print(
            f"  - {rec['name']} {rec['major']} (频次:{rec['frequency']}, +{rec['predicted_increase']}分)"
        )
