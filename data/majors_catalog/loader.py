from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    MajorCatalogStatus,
    NationalMajor,
    SchoolCatalogStatus,
    SchoolMajorOffering,
)


class MajorsCatalogLoader:
    def __init__(self, catalog_root: Path) -> None:
        self._catalog_root = Path(catalog_root)
        self._latest_doc = self._read_json(
            self._catalog_root / "national" / "latest.json"
        )
        self._changes_path = self._catalog_root / "changes" / "2024-2026.md"
        self._majors = [
            self._major_from_payload(item, self._latest_doc)
            for item in self._latest_doc.get("majors", [])
        ]
        self._by_code = {major.code: major for major in self._majors}
        self._by_name = {major.name: major for major in self._majors}

    @classmethod
    def from_catalog_root(cls, catalog_root: Path | str) -> "MajorsCatalogLoader":
        return cls(Path(catalog_root))

    def lookup(self, name_or_code: str) -> NationalMajor | None:
        by_code = self._by_code.get(name_or_code)
        if by_code is not None:
            return by_code
        return self._by_name.get(name_or_code)

    def list_changes(self) -> list[NationalMajor]:
        return [major for major in self._majors if major.status != "active"]

    def list_risky_majors(self) -> list[NationalMajor]:
        return [major for major in self._majors if major.risk_tags]

    def build_status(self) -> MajorCatalogStatus:
        return MajorCatalogStatus(
            year=int(self._latest_doc["year"]),
            version=str(self._latest_doc["version"]),
            major_count=len(self._majors),
            change_count=len(self.list_changes()),
            risky_major_count=len(self.list_risky_majors()),
            coverage_mode=str(self._latest_doc.get("coverage_mode", "unknown")),
            source=str(self._latest_doc["source"]),
            source_url=str(self._latest_doc["source_url"]),
            last_verified_at=str(self._latest_doc["last_verified_at"]),
            version_strategy=self.version_strategy(),
        )

    def list_school_offerings(
        self, year: int, school_code: str
    ) -> list[SchoolMajorOffering]:
        school_doc = self._read_json(
            self._catalog_root / "schools" / str(year) / f"{school_code}.json"
        )
        return [
            self._school_offering_from_payload(item)
            for item in school_doc.get("offerings", [])
        ]

    def build_school_status(self, year: int) -> SchoolCatalogStatus:
        year_dir = self._catalog_root / "schools" / str(year)
        school_codes = sorted(path.stem for path in year_dir.glob("*.json"))
        offering_count = 0
        mapped_offering_count = 0
        unmapped_offering_count = 0
        version = "unknown"
        for school_code in school_codes:
            school_doc = self._read_json(year_dir / f"{school_code}.json")
            version = str(school_doc.get("version", version))
            offerings = self.list_school_offerings(year, school_code)
            offering_count += len(offerings)
            mapped_offering_count += sum(
                1
                for offering in offerings
                if offering.mapping_status in {"exact", "mapped_alias"}
            )
            unmapped_offering_count += len(offerings) - sum(
                1
                for offering in offerings
                if offering.mapping_status in {"exact", "mapped_alias"}
            )
        return SchoolCatalogStatus(
            year=year,
            version=version,
            school_count=len(school_codes),
            offering_count=offering_count,
            mapped_offering_count=mapped_offering_count,
            unmapped_offering_count=unmapped_offering_count,
            school_codes=school_codes,
            version_strategy=self.version_strategy(),
        )

    def verify_school_catalog(self, year: int) -> dict[str, object]:
        year_dir = self._catalog_root / "schools" / str(year)
        if not year_dir.is_dir():
            return {
                "ok": False,
                "missing_required_files": [f"schools/{year}/"],
                "school_count": 0,
                "offering_count": 0,
            }
        status = self.build_school_status(year)
        return {
            "ok": status.unmapped_offering_count == 0,
            "missing_required_files": [],
            "version": status.version,
            "school_count": status.school_count,
            "offering_count": status.offering_count,
            "mapped_offering_count": status.mapped_offering_count,
            "unmapped_offering_count": status.unmapped_offering_count,
            "school_codes": status.school_codes,
            "version_strategy": status.version_strategy,
        }

    def version_strategy(self) -> str:
        return "national/<year>.json + national/latest.json + changes/2024-2026.md + schools/<year>/<school_code>.json(versioned)"

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _major_from_payload(
        payload: dict[str, Any], root_doc: dict[str, Any]
    ) -> NationalMajor:
        latest_year = int(root_doc["year"])
        return NationalMajor(
            code=str(payload["code"]),
            name=str(payload["name"]),
            discipline=str(payload["discipline"]),
            category=str(payload["category"]),
            degree=str(payload["degree"]),
            is_directional=bool(payload["is_directional"]),
            status=str(payload["status"]),
            year_added=int(payload["year_added"]),
            year_removed=int(payload["year_removed"])
            if payload.get("year_removed") is not None
            else None,
            notes=str(payload["notes"]) if payload.get("notes") is not None else None,
            source_url=str(payload.get("source_url") or root_doc["source_url"]),
            last_verified_at=str(
                payload.get("last_verified_at") or root_doc["last_verified_at"]
            ),
            risk_tags=_build_major_risk_tags(payload, latest_year),
        )

    def _school_offering_from_payload(
        self, payload: dict[str, Any]
    ) -> SchoolMajorOffering:
        raw_national_major_code = payload.get("national_major_code")
        effective_national_major_code = (
            raw_national_major_code
            if raw_national_major_code is not None
            else payload.get("major_code")
        )
        national_major = (
            self._by_code.get(str(effective_national_major_code))
            if effective_national_major_code is not None
            else None
        )
        mapping_status = str(
            payload.get("mapping_status")
            or _mapping_status(
                payload,
                national_major,
                has_explicit_mapping=raw_national_major_code is not None,
            )
        )
        risk_tags = _build_offering_risk_tags(payload, national_major, mapping_status)
        return SchoolMajorOffering(
            school_code=str(payload["school_code"]),
            school_name=str(payload["school_name"]),
            major_code=str(payload["major_code"]),
            major_name=str(payload["major_name"]),
            national_major_code=(
                str(raw_national_major_code)
                if raw_national_major_code is not None
                else None
            ),
            admission_year=int(payload["admission_year"]),
            province=str(payload["province"]),
            duration_years=int(payload["duration_years"]),
            tuition_cny=int(payload["tuition_cny"])
            if payload.get("tuition_cny") is not None
            else None,
            study_mode=str(payload["study_mode"]),
            is_new=bool(payload["is_new"]),
            is_discontinued=bool(payload["is_discontinued"]),
            mapping_status=mapping_status,
            risk_tags=risk_tags,
            source=str(payload["source"]),
            last_verified_at=str(payload["last_verified_at"]),
        )


