from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import MajorCatalogStatus, NationalMajor


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
