"""JSON API surface used by the React Sprint 3 frontend.

These routes intentionally do not replace the existing HTML public portal
routes. They provide typed JSON contracts so the React hooks can be generated
from FastAPI OpenAPI instead of drifting as hand-written client code.
"""

from __future__ import annotations

import base64
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from data.majors_catalog.loader import MajorsCatalogLoader
from data.share.short_link import ShortLinkService


router = APIRouter(prefix="/api", tags=["react-sprint3"])

ScoreType = Literal["physics", "history"]
ReviewStatus = Literal[
    "pending",
    "in_progress",
    "approved",
    "rejected",
    "changes_requested",
]
ReviewAction = Literal["approve", "reject", "request_changes"]
ProviderId = Literal["claude", "gpt", "gemini", "deepseek"]
PosterTemplate = Literal["classic", "modern", "minimal"]


class ScoreLineItem(BaseModel):
    batch: str
    score: float
    rank: int


class ScoreLineResponse(BaseModel):
    province: str
    year: int
    scoreType: ScoreType
    lines: list[ScoreLineItem]


class RankEstimatorResponse(BaseModel):
    province: str
    year: int
    scoreType: ScoreType
    rank: int
    equivalentScore: float


class MajorItem(BaseModel):
    id: str
    name: str
    category: str


class MajorsResponse(BaseModel):
    majors: list[MajorItem]
    total: int


class SchoolItem(BaseModel):
    id: str
    name: str
    province: str
    is985: bool
    is211: bool


class SchoolsResponse(BaseModel):
    schools: list[SchoolItem]
    total: int


class ReviewStartInput(BaseModel):
    planId: str = Field(min_length=1)
    reviewerId: str | None = None


class ReviewStatusResponse(BaseModel):
    id: str
    planId: str
    status: ReviewStatus
    reviewerId: str | None = None
    comment: str | None = None
    updatedAt: str


class ReviewActionInput(BaseModel):
    action: ReviewAction
    reviewId: str = Field(min_length=1)
    comment: str | None = None


class PosterGenerateInput(BaseModel):
    planId: str = Field(min_length=1)
    template: PosterTemplate = "classic"


class PosterGenerateResponse(BaseModel):
    jobId: str
    status: Literal["queued", "processing", "completed", "failed"] = "completed"
    progress: int = Field(default=100, ge=0, le=100)
    posterUrl: str | None = None
    qrCode: str | None = None
    expiresAt: str | None = None


class PosterStatusResponse(BaseModel):
    jobId: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: int = Field(ge=0, le=100)
    posterUrl: str | None = None
    qrCode: str | None = None
    expiresAt: str | None = None
    updatedAt: str


class LLMConfigResponse(BaseModel):
    currentProvider: ProviderId
    fallbackOrder: list[ProviderId]
    availableProviders: list[ProviderId]


class AuditEnhanceInput(BaseModel):
    planId: str
    enhancementType: Literal["detail", "risk", "suggestion"] = "detail"
    baseAudit: dict | None = None


class Recommendation(BaseModel):
    title: str
    detail: str
    priority: Literal["low", "medium", "high"]


class AuditEnhancementResponse(BaseModel):
    summary: str
    recommendations: list[Recommendation]
    provider: ProviderId


class LLMEnhanceStatusResponse(BaseModel):
    planId: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: int = Field(ge=0, le=100)
    currentStep: str
    updatedAt: str


class ShareLinkStatsResponse(BaseModel):
    views: int
    uniqueVisitors: int
    lastAccessedAt: str | None = None


_CATALOG_ROOT = Path(__file__).resolve().parents[2] / "data" / "majors_catalog"
_FALLBACK_PROVINCE = "湖南"
_SCHOOLS = [
    SchoolItem(id="10001", name="北京大学", province="北京", is985=True, is211=True),
    SchoolItem(id="10532", name="湖南大学", province="湖南", is985=True, is211=True),
    SchoolItem(id="10533", name="中南大学", province="湖南", is985=True, is211=True),
    SchoolItem(id="10536", name="长沙理工大学", province="湖南", is985=False, is211=False),
]
_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _review_store(request: Request) -> dict[str, ReviewStatusResponse]:
    store = getattr(request.app.state, "react_sprint3_reviews", None)
    if not isinstance(store, dict):
        store = {}
        request.app.state.react_sprint3_reviews = store
    return store


def _poster_store(request: Request) -> dict[str, PosterStatusResponse]:
    store = getattr(request.app.state, "react_sprint4_posters", None)
    if not isinstance(store, dict):
        store = {}
        request.app.state.react_sprint4_posters = store
    return store


def _catalog_loader() -> MajorsCatalogLoader:
    return MajorsCatalogLoader.from_catalog_root(_CATALOG_ROOT)


@router.get("/data-query/score-line", response_model=ScoreLineResponse)
def get_score_line(
    province: str,
    year: int,
    scoreType: ScoreType,
) -> ScoreLineResponse:
    base_score = 422 if scoreType == "physics" else 438
    return ScoreLineResponse(
        province=province or _FALLBACK_PROVINCE,
        year=year,
        scoreType=scoreType,
        lines=[
            ScoreLineItem(batch="本科批", score=base_score, rank=102000),
            ScoreLineItem(batch="特殊类型招生控制线", score=base_score + 55, rank=42000),
        ],
    )


@router.get("/data-query/rank-estimator", response_model=RankEstimatorResponse)
def get_rank_estimator(
    province: str,
    year: int,
    scoreType: ScoreType,
    rank: int,
) -> RankEstimatorResponse:
    if rank < 0:
        raise HTTPException(status_code=422, detail="rank must be non-negative")
    equivalent = max(150, 680 - rank / 350)
    if scoreType == "history":
        equivalent -= 12
    return RankEstimatorResponse(
        province=province or _FALLBACK_PROVINCE,
        year=year,
        scoreType=scoreType,
        rank=rank,
        equivalentScore=round(equivalent, 1),
    )


