from __future__ import annotations

from pathlib import Path

from .loader import MajorsCatalogLoader


DEFAULT_CATALOG_ROOT = Path(__file__).resolve().parents[2] / "data" / "majors_catalog"


def build_status_payload(catalog_root: Path) -> dict[str, object]:
    loader = MajorsCatalogLoader.from_catalog_root(catalog_root)
    status = loader.build_status()
    return {
        "ok": True,
        "year": status.year,
        "version": status.version,
        "major_count": status.major_count,
        "change_count": status.change_count,
        "risky_major_count": status.risky_major_count,
        "coverage_mode": status.coverage_mode,
        "source": status.source,
        "source_url": status.source_url,
        "last_verified_at": status.last_verified_at,
        "version_strategy": status.version_strategy,
    }


def build_lookup_payload(catalog_root: Path, name_or_code: str) -> dict[str, object]:
    loader = MajorsCatalogLoader.from_catalog_root(catalog_root)
    major = loader.lookup(name_or_code)
    if major is None:
        return {
            "ok": False,
            "code": "E_MAJORS_NOT_FOUND",
            "message": f"major not found: {name_or_code}",
        }
    return {
        "ok": True,
        "major": major.to_dict(),
    }


def build_verify_payload(catalog_root: Path) -> dict[str, object]:
    missing_required_files: list[str] = []
    national_dir = catalog_root / "national"
    changes_path = catalog_root / "changes" / "2024-2026.md"
    latest = national_dir / "latest.json"
    current_year = national_dir / "2024.json"
    if not national_dir.is_dir():
        missing_required_files.append("national/")
    if not current_year.is_file():
        missing_required_files.append("national/2024.json")
    if not latest.is_file():
        missing_required_files.append("national/latest.json")
    if not changes_path.is_file():
        missing_required_files.append("changes/2024-2026.md")

    if missing_required_files:
        return {
            "ok": False,
            "missing_required_files": missing_required_files,
            "major_count": 0,
        }

    loader = MajorsCatalogLoader.from_catalog_root(catalog_root)
    status = loader.build_status()
    return {
        "ok": True,
        "missing_required_files": [],
        "major_count": status.major_count,
        "change_count": status.change_count,
        "risky_major_count": status.risky_major_count,
        "coverage_mode": status.coverage_mode,
        "version_strategy": status.version_strategy,
    }


def build_changes_payload(catalog_root: Path) -> dict[str, object]:
    loader = MajorsCatalogLoader.from_catalog_root(catalog_root)
    changes = [major.to_dict() for major in loader.list_changes()]
    return {
        "ok": True,
        "changes": changes,
        "change_count": len(changes),
    }


def build_school_status_payload(catalog_root: Path, year: int) -> dict[str, object]:
    loader = MajorsCatalogLoader.from_catalog_root(catalog_root)
    status = loader.build_school_status(year)
    return {
        "ok": True,
        "year": status.year,
        "version": status.version,
        "school_count": status.school_count,
        "offering_count": status.offering_count,
        "mapped_offering_count": status.mapped_offering_count,
        "unmapped_offering_count": status.unmapped_offering_count,
        "school_codes": status.school_codes,
        "version_strategy": status.version_strategy,
    }


def build_school_verify_payload(catalog_root: Path, year: int) -> dict[str, object]:
    loader = MajorsCatalogLoader.from_catalog_root(catalog_root)
    payload = loader.verify_school_catalog(year)
    payload["year"] = year
    return payload
