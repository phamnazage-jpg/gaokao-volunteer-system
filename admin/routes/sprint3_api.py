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
from typing import Literal, Any, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from admin.auth import require_role
from admin.config import Settings, get_settings_dep
from admin.db import AdminUser
from data.majors_catalog.loader import MajorsCatalogLoader
from data.share.short_link import ShortLinkService, build_url


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



class ChatProfile(BaseModel):
    province: str | None = None
    score: int | None = Field(default=None, ge=0, le=750)
    rank: int | None = Field(default=None, ge=1)
    subjects: list[str] | None = None


class ChatSendInput(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    sessionId: str | None = None
    userName: str | None = None
    profile: ChatProfile | None = None


class ChatMessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    data: dict[str, Any] | None = None
    timestamp: str


class ChatSendResponse(BaseModel):
    sessionId: str
    userMessageId: str
    assistantMessageId: str
    assistantMessage: ChatMessageResponse


class ChatStreamResponse(BaseModel):
    content: str
    status: Literal["idle", "thinking", "paused", "stopped"] = "idle"
    done: bool = True


class ChatHistoryResponse(BaseModel):
    sessionId: str
    messages: list[ChatMessageResponse]


class ConsultationItem(BaseModel):
    id: str
    title: str
    messageCount: int
    createdAt: str
    updatedAt: str


class ConsultationListResponse(BaseModel):
    consultations: list[ConsultationItem]
    total: int


class ConsultationDetailResponse(BaseModel):
    id: str
    title: str
    messages: list[ChatMessageResponse]
    createdAt: str
    updatedAt: str


class PlanChoice(BaseModel):
    university: str
    major: str
    estScore: float
    probability: float
    risk: str
    riskType: str
    reason: str


class PlanResponse(BaseModel):
    id: str
    name: str
    rush: list[PlanChoice]
    stable: list[PlanChoice]
    safe: list[PlanChoice]
    createdAt: str


class PlanListResponse(BaseModel):
    plans: list[PlanResponse]
    total: int


class SuccessResponse(BaseModel):
    success: bool = True


class ConsultationCreateInput(BaseModel):
    title: str | None = Field(default=None, max_length=100)


class ConsultationUpdateInput(BaseModel):
    title: str | None = Field(default=None, max_length=100)
    messages: list[ChatMessageResponse] | None = None


class PlanProfile(BaseModel):
    province: str
    score: int = Field(ge=0, le=750)
    rank: int = Field(ge=1)
    subjects: list[str]


class PlanCreateInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    profile: PlanProfile | None = None
    rush: list[PlanChoice] = Field(default_factory=list)
    stable: list[PlanChoice] = Field(default_factory=list)
    safe: list[PlanChoice] = Field(default_factory=list)


class PlanUpdateInput(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    profile: PlanProfile | None = None
    rush: list[PlanChoice] | None = None
    stable: list[PlanChoice] | None = None
    safe: list[PlanChoice] | None = None


class AssessmentInput(BaseModel):
    province: str
    score: int = Field(ge=0, le=750)
    rank: int = Field(ge=1)
    subjects: list[str]


class AssessmentResponse(BaseModel):
    assessmentId: str
    estimatedRank: int
    recommendedPlans: list[PlanResponse]


class AuditSubmitInput(BaseModel):
    planId: str
    planContent: str = Field(min_length=1)


class AuditRisk(BaseModel):
    index: int
    level: Literal["低", "中", "高"]
    title: str
    description: str


class AuditResponse(BaseModel):
    auditId: str
    status: Literal["pending", "processing", "completed", "failed"]
    risks: list[AuditRisk]
    score: float = Field(ge=0, le=100)


class AuditStatusResponse(BaseModel):
    auditId: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = Field(ge=0, le=100)


class AdminShareLinkItem(BaseModel):
    code: str
    share_url: str
    result_type: Literal["review_result", "report"] = "report"
    target_id: str
    created_at: str | None = None
    expires_at_iso: str | None = None
    revoked: bool = False
    access_count: int = 0
    unique_visitors: int = 0
    last_access_at_iso: str | None = None


class AdminShareLinksResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AdminShareLinkItem]


class AdminShareLinkTrendPoint(BaseModel):
    date: str
    views: int


class AdminShareLinkAuditLog(BaseModel):
    id: str
    action: str
    actor: str | None = None
    createdAt: str | None = None
    note: str | None = None


class AdminShareLinkDetailResponse(BaseModel):
    link: AdminShareLinkItem
    stats: ShareLinkStatsResponse
    trend: list[AdminShareLinkTrendPoint]
    auditLogs: list[AdminShareLinkAuditLog]


class AdminPostersResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[PosterStatusResponse]


class PortalCWBResponse(BaseModel):
    token: str
    province: str
    year: int
    scoreType: ScoreType
    score: float
    rank: int
    equivalentScore: float


class PortalSchool(BaseModel):
    id: str
    name: str
    majors: list[str]
    admissionProbability: Literal["冲", "稳", "保"]


class PortalPlanPayload(BaseModel):
    id: str
    title: str
    schools: list[PortalSchool]


class PortalFullPlanResponse(BaseModel):
    token: str
    plan: PortalPlanPayload
    createdAt: str

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


def _consultation_store(request: Request) -> dict[str, ConsultationDetailResponse]:
    store = getattr(request.app.state, "react_consultations", None)
    if not isinstance(store, dict):
        store = {}
        request.app.state.react_consultations = store
    return store


def _sample_plan(plan_id: str = "plan-001") -> PlanResponse:
    return PlanResponse(
        id=plan_id,
        name="广东物理 620 冲稳保方案",
        rush=[
            PlanChoice(
                university="中山大学",
                major="计算机类",
                estScore=625,
                probability=42,
                risk="冲刺",
                riskType="rush",
                reason="学校层次高，适合作为冲刺选项，需结合当年位次复核。",
            )
        ],
        stable=[
            PlanChoice(
                university="华南师范大学",
                major="软件工程",
                estScore=612,
                probability=72,
                risk="稳妥",
                riskType="stable",
                reason="分数与往年录取区间接近，适合作为主体稳妥选择。",
            )
        ],
        safe=[
            PlanChoice(
                university="广东工业大学",
                major="自动化",
                estScore=595,
                probability=88,
                risk="保底",
                riskType="safe",
                reason="录取余量相对充足，可降低整体滑档风险。",
            )
        ],
        createdAt="2026-07-06T00:00:00+00:00",
    )


def _audit_store(request: Request) -> dict[str, AuditResponse]:
    store = getattr(request.app.state, "react_audits", None)
    if not isinstance(store, dict):
        store = {}
        request.app.state.react_audits = store
    return store


def _share_result_type(note: str | None) -> Literal["review_result", "report"]:
    prefix = str(note or "").partition(":")[0]
    return "review_result" if prefix == "review_result" else "report"


def _share_item(link: Any, request: Request, result_type: Literal["review_result", "report"] | None = None) -> AdminShareLinkItem:
    data = link.to_dict()
    stats = ShortLinkService(db_path=getattr(request.app.state.settings, "share_db_path")).get_stats(link.code) or {}
    resolved_type = result_type or _share_result_type(link.note)
    return AdminShareLinkItem(
        code=link.code,
        share_url=build_url(link.code, base=str(request.base_url).rstrip("/")),
        result_type=resolved_type,
        target_id=link.report_id,
        created_at=data.get("created_at_iso"),
        expires_at_iso=data.get("expires_at_iso"),
        revoked=bool(link.revoked),
        access_count=int(stats.get("access_count") or link.access_count or 0),
        unique_visitors=int(stats.get("unique_visitors") or 0),
        last_access_at_iso=stats.get("last_access_at_iso") or data.get("last_access_at_iso"),
    )


def _share_stats(stats: dict[str, Any] | None) -> ShareLinkStatsResponse:
    stats = stats or {}
    return ShareLinkStatsResponse(
        views=int(stats.get("access_count") or 0),
        uniqueVisitors=int(stats.get("unique_visitors") or 0),
        lastAccessedAt=stats.get("last_access_at_iso"),
    )


def _share_trend(stats: dict[str, Any] | None) -> list[AdminShareLinkTrendPoint]:
    return [
        AdminShareLinkTrendPoint(date=str(item.get("date") or ""), views=int(item.get("access_count") or 0))
        for item in list((stats or {}).get("daily_accesses") or [])
        if isinstance(item, dict)
    ]


def _plan_store(request: Request) -> dict[str, PlanResponse]:
    store = getattr(request.app.state, "react_plans", None)
    if not isinstance(store, dict):
        store = {}
        request.app.state.react_plans = store
    return store


def _chat_reply(payload: ChatSendInput) -> str:
    profile = payload.profile
    facts = []
    if profile and profile.province:
        facts.append(f"省份：{profile.province}")
    if profile and profile.score is not None:
        facts.append(f"分数：{profile.score}")
    if profile and profile.rank is not None:
        facts.append(f"位次：{profile.rank}")
    if profile and profile.subjects:
        facts.append(f"选科：{'/'.join(profile.subjects)}")
    fact_text = "；".join(facts) if facts else "暂未提供完整分数、位次和选科"
    return (
        f"我已收到你的问题：{payload.message}。\n\n"
        f"当前资料：{fact_text}。\n\n"
        "你可以继续补充分数、位次、选科和目标城市；资料完整后，我会按冲刺、稳妥、保底三档给出建议。"
    )


def _chat_response(payload: ChatSendInput, request: Request) -> ChatSendResponse:
    session_id = payload.sessionId or str(uuid4())
    now = _now_iso()
    user_message = ChatMessageResponse(
        id=f"user-{secrets.token_hex(4)}",
        role="user",
        content=payload.message,
        timestamp=now,
    )
    assistant_message = ChatMessageResponse(
        id=f"assistant-{secrets.token_hex(4)}",
        role="assistant",
        content=_chat_reply(payload),
        timestamp=now,
    )
    title = payload.message.strip()[:32] or "新咨询"
    _consultation_store(request)[session_id] = ConsultationDetailResponse(
        id=session_id,
        title=title,
        messages=[user_message, assistant_message],
        createdAt=now,
        updatedAt=now,
    )
    return ChatSendResponse(
        sessionId=session_id,
        userMessageId=user_message.id,
        assistantMessageId=assistant_message.id,
        assistantMessage=assistant_message,
    )


@router.post("/chat/send", response_model=ChatSendResponse)
def send_chat_message(payload: ChatSendInput, request: Request) -> ChatSendResponse:
    return _chat_response(payload, request)


@router.post("/chat/stream", response_model=ChatStreamResponse)
def stream_chat_message(payload: ChatSendInput, request: Request) -> ChatStreamResponse:
    response = _chat_response(payload, request)
    return ChatStreamResponse(content=response.assistantMessage.content)


@router.get("/chat/history", response_model=ChatHistoryResponse)
def get_chat_history(sessionId: str, request: Request) -> ChatHistoryResponse:
    consultation = _consultation_store(request).get(sessionId)
    if consultation is None:
        raise HTTPException(status_code=404, detail="chat history not found")
    return ChatHistoryResponse(sessionId=sessionId, messages=consultation.messages)


@router.get("/consultations", response_model=ConsultationListResponse)
def list_consultations(request: Request) -> ConsultationListResponse:
    items = [
        ConsultationItem(
            id=item.id,
            title=item.title,
            messageCount=len(item.messages),
            createdAt=item.createdAt,
            updatedAt=item.updatedAt,
        )
        for item in _consultation_store(request).values()
    ]
    return ConsultationListResponse(consultations=items, total=len(items))


@router.post("/consultations", response_model=ConsultationItem)
def create_consultation(payload: ConsultationCreateInput, request: Request) -> ConsultationItem:
    now = _now_iso()
    consultation_id = str(uuid4())
    title = (payload.title or "新咨询").strip() or "新咨询"
    _consultation_store(request)[consultation_id] = ConsultationDetailResponse(
        id=consultation_id,
        title=title,
        messages=[],
        createdAt=now,
        updatedAt=now,
    )
    return ConsultationItem(id=consultation_id, title=title, messageCount=0, createdAt=now, updatedAt=now)


@router.get("/consultations/{consultation_id}", response_model=ConsultationDetailResponse)
def get_consultation(consultation_id: str, request: Request) -> ConsultationDetailResponse:
    consultation = _consultation_store(request).get(consultation_id)
    if consultation is None:
        raise HTTPException(status_code=404, detail="consultation not found")
    return consultation


@router.patch("/consultations/{consultation_id}", response_model=SuccessResponse)
def update_consultation(consultation_id: str, payload: ConsultationUpdateInput, request: Request) -> SuccessResponse:
    store = _consultation_store(request)
    consultation = store.get(consultation_id)
    if consultation is None:
        raise HTTPException(status_code=404, detail="consultation not found")
    store[consultation_id] = consultation.model_copy(
        update={
            "title": payload.title or consultation.title,
            "messages": payload.messages if payload.messages is not None else consultation.messages,
            "updatedAt": _now_iso(),
        }
    )
    return SuccessResponse()


@router.delete("/consultations/{consultation_id}", response_model=SuccessResponse)
def delete_consultation(consultation_id: str, request: Request) -> SuccessResponse:
    if _consultation_store(request).pop(consultation_id, None) is None:
        raise HTTPException(status_code=404, detail="consultation not found")
    return SuccessResponse()


@router.get("/plans", response_model=PlanListResponse)
def list_plans(request: Request) -> PlanListResponse:
    plans = list(_plan_store(request).values())
    return PlanListResponse(plans=plans, total=len(plans))


@router.post("/plans", response_model=PlanResponse)
def create_plan(payload: PlanCreateInput, request: Request) -> PlanResponse:
    plan_id = f"plan_{secrets.token_hex(4)}"
    plan = PlanResponse(
        id=plan_id,
        name=payload.name,
        rush=payload.rush,
        stable=payload.stable,
        safe=payload.safe,
        createdAt=_now_iso(),
    )
    _plan_store(request)[plan_id] = plan
    return plan


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: str, request: Request) -> PlanResponse:
    plan = _plan_store(request).get(plan_id)
    if plan is None and plan_id == "plan-001":
        plan = _sample_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")
    return plan