@router.get("/data-query/majors", response_model=MajorsResponse)
def list_majors(keyword: str | None = None) -> MajorsResponse:
    needle = (keyword or "").strip()
    majors = []
    for major in _catalog_loader()._majors:  # existing loader has no public list method
        if needle and needle not in major.name and needle not in major.code:
            continue
        majors.append(MajorItem(id=major.code, name=major.name, category=major.category))
        if len(majors) >= 20:
            break
    return MajorsResponse(majors=majors, total=len(majors))


@router.get("/data-query/schools", response_model=SchoolsResponse)
def list_schools(keyword: str | None = None) -> SchoolsResponse:
    needle = (keyword or "").strip()
    schools = [
        school
        for school in _SCHOOLS
        if not needle or needle in school.name or needle in school.province or needle in school.id
    ]
    return SchoolsResponse(schools=schools, total=len(schools))


@router.post("/review/start", response_model=ReviewStatusResponse)
def start_review(payload: ReviewStartInput, request: Request) -> ReviewStatusResponse:
    review = ReviewStatusResponse(
        id=f"rvw_{secrets.token_hex(4)}",
        planId=payload.planId,
        status="in_progress",
        reviewerId=payload.reviewerId,
        comment=None,
        updatedAt=_now_iso(),
    )
    _review_store(request)[review.id] = review
    return review


@router.get("/review/{review_id}/status", response_model=ReviewStatusResponse)
def get_review_status(review_id: str, request: Request) -> ReviewStatusResponse:
    review = _review_store(request).get(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="review not found")
    return review


@router.post("/review/action", response_model=ReviewStatusResponse)
def apply_review_action(payload: ReviewActionInput, request: Request) -> ReviewStatusResponse:
    review = _review_store(request).get(payload.reviewId)
    if review is None:
        raise HTTPException(status_code=404, detail="review not found")
    next_status: ReviewStatus = cast(
        ReviewStatus,
        {
            "approve": "approved",
            "reject": "rejected",
            "request_changes": "changes_requested",
        }[payload.action],
    )
    updated = review.model_copy(
        update={
            "status": next_status,
            "comment": payload.comment,
            "updatedAt": _now_iso(),
        }
    )
    _review_store(request)[updated.id] = updated
    return updated


@router.post("/poster/generate", response_model=PosterGenerateResponse)
def generate_poster(payload: PosterGenerateInput, request: Request) -> PosterGenerateResponse:
    poster_dir = Path(__file__).resolve().parent.parent / "static" / "posters"
    poster_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{payload.planId}-{payload.template}-{secrets.token_hex(3)}.png"
    (poster_dir / filename).write_bytes(_ONE_PIXEL_PNG)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    base = str(request.base_url).rstrip("/")
    url = f"{base}/static/posters/{filename}"
    job_id = f"poster_{secrets.token_hex(4)}"
    status_payload = PosterStatusResponse(
        jobId=job_id,
        status="completed",
        progress=100,
        posterUrl=url,
        qrCode=url,
        expiresAt=expires_at.isoformat(),
        updatedAt=_now_iso(),
    )
    _poster_store(request)[job_id] = status_payload
    return PosterGenerateResponse(
        jobId=job_id,
        status=status_payload.status,
        progress=status_payload.progress,
        posterUrl=url,
        qrCode=url,
        expiresAt=expires_at.isoformat(),
    )


@router.get("/poster/{job_id}/status", response_model=PosterStatusResponse)
def get_poster_status(job_id: str, request: Request) -> PosterStatusResponse:
    poster = _poster_store(request).get(job_id)
    if poster is None:
        raise HTTPException(status_code=404, detail="poster job not found")
    return poster


@router.get("/llm/config", response_model=LLMConfigResponse)
def get_llm_config() -> LLMConfigResponse:
    order: list[ProviderId] = ["claude", "gpt", "gemini", "deepseek"]
    return LLMConfigResponse(
        currentProvider="claude",
        fallbackOrder=order,
        availableProviders=order,
    )


@router.post("/llm/{provider}/enhance", response_model=AuditEnhancementResponse)
def enhance_audit(provider: ProviderId, payload: AuditEnhanceInput) -> AuditEnhancementResponse:
    return AuditEnhancementResponse(
        summary=f"{provider} enhancement for {payload.planId}",
        provider=provider,
        recommendations=[
            Recommendation(
                title="Review plan assumptions",
                detail="Verify province, score type, rank, and batch before final submission.",
                priority="medium",
            )
        ],
    )


@router.get("/llm/enhance/{plan_id}/status", response_model=LLMEnhanceStatusResponse)
def get_llm_enhance_status(plan_id: str) -> LLMEnhanceStatusResponse:
    return LLMEnhanceStatusResponse(
        planId=plan_id,
        status="completed",
        progress=100,
        currentStep="增强建议已生成",
        updatedAt=_now_iso(),
    )


@router.get("/share-link/{code}/stats", response_model=ShareLinkStatsResponse)
def get_share_link_stats(code: str, request: Request) -> ShareLinkStatsResponse:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        raise HTTPException(status_code=500, detail="settings unavailable")
    stats = ShortLinkService(db_path=settings.share_db_path).get_stats(code)
    if stats is None:
        raise HTTPException(status_code=404, detail="share link not found")
    return ShareLinkStatsResponse(
        views=int(stats.get("access_count") or 0),
        uniqueVisitors=int(stats.get("unique_visitors") or 0),
        lastAccessedAt=stats.get("last_access_at_iso"),
    )
