from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class NationalMajor:
    code: str
    name: str
    discipline: str
    category: str
    degree: str
    is_directional: bool
    status: str
    year_added: int
    year_removed: int | None
    notes: str | None
    source_url: str
    last_verified_at: str
    risk_tags: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SchoolMajorOffering:
    school_code: str
    school_name: str
    major_code: str
    major_name: str
    national_major_code: str | None
    admission_year: int
    province: str
    duration_years: int
    tuition_cny: int | None
    study_mode: str
    is_new: bool
    is_discontinued: bool
    mapping_status: str
    risk_tags: list[str]
    source: str
    last_verified_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MajorCatalogStatus:
    year: int
    version: str
    major_count: int
    change_count: int
    risky_major_count: int
    coverage_mode: str
    source: str
    source_url: str
    last_verified_at: str
    version_strategy: str


@dataclass(frozen=True)
class SchoolCatalogStatus:
    year: int
    version: str
    school_count: int
    offering_count: int
    mapped_offering_count: int
    unmapped_offering_count: int
    school_codes: list[str]
    version_strategy: str