@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: str, payload: PlanUpdateInput, request: Request) -> PlanResponse:
    store = _plan_store(request)
    plan = store.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")
    updated = plan.model_copy(
        update={
            "name": payload.name if payload.name is not None else plan.name,
            "rush": payload.rush if payload.rush is not None else plan.rush,
            "stable": payload.stable if payload.stable is not None else plan.stable,
            "safe": payload.safe if payload.safe is not None else plan.safe,
        }
    )
    store[plan_id] = updated
    return updated


@router.delete("/plans/{plan_id}", response_model=SuccessResponse)
def delete_plan(plan_id: str, request: Request) -> SuccessResponse:
    if _plan_store(request).pop(plan_id, None) is None:
        raise HTTPException(status_code=404, detail="plan not found")
    return SuccessResponse()

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


@router.get("/admin/posters", response_model=AdminPostersResponse)
def list_admin_posters(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    template: str | None = None,
    _: AdminUser = Depends(require_role("admin")),
) -> AdminPostersResponse:
    posters = list(_poster_store(request).values())
    if status:
        posters = [poster for poster in posters if poster.status == status]
    items = posters[offset : offset + limit]
    return AdminPostersResponse(total=len(posters), limit=limit, offset=offset, items=items)


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


@router.post("/assessment", response_model=AssessmentResponse)
def create_assessment(payload: AssessmentInput) -> AssessmentResponse:
    plan = _sample_plan(f"assessment_{secrets.token_hex(4)}")
    return AssessmentResponse(
        assessmentId=f"assessment_{secrets.token_hex(4)}",
        estimatedRank=payload.rank,
        recommendedPlans=[plan],
    )