def _build_major_risk_tags(payload: dict[str, Any], latest_year: int) -> list[str]:
    if payload.get("risk_tags") is not None:
        return [str(tag) for tag in payload.get("risk_tags", [])]

    tags: list[str] = []
    status = str(payload.get("status", "active"))
    year_added = int(payload.get("year_added", latest_year))
    year_removed = payload.get("year_removed")
    if status != "active":
        tags.append("non_active")
    if year_added >= latest_year - 1:
        tags.append("new_in_last_2y")
    if year_removed is not None and int(year_removed) >= latest_year - 1:
        tags.append("removed_in_last_2y")
    return tags


def _mapping_status(
    payload: dict[str, Any],
    national_major: NationalMajor | None,
    *,
    has_explicit_mapping: bool,
) -> str:
    if national_major is None:
        return "unmapped"
    same_code = str(payload.get("major_code")) == national_major.code
    same_name = str(payload.get("major_name")) == national_major.name
    if same_code and same_name and not has_explicit_mapping:
        return "implicit_code_match"
    if same_code and same_name:
        return "exact"
    return "mapped_alias"


def _build_offering_risk_tags(
    payload: dict[str, Any],
    national_major: NationalMajor | None,
    mapping_status: str,
) -> list[str]:
    if payload.get("risk_tags") is not None:
        return [str(tag) for tag in payload.get("risk_tags", [])]

    tags: list[str] = []
    if mapping_status == "unmapped":
        tags.append("unmapped_national_major")
    elif national_major is not None:
        tags.extend(national_major.risk_tags)
    if mapping_status == "implicit_code_match":
        tags.append("missing_explicit_mapping")
    if bool(payload.get("is_new")):
        tags.append("school_new_in_last_2y")
    if bool(payload.get("is_discontinued")):
        tags.append("school_discontinued")
    return sorted(set(tags))
