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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MajorCatalogStatus:
    year: int
    version: str
    major_count: int
    coverage_mode: str
    source: str
    source_url: str
    last_verified_at: str