@router.post("/audit/submit", response_model=AuditResponse)
def submit_audit(payload: AuditSubmitInput, request: Request) -> AuditResponse:
    audit = AuditResponse(
        auditId=f"audit_{secrets.token_hex(4)}",
        status="completed",
        risks=[
            AuditRisk(
                index=1,
                level="中",
                title="冲稳保结构需复核",
                description="请确认冲刺、稳妥、保底三档数量和风险承受能力匹配。",
            )
        ],
        score=82,
    )
    _audit_store(request)[audit.auditId] = audit
    return audit


@router.get("/audit/{audit_id}/status", response_model=AuditStatusResponse)
def get_audit_status(audit_id: str, request: Request) -> AuditStatusResponse:
    audit = _audit_store(request).get(audit_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="audit not found")
    return AuditStatusResponse(auditId=audit.auditId, status=audit.status, progress=100)


@router.get("/admin/share-links", response_model=AdminShareLinksResponse)
def list_admin_share_links(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    result_type: str | None = None,
    current_user: AdminUser = Depends(require_role("admin")),
    settings: Settings = Depends(get_settings_dep),
) -> AdminShareLinksResponse:
    svc = ShortLinkService(db_path=settings.share_db_path)
    links = svc.list_by_owner(current_user.username, limit=max(limit + offset, 1))
    if result_type:
        links = [link for link in links if _share_result_type(link.note) == result_type]
    if status:
        if status == "revoked":
            links = [link for link in links if link.revoked]
        elif status == "expired":
            links = [link for link in links if link.is_expired()]
        elif status == "active":
            links = [link for link in links if link.is_active()]
    items = [_share_item(link, request) for link in links[offset : offset + limit]]
    return AdminShareLinksResponse(total=len(links), limit=limit, offset=offset, items=items)


