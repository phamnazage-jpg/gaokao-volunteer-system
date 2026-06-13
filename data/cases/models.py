"""案例管理数据模型 (T6.5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

CaseCategory = Literal["success", "typical", "warning"]
CaseReviewStatus = Literal["pending", "approved", "rejected"]


@dataclass(frozen=True)
class CaseRecord:
    id: int
    title: str
    category: CaseCategory
    summary: str | None = None
    content: str | None = None
    review_status: CaseReviewStatus = "pending"
    review_note: str | None = None
    reviewer: str | None = None
    reviewed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    tags: list[str] = field(default_factory=list)
