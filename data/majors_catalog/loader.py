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

    def build_status(self) -> MajorCatalogStatus:
        return MajorCatalogStatus(
            year=int(self._latest_doc["year"]),
            version=str(self._latest_doc["version"]),
            major_count=len(self._majors),
            coverage_mode=str(self._latest_doc.get("coverage_mode", "unknown")),
            source=str(self._latest_doc["source"]),
            source_url=str(self._latest_doc["source_url"]),
            last_verified_at=str(self._latest_doc["last_verified_at"]),
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
        for school_code in school_codes:
            offering_count += len(self.list_school_offerings(year, school_code))
        return SchoolCatalogStatus(
            year=year,
            school_count=len(school_codes),
            offering_count=offering_count,
            school_codes=school_codes,
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
            "ok": True,
            "missing_required_files": [],
            "school_count": status.school_count,
            "offering_count": status.offering_count,
            "school_codes": status.school_codes,
        }

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _major_from_payload(
        payload: dict[str, Any], root_doc: dict[str, Any]
    ) -> NationalMajor:
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
        )

    @staticmethod
    def _school_offering_from_payload(payload: dict[str, Any]) -> SchoolMajorOffering:
        return SchoolMajorOffering(
            school_code=str(payload["school_code"]),
            school_name=str(payload["school_name"]),
            major_code=str(payload["major_code"]),
            major_name=str(payload["major_name"]),
            admission_year=int(payload["admission_year"]),
            province=str(payload["province"]),
            duration_years=int(payload["duration_years"]),
            tuition_cny=int(payload["tuition_cny"])
            if payload.get("tuition_cny") is not None
            else None,
            study_mode=str(payload["study_mode"]),
            is_new=bool(payload["is_new"]),
            is_discontinued=bool(payload["is_discontinued"]),
            source=str(payload["source"]),
            last_verified_at=str(payload["last_verified_at"]),
        )