@router.get("/admin/share-links/{code}", response_model=AdminShareLinkDetailResponse)
def get_admin_share_link(
    code: str,
    request: Request,
    current_user: AdminUser = Depends(require_role("admin")),
    settings: Settings = Depends(get_settings_dep),
) -> AdminShareLinkDetailResponse:
    svc = ShortLinkService(db_path=settings.share_db_path)
    link = svc.get(code)
    if link is None or link.owner_id != current_user.username:
        raise HTTPException(status_code=404, detail="share link not found")
    stats = svc.get_stats(code) or {}
    item = _share_item(link, request)
    return AdminShareLinkDetailResponse(
        link=item,
        stats=_share_stats(stats),
        trend=_share_trend(stats),
        auditLogs=[
            AdminShareLinkAuditLog(
                id=f"share-{link.code}",
                action="created",
                actor=link.owner_id,
                createdAt=item.created_at,
                note=link.note,
            )
        ],
    )


@router.get("/portal/{token}/cwb", response_model=PortalCWBResponse)
def get_portal_cwb_json(token: str, settings: Settings = Depends(get_settings_dep)) -> PortalCWBResponse:
    from admin.routes.web_public import _build_portal_context, _resolve_order_from_token

    order = _resolve_order_from_token(token, settings)
    context = _build_portal_context(order, settings)
    intake = context.get("intake_summary") or {}
    subjects = "".join(intake.get("candidate_subjects") or [])
    score_type: ScoreType = "history" if "历史" in subjects else "physics"
    score = int(intake.get("candidate_score") or order.candidate_score or 0)
    rank = int(intake.get("candidate_rank") or order.candidate_rank or 1)
    return PortalCWBResponse(
        token=token,
        province=str(intake.get("candidate_province") or order.candidate_province or _FALLBACK_PROVINCE),
        year=2026,
        scoreType=score_type,
        score=score,
        rank=rank,
        equivalentScore=max(150, round(680 - rank / 350, 1)),
    )


@router.get("/portal/{token}/full-plan", response_model=PortalFullPlanResponse)
def get_portal_full_plan_json(token: str, settings: Settings = Depends(get_settings_dep)) -> PortalFullPlanResponse:
    from admin.routes.web_public import _resolve_order_from_token

    order = _resolve_order_from_token(token, settings)
    province = order.candidate_province or _FALLBACK_PROVINCE
    return PortalFullPlanResponse(
        token=token,
        plan=PortalPlanPayload(
            id=f"plan-{order.id}",
            title=f"{province} 志愿方案",
            schools=[
                PortalSchool(id="rush-1", name="中山大学", majors=["计算机类", "软件工程"], admissionProbability="冲"),
                PortalSchool(id="stable-1", name="湖南大学", majors=["自动化", "信息安全"], admissionProbability="稳"),
                PortalSchool(id="safe-1", name="长沙理工大学", majors=["电气工程", "交通运输"], admissionProbability="保"),
            ],
        ),
        createdAt=_now_iso(),
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
