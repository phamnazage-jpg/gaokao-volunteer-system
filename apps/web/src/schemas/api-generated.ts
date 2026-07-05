import { makeApi, Zodios, type ZodiosOptions } from "@zodios/core";
import { z } from "zod";

const LoginRequest = z
  .object({
    username: z.string().min(1).max(64),
    password: z.string().min(1).max(256),
  })
  .passthrough();
const LoginResponse = z
  .object({
    access_token: z.string(),
    token_type: z.string().optional().default("bearer"),
    expires_in: z.number().int(),
  })
  .passthrough();
const ValidationError = z
  .object({
    loc: z.array(z.union([z.string(), z.number()])),
    msg: z.string(),
    type: z.string(),
    input: z.unknown().optional(),
    ctx: z.object({}).partial().passthrough().optional(),
  })
  .passthrough();
const HTTPValidationError = z
  .object({ detail: z.array(ValidationError) })
  .partial()
  .passthrough();
const UserPublic = z
  .object({
    id: z.number().int(),
    username: z.string(),
    role: z.string(),
    is_active: z.boolean(),
    created_at: z.string(),
    last_login_at: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const category = z
  .union([z.enum(["success", "typical", "warning"]), z.null()])
  .optional();
const review_status = z
  .union([z.enum(["pending", "approved", "rejected"]), z.null()])
  .optional();
const CaseDetailResponse = z
  .object({
    review_status: z.enum(["pending", "approved", "rejected"]),
    review_note: z.union([z.string(), z.null()]).optional(),
    reviewer: z.union([z.string(), z.null()]).optional(),
    reviewed_at: z.union([z.string(), z.null()]).optional(),
    title: z.string().min(1),
    category: z.enum(["success", "typical", "warning"]),
    summary: z.union([z.string(), z.null()]).optional(),
    content: z.union([z.string(), z.null()]).optional(),
    tags: z.array(z.string()).optional(),
    id: z.number().int(),
    created_at: z.union([z.string(), z.null()]).optional(),
    updated_at: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const CaseListResponse = z
  .object({
    total: z.number().int(),
    limit: z.number().int(),
    offset: z.number().int(),
    items: z.array(CaseDetailResponse),
  })
  .passthrough();
const CaseBasePayload = z
  .object({
    title: z.string().min(1),
    category: z.enum(["success", "typical", "warning"]),
    summary: z.union([z.string(), z.null()]).optional(),
    content: z.union([z.string(), z.null()]).optional(),
    tags: z.array(z.string()).optional(),
  })
  .passthrough();
const ReviewCaseRequest = z
  .object({
    review_status: z.enum(["approved", "rejected"]),
    review_note: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const status = z
  .union([
    z.enum([
      "pending",
      "paid",
      "serving",
      "delivered",
      "completed",
      "refunded",
    ]),
    z.null(),
  ])
  .optional();
const source = z
  .union([z.enum(["xianyu", "wechat", "web", "school"]), z.null()])
  .optional();
const OrderSummaryResponse = z
  .object({
    id: z.string(),
    source: z.string(),
    external_id: z.union([z.string(), z.null()]).optional(),
    service_version: z.string(),
    status: z.string(),
    amount_cents: z.number().int(),
    customer_name: z.union([z.string(), z.null()]).optional(),
    customer_phone: z.union([z.string(), z.null()]).optional(),
    customer_wechat: z.union([z.string(), z.null()]).optional(),
    candidate_name: z.union([z.string(), z.null()]).optional(),
    candidate_province: z.union([z.string(), z.null()]).optional(),
    assigned_consultant: z.union([z.string(), z.null()]).optional(),
    intake_status: z.union([z.string(), z.null()]).optional(),
    intake_submitted_at: z.union([z.string(), z.null()]).optional(),
    created_at: z.union([z.string(), z.null()]).optional(),
    status_updated_at: z.union([z.string(), z.null()]).optional(),
    tags: z.array(z.string()).optional(),
  })
  .passthrough();
const ConsentInfo = z
  .object({
    consent_method: z.enum([
      "verbal_chat",
      "phone_recording",
      "screenshot",
      "written_form",
      "self_declared",
    ]),
    consent_note: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const CreateOrderRequest = z
  .object({
    source: z.enum(["xianyu", "wechat", "web", "school"]),
    external_id: z.union([z.string(), z.null()]).optional(),
    service_version: z.enum(["audit", "basic", "standard", "premium"]),
    amount_cents: z.number().int().gte(0),
    customer_name: z.union([z.string(), z.null()]).optional(),
    customer_phone: z.union([z.string(), z.null()]).optional(),
    customer_wechat: z.union([z.string(), z.null()]).optional(),
    candidate_name: z.union([z.string(), z.null()]).optional(),
    candidate_id_card: z.union([z.string(), z.null()]).optional(),
    candidate_province: z.union([z.string(), z.null()]).optional(),
    candidate_score: z.union([z.number(), z.null()]).optional(),
    candidate_rank: z.union([z.number(), z.null()]).optional(),
    candidate_subjects: z.array(z.string()).optional(),
    candidate_interests: z.union([z.string(), z.null()]).optional(),
    candidate_strong_subjects: z.union([z.string(), z.null()]).optional(),
    candidate_weak_subjects: z.union([z.string(), z.null()]).optional(),
    candidate_family: z.union([z.string(), z.null()]).optional(),
    assigned_consultant: z.union([z.string(), z.null()]).optional(),
    notes: z.union([z.string(), z.null()]).optional(),
    tags: z.array(z.string()).optional(),
    consent: ConsentInfo,
  })
  .passthrough();
const OrderHistoryItem = z
  .object({
    id: z.number().int(),
    order_id: z.string(),
    from_status: z.union([z.string(), z.null()]).optional(),
    to_status: z.string(),
    actor: z.union([z.string(), z.null()]).optional(),
    reason: z.union([z.string(), z.null()]).optional(),
    changed_at: z.string(),
  })
  .passthrough();
const OrderMutationResponse = z
  .object({
    order: z.object({}).partial().passthrough(),
    history: z.array(OrderHistoryItem),
    available_next_statuses: z.array(z.string()),
    action: z.string(),
  })
  .passthrough();
const OrderDetailPayload = z
  .object({
    order: z.object({}).partial().passthrough(),
    history: z.array(OrderHistoryItem),
    available_next_statuses: z.array(z.string()),
  })
  .passthrough();
const UpdateOrderRequest = z
  .object({
    updates: z.union([z.object({}).partial().passthrough(), z.null()]),
    to_status: z.union([
      z.enum([
        "pending",
        "paid",
        "serving",
        "delivered",
        "completed",
        "refunded",
      ]),
      z.null(),
    ]),
    reason: z.union([z.string(), z.null()]),
  })
  .partial()
  .passthrough();
const OrderDeletionResponse = z
  .object({
    action: z.string(),
    order_id: z.string(),
    files_deleted: z.number().int().optional().default(0),
  })
  .passthrough();
const ScoreLineItem = z
  .object({ batch: z.string(), score: z.number(), rank: z.number().int() })
  .passthrough();
const ScoreLineResponse = z
  .object({
    province: z.string(),
    year: z.number().int(),
    scoreType: z.enum(["physics", "history"]),
    lines: z.array(ScoreLineItem),
  })
  .passthrough();
const RankEstimatorResponse = z
  .object({
    province: z.string(),
    year: z.number().int(),
    scoreType: z.enum(["physics", "history"]),
    rank: z.number().int(),
    equivalentScore: z.number(),
  })
  .passthrough();
const keyword = z.union([z.string(), z.null()]).optional();
const MajorItem = z
  .object({ id: z.string(), name: z.string(), category: z.string() })
  .passthrough();
const MajorsResponse = z
  .object({ majors: z.array(MajorItem), total: z.number().int() })
  .passthrough();
const SchoolItem = z
  .object({
    id: z.string(),
    name: z.string(),
    province: z.string(),
    is985: z.boolean(),
    is211: z.boolean(),
  })
  .passthrough();
const SchoolsResponse = z
  .object({ schools: z.array(SchoolItem), total: z.number().int() })
  .passthrough();
const ReviewStartInput = z
  .object({
    planId: z.string().min(1),
    reviewerId: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const ReviewStatusResponse = z
  .object({
    id: z.string(),
    planId: z.string(),
    status: z.enum([
      "pending",
      "in_progress",
      "approved",
      "rejected",
      "changes_requested",
    ]),
    reviewerId: z.union([z.string(), z.null()]).optional(),
    comment: z.union([z.string(), z.null()]).optional(),
    updatedAt: z.string(),
  })
  .passthrough();
const ReviewActionInput = z
  .object({
    action: z.enum(["approve", "reject", "request_changes"]),
    reviewId: z.string().min(1),
    comment: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const PosterGenerateInput = z
  .object({
    planId: z.string().min(1),
    template: z
      .enum(["classic", "modern", "minimal"])
      .optional()
      .default("classic"),
  })
  .passthrough();
const PosterGenerateResponse = z
  .object({
    jobId: z.string(),
    status: z
      .enum(["queued", "processing", "completed", "failed"])
      .optional()
      .default("completed"),
    progress: z.number().int().gte(0).lte(100).optional().default(100),
    posterUrl: z.union([z.string(), z.null()]).optional(),
    qrCode: z.union([z.string(), z.null()]).optional(),
    expiresAt: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const PosterStatusResponse = z
  .object({
    jobId: z.string(),
    status: z.enum(["queued", "processing", "completed", "failed"]),
    progress: z.number().int().gte(0).lte(100),
    posterUrl: z.union([z.string(), z.null()]).optional(),
    qrCode: z.union([z.string(), z.null()]).optional(),
    expiresAt: z.union([z.string(), z.null()]).optional(),
    updatedAt: z.string(),
  })
  .passthrough();
const LLMConfigResponse = z
  .object({
    currentProvider: z.enum(["claude", "gpt", "gemini", "deepseek"]),
    fallbackOrder: z.array(z.enum(["claude", "gpt", "gemini", "deepseek"])),
    availableProviders: z.array(
      z.enum(["claude", "gpt", "gemini", "deepseek"])
    ),
  })
  .passthrough();
const AuditEnhanceInput = z
  .object({
    planId: z.string(),
    enhancementType: z
      .enum(["detail", "risk", "suggestion"])
      .optional()
      .default("detail"),
    baseAudit: z
      .union([z.object({}).partial().passthrough(), z.null()])
      .optional(),
  })
  .passthrough();
const Recommendation = z
  .object({
    title: z.string(),
    detail: z.string(),
    priority: z.enum(["low", "medium", "high"]),
  })
  .passthrough();
const AuditEnhancementResponse = z
  .object({
    summary: z.string(),
    recommendations: z.array(Recommendation),
    provider: z.enum(["claude", "gpt", "gemini", "deepseek"]),
  })
  .passthrough();
const LLMEnhanceStatusResponse = z
  .object({
    planId: z.string(),
    status: z.enum(["queued", "processing", "completed", "failed"]),
    progress: z.number().int().gte(0).lte(100),
    currentStep: z.string(),
    updatedAt: z.string(),
  })
  .passthrough();
const ShareLinkStatsResponse = z
  .object({
    views: z.number().int(),
    uniqueVisitors: z.number().int(),
    lastAccessedAt: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const DashboardResponse = z
  .object({
    summary: z.object({}).partial().passthrough(),
    by_status: z.object({}).partial().passthrough(),
    by_source: z.object({}).partial().passthrough(),
    by_service_version: z.object({}).partial().passthrough(),
    trends: z.object({}).partial().passthrough(),
    generated_at: z.string(),
  })
  .passthrough();
const OrderStatsResponse = z
  .object({
    total_orders: z.number().int(),
    total_revenue_cents: z.number().int(),
    by_status: z.object({}).partial().passthrough(),
    by_source: z.object({}).partial().passthrough(),
    by_service_version: z.object({}).partial().passthrough(),
  })
  .passthrough();
const UserSummaryResponse = z
  .object({
    user_key: z.string(),
    customer_name: z.union([z.string(), z.null()]).optional(),
    customer_phone: z.union([z.string(), z.null()]).optional(),
    customer_wechat: z.union([z.string(), z.null()]).optional(),
    candidate_name: z.union([z.string(), z.null()]).optional(),
    candidate_province: z.union([z.string(), z.null()]).optional(),
    order_count: z.number().int(),
    total_amount_cents: z.number().int(),
    latest_order_at: z.union([z.string(), z.null()]).optional(),
    latest_status: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const UserListResponse = z
  .object({
    total: z.number().int(),
    limit: z.number().int(),
    offset: z.number().int(),
    query: z.union([z.string(), z.null()]).optional(),
    items: z.array(UserSummaryResponse),
  })
  .passthrough();
const UserDetailResponse = z
  .object({
    user_key: z.string(),
    customer_name: z.union([z.string(), z.null()]).optional(),
    customer_phone: z.union([z.string(), z.null()]).optional(),
    customer_wechat: z.union([z.string(), z.null()]).optional(),
    candidate_name: z.union([z.string(), z.null()]).optional(),
    candidate_province: z.union([z.string(), z.null()]).optional(),
    order_count: z.number().int(),
    total_amount_cents: z.number().int(),
    latest_order_at: z.union([z.string(), z.null()]).optional(),
    latest_status: z.union([z.string(), z.null()]).optional(),
    orders: z.array(z.object({}).partial().passthrough()),
  })
  .passthrough();
const OpsAlertEventResponse = z
  .object({
    created_at: z.string(),
    alert_type: z.string(),
    title: z.string(),
    body: z.string(),
    details: z.object({}).partial().passthrough(),
  })
  .passthrough();
const OpsAlertListResponse = z
  .object({ total: z.number().int(), items: z.array(OpsAlertEventResponse) })
  .passthrough();
const NotificationEventResponse = z
  .object({
    order_id: z.string(),
    event_type: z.string(),
    channel: z.string(),
    status: z.string(),
    attempt_count: z.number().int(),
    last_attempt_at: z.union([z.string(), z.null()]).optional(),
    failure_reason: z.union([z.string(), z.null()]).optional(),
    created_at: z.string(),
    payload: z
      .union([z.object({}).partial().passthrough(), z.string(), z.null()])
      .optional(),
  })
  .passthrough();
const NotificationListResponse = z
  .object({
    total: z.number().int(),
    limit: z.number().int(),
    offset: z.number().int(),
    filters: z.object({}).partial().passthrough(),
    items: z.array(NotificationEventResponse),
  })
  .passthrough();
const PublicOrderCreate = z
  .object({
    service_version: z.enum(["audit", "basic", "standard", "premium"]),
    amount_cents: z.number().int().gte(0),
    customer_name: z.union([z.string(), z.null()]).optional(),
    customer_phone: z.union([z.string(), z.null()]).optional(),
    customer_wechat: z.union([z.string(), z.null()]).optional(),
    customer_email: z.union([z.string(), z.null()]).optional(),
    candidate_name: z.string().min(1),
    candidate_province: z.union([z.string(), z.null()]).optional(),
    notes: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const PublicOrderCreated = z
  .object({
    order_id: z.string(),
    source: z.string(),
    status: z.string(),
    service_version: z.string(),
    amount_cents: z.number().int(),
    next_step: z.string(),
    checkout_url: z.string(),
    portal_status_url: z.string(),
    portal_info_url: z.string(),
  })
  .passthrough();
const WebhookAck = z
  .object({
    payment_id: z.string(),
    processed: z.boolean(),
    idempotent: z.boolean(),
    order_status: z.string(),
  })
  .passthrough();
const Body_upload_order_attachment_portal__token__attachments_post = z
  .object({ files: z.array(z.string()) })
  .passthrough();
const PortalAttachmentUploaded = z
  .object({
    order_id: z.string(),
    intake_status: z.string(),
    stage: z.string(),
    attachments: z.array(z.object({}).partial().passthrough()),
  })
  .passthrough();
const IntakePayload = z
  .object({
    mode: z.enum(["draft", "submit"]).default("submit"),
    candidate_province: z.union([z.string(), z.null()]),
    candidate_score: z.union([z.number(), z.null()]),
    candidate_rank: z.union([z.number(), z.null()]),
    candidate_subjects: z.array(z.string()).max(6),
    candidate_interests: z.union([z.string(), z.null()]),
    target_cities: z.array(z.string()).max(5),
    target_majors: z.array(z.string()).max(10),
    university_preferences: z.union([z.string(), z.null()]),
    school_region_preferences: z.array(z.string()).max(10),
    school_preference_types: z.array(z.string()).max(10),
    target_schools: z.array(z.string()).max(10),
    disliked_majors: z.array(z.string()).max(10),
    priority_strategy: z.union([z.string(), z.null()]),
    graduation_plan: z.union([z.string(), z.null()]),
    tuition_preference: z.union([z.string(), z.null()]),
    employment_region_preferences: z.array(z.string()).max(10),
    family_background: z.union([z.string(), z.null()]),
    industry_resources: z.union([z.string(), z.null()]),
    extra_notes: z.union([z.string(), z.null()]),
    interest_assessment_type: z.union([z.string(), z.null()]),
    interest_assessment_result: z.union([z.string(), z.null()]),
    interest_assessment_notes: z.union([z.string(), z.null()]),
    existing_plan_summary: z.union([z.string(), z.null()]),
    guardian_notes: z.union([z.string(), z.null()]),
    consent_version: z.union([z.string(), z.null()]),
    consent_scope: z.union([z.string(), z.null()]),
    privacy_accepted: z.boolean().default(false),
    service_terms_accepted: z.boolean().default(false),
    guardian_confirmed: z.boolean().default(false),
  })
  .partial()
  .passthrough();
const PortalIntakeResponse = z
  .object({
    intake_status: z.string(),
    stage: z.string(),
    order_id: z.string(),
    profile_minimum_complete: z.boolean(),
    profile_missing_fields: z.array(z.string()),
  })
  .passthrough();
const DeletionRequestCreate = z
  .object({
    requester_name: z.string().min(1).max(64),
    requester_contact: z.string().min(1).max(128),
    reason: z.string().min(1).max(2000),
    scope: z.enum(["order_only", "order_and_attachments", "full_account"]),
    confirm_guardian: z.boolean(),
  })
  .passthrough();
const DeletionRequestCreated = z
  .object({
    order_id: z.string(),
    request_logged: z.boolean(),
    next_step: z.string(),
  })
  .passthrough();

export const schemas = {
  LoginRequest,
  LoginResponse,
  ValidationError,
  HTTPValidationError,
  UserPublic,
  category,
  review_status,
  CaseDetailResponse,
  CaseListResponse,
  CaseBasePayload,
  ReviewCaseRequest,
  status,
  source,
  OrderSummaryResponse,
  ConsentInfo,
  CreateOrderRequest,
  OrderHistoryItem,
  OrderMutationResponse,
  OrderDetailPayload,
  UpdateOrderRequest,
  OrderDeletionResponse,
  ScoreLineItem,
  ScoreLineResponse,
  RankEstimatorResponse,
  keyword,
  MajorItem,
  MajorsResponse,
  SchoolItem,
  SchoolsResponse,
  ReviewStartInput,
  ReviewStatusResponse,
  ReviewActionInput,
  PosterGenerateInput,
  PosterGenerateResponse,
  PosterStatusResponse,
  LLMConfigResponse,
  AuditEnhanceInput,
  Recommendation,
  AuditEnhancementResponse,
  LLMEnhanceStatusResponse,
  ShareLinkStatsResponse,
  DashboardResponse,
  OrderStatsResponse,
  UserSummaryResponse,
  UserListResponse,
  UserDetailResponse,
  OpsAlertEventResponse,
  OpsAlertListResponse,
  NotificationEventResponse,
  NotificationListResponse,
  PublicOrderCreate,
  PublicOrderCreated,
  WebhookAck,
  Body_upload_order_attachment_portal__token__attachments_post,
  PortalAttachmentUploaded,
  IntakePayload,
  PortalIntakeResponse,
  DeletionRequestCreate,
  DeletionRequestCreated,
};

const endpoints = makeApi([
  {
    method: "get",
    path: "/api/admin/cases",
    alias: "list_cases_api_admin_cases_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(200).optional().default(50),
      },
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().gte(0).optional().default(0),
      },
      {
        name: "category",
        type: "Query",
        schema: category,
      },
      {
        name: "review_status",
        type: "Query",
        schema: review_status,
      },
    ],
    response: CaseListResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/admin/cases",
    alias: "create_case_api_admin_cases_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CaseBasePayload,
      },
    ],
    response: CaseDetailResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/admin/cases/:case_id",
    alias: "get_case_api_admin_cases__case_id__get",
    requestFormat: "json",
    parameters: [
      {
        name: "case_id",
        type: "Path",
        schema: z.number().int().gte(1),
      },
    ],
    response: CaseDetailResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "patch",
    path: "/api/admin/cases/:case_id",
    alias: "update_case_api_admin_cases__case_id__patch",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CaseBasePayload,
      },
      {
        name: "case_id",
        type: "Path",
        schema: z.number().int().gte(1),
      },
    ],
    response: CaseDetailResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/api/admin/cases/:case_id",
    alias: "delete_case_api_admin_cases__case_id__delete",
    requestFormat: "json",
    parameters: [
      {
        name: "case_id",
        type: "Path",
        schema: z.number().int().gte(1),
      },
    ],
    response: z.void(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/admin/cases/:case_id/review",
    alias: "review_case_api_admin_cases__case_id__review_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ReviewCaseRequest,
      },
      {
        name: "case_id",
        type: "Path",
        schema: z.number().int().gte(1),
      },
    ],
    response: CaseDetailResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/admin/notifications",
    alias: "list_notifications_api_admin_notifications_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(200).optional().default(50),
      },
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().gte(0).optional().default(0),
      },
      {
        name: "order_id",
        type: "Query",
        schema: keyword,
      },
      {
        name: "status",
        type: "Query",
        schema: keyword,
      },
      {
        name: "channel",
        type: "Query",
        schema: keyword,
      },
    ],
    response: NotificationListResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/admin/notifications/deletion-requests",
    alias:
      "list_deletion_requests_api_admin_notifications_deletion_requests_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(200).optional().default(50),
      },
      {
        name: "order_id",
        type: "Query",
        schema: keyword,
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/admin/notifications/ops-alerts",
    alias: "list_ops_alerts_api_admin_notifications_ops_alerts_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(200).optional().default(50),
      },
    ],
    response: OpsAlertListResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/admin/orders",
    alias: "list_orders_api_admin_orders_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(200).optional().default(50),
      },
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().gte(0).optional().default(0),
      },
      {
        name: "status",
        type: "Query",
        schema: status,
      },
      {
        name: "source",
        type: "Query",
        schema: source,
      },
    ],
    response: z.array(OrderSummaryResponse),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/admin/orders",
    alias: "create_order_api_admin_orders_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CreateOrderRequest,
      },
    ],
    response: OrderMutationResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/admin/orders/:order_id",
    alias: "get_order_api_admin_orders__order_id__get",
    requestFormat: "json",
    parameters: [
      {
        name: "order_id",
        type: "Path",
        schema: z.string().min(1),
      },
    ],
    response: OrderDetailPayload,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "patch",
    path: "/api/admin/orders/:order_id",
    alias: "patch_order_api_admin_orders__order_id__patch",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: UpdateOrderRequest,
      },
      {
        name: "order_id",
        type: "Path",
        schema: z.string().min(1),
      },
    ],
    response: OrderMutationResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/api/admin/orders/:order_id",
    alias: "delete_or_anonymize_order_api_admin_orders__order_id__delete",
    requestFormat: "json",
    parameters: [
      {
        name: "order_id",
        type: "Path",
        schema: z.string().min(1),
      },
      {
        name: "mode",
        type: "Query",
        schema: z.enum(["delete", "anonymize"]).optional().default("delete"),
      },
      {
        name: "reason",
        type: "Query",
        schema: z.string().min(1),
      },
    ],
    response: OrderDeletionResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/admin/orders/export",
    alias: "export_orders_csv_api_admin_orders_export_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(1000).optional().default(1000),
      },
      {
        name: "status",
        type: "Query",
        schema: status,
      },
      {
        name: "source",
        type: "Query",
        schema: source,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/admin/stats/dashboard",
    alias: "get_dashboard_api_admin_stats_dashboard_get",
    description: `���ع�����̨�Ǳ������� payload: summary(����/�û�/���� + ����/7d/30d ��Ƭ) + 6 ̬�ֲ� + ��Դ�ֲ� + ����汾�ֲ� + ����/7d/30d �������� (������, 0 ���)��`,
    requestFormat: "json",
    response: DashboardResponse,
  },
  {
    method: "get",
    path: "/api/admin/stats/orders",
    alias: "get_order_stats_api_admin_stats_orders_get",
    description: `����ά��ͳ��:T6.1 �׶�Ϊռλ,T6.2 ������ʵ SQL �ۺϡ��ֶ������� T6.1 stub �׶β���,ǰ�˾���Լ���ơ�`,
    requestFormat: "json",
    response: OrderStatsResponse,
  },
  {
    method: "get",
    path: "/api/admin/users",
    alias: "list_users_api_admin_users_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(200).optional().default(50),
      },
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().gte(0).optional().default(0),
      },
      {
        name: "q",
        type: "Query",
        schema: keyword,
      },
    ],
    response: UserListResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/admin/users/:user_key",
    alias: "get_user_detail_api_admin_users__user_key__get",
    requestFormat: "json",
    parameters: [
      {
        name: "user_key",
        type: "Path",
        schema: z.string().min(1),
      },
    ],
    response: UserDetailResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/auth/login",
    alias: "login_api_auth_login_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: LoginRequest,
      },
    ],
    response: LoginResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/auth/me",
    alias: "me_api_auth_me_get",
    requestFormat: "json",
    response: UserPublic,
  },
  {
    method: "get",
    path: "/api/cases",
    alias: "list_cases_api_cases_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(200).optional().default(50),
      },
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().gte(0).optional().default(0),
      },
      {
        name: "category",
        type: "Query",
        schema: category,
      },
      {
        name: "review_status",
        type: "Query",
        schema: review_status,
      },
    ],
    response: CaseListResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/cases",
    alias: "create_case_api_cases_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CaseBasePayload,
      },
    ],
    response: CaseDetailResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/cases/:case_id",
    alias: "get_case_api_cases__case_id__get",
    requestFormat: "json",
    parameters: [
      {
        name: "case_id",
        type: "Path",
        schema: z.number().int().gte(1),
      },
    ],
    response: CaseDetailResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "patch",
    path: "/api/cases/:case_id",
    alias: "update_case_api_cases__case_id__patch",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CaseBasePayload,
      },
      {
        name: "case_id",
        type: "Path",
        schema: z.number().int().gte(1),
      },
    ],
    response: CaseDetailResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/api/cases/:case_id",
    alias: "delete_case_api_cases__case_id__delete",
    requestFormat: "json",
    parameters: [
      {
        name: "case_id",
        type: "Path",
        schema: z.number().int().gte(1),
      },
    ],
    response: z.void(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/cases/:case_id/review",
    alias: "review_case_api_cases__case_id__review_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ReviewCaseRequest,
      },
      {
        name: "case_id",
        type: "Path",
        schema: z.number().int().gte(1),
      },
    ],
    response: CaseDetailResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/data-query/majors",
    alias: "list_majors_api_data_query_majors_get",
    requestFormat: "json",
    parameters: [
      {
        name: "keyword",
        type: "Query",
        schema: keyword,
      },
    ],
    response: MajorsResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/data-query/rank-estimator",
    alias: "get_rank_estimator_api_data_query_rank_estimator_get",
    requestFormat: "json",
    parameters: [
      {
        name: "province",
        type: "Query",
        schema: z.string(),
      },
      {
        name: "year",
        type: "Query",
        schema: z.number().int(),
      },
      {
        name: "scoreType",
        type: "Query",
        schema: z.enum(["physics", "history"]),
      },
      {
        name: "rank",
        type: "Query",
        schema: z.number().int(),
      },
    ],
    response: RankEstimatorResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/data-query/schools",
    alias: "list_schools_api_data_query_schools_get",
    requestFormat: "json",
    parameters: [
      {
        name: "keyword",
        type: "Query",
        schema: keyword,
      },
    ],
    response: SchoolsResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/data-query/score-line",
    alias: "get_score_line_api_data_query_score_line_get",
    requestFormat: "json",
    parameters: [
      {
        name: "province",
        type: "Query",
        schema: z.string(),
      },
      {
        name: "year",
        type: "Query",
        schema: z.number().int(),
      },
      {
        name: "scoreType",
        type: "Query",
        schema: z.enum(["physics", "history"]),
      },
    ],
    response: ScoreLineResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/llm/:provider/enhance",
    alias: "enhance_audit_api_llm__provider__enhance_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AuditEnhanceInput,
      },
      {
        name: "provider",
        type: "Path",
        schema: z.enum(["claude", "gpt", "gemini", "deepseek"]),
      },
    ],
    response: AuditEnhancementResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/llm/config",
    alias: "get_llm_config_api_llm_config_get",
    requestFormat: "json",
    response: LLMConfigResponse,
  },
  {
    method: "get",
    path: "/api/llm/enhance/:plan_id/status",
    alias: "get_llm_enhance_status_api_llm_enhance__plan_id__status_get",
    requestFormat: "json",
    parameters: [
      {
        name: "plan_id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: LLMEnhanceStatusResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/meta",
    alias: "meta_api_meta_get",
    requestFormat: "json",
    response: z.object({}).partial().passthrough(),
  },
  {
    method: "get",
    path: "/api/orders",
    alias: "list_orders_api_orders_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(200).optional().default(50),
      },
      {
        name: "offset",
        type: "Query",
        schema: z.number().int().gte(0).optional().default(0),
      },
      {
        name: "status",
        type: "Query",
        schema: status,
      },
      {
        name: "source",
        type: "Query",
        schema: source,
      },
    ],
    response: z.array(OrderSummaryResponse),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/orders",
    alias: "create_order_api_orders_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CreateOrderRequest,
      },
    ],
    response: OrderMutationResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/orders/:order_id",
    alias: "get_order_api_orders__order_id__get",
    requestFormat: "json",
    parameters: [
      {
        name: "order_id",
        type: "Path",
        schema: z.string().min(1),
      },
    ],
    response: OrderDetailPayload,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "patch",
    path: "/api/orders/:order_id",
    alias: "patch_order_api_orders__order_id__patch",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: UpdateOrderRequest,
      },
      {
        name: "order_id",
        type: "Path",
        schema: z.string().min(1),
      },
    ],
    response: OrderMutationResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/api/orders/:order_id",
    alias: "delete_or_anonymize_order_api_orders__order_id__delete",
    requestFormat: "json",
    parameters: [
      {
        name: "order_id",
        type: "Path",
        schema: z.string().min(1),
      },
      {
        name: "mode",
        type: "Query",
        schema: z.enum(["delete", "anonymize"]).optional().default("delete"),
      },
      {
        name: "reason",
        type: "Query",
        schema: z.string().min(1),
      },
    ],
    response: OrderDeletionResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/orders/export",
    alias: "export_orders_csv_api_orders_export_get",
    requestFormat: "json",
    parameters: [
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(1000).optional().default(1000),
      },
      {
        name: "status",
        type: "Query",
        schema: status,
      },
      {
        name: "source",
        type: "Query",
        schema: source,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/poster/:job_id/status",
    alias: "get_poster_status_api_poster__job_id__status_get",
    requestFormat: "json",
    parameters: [
      {
        name: "job_id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: PosterStatusResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/poster/generate",
    alias: "generate_poster_api_poster_generate_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PosterGenerateInput,
      },
    ],
    response: PosterGenerateResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/public/orders",
    alias: "create_public_order_endpoint_api_public_orders_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PublicOrderCreate,
      },
    ],
    response: PublicOrderCreated,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/public/payments/mock/webhook",
    alias: "mock_payment_webhook_api_public_payments_mock_webhook_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({}).partial().passthrough(),
      },
    ],
    response: WebhookAck,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/review/:review_id/status",
    alias: "get_review_status_api_review__review_id__status_get",
    requestFormat: "json",
    parameters: [
      {
        name: "review_id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: ReviewStatusResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/review/action",
    alias: "apply_review_action_api_review_action_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ReviewActionInput,
      },
    ],
    response: ReviewStatusResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/review/start",
    alias: "start_review_api_review_start_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ReviewStartInput,
      },
    ],
    response: ReviewStatusResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/share-link",
    alias: "create_share_link_api_share_link_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({}).partial().passthrough(),
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/api/share-link/:code/revoke",
    alias: "revoke_share_link_api_share_link__code__revoke_post",
    requestFormat: "json",
    parameters: [
      {
        name: "code",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/share-link/:code/stats",
    alias: "get_share_link_stats_api_share_link__code__stats_get",
    requestFormat: "json",
    parameters: [
      {
        name: "code",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: ShareLinkStatsResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/share-link/latest",
    alias: "latest_share_link_api_share_link_latest_get",
    requestFormat: "json",
    parameters: [
      {
        name: "result_type",
        type: "Query",
        schema: z.string(),
      },
      {
        name: "target_token",
        type: "Query",
        schema: z.string(),
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/api/stats/dashboard",
    alias: "get_dashboard_api_stats_dashboard_get",
    description: `���ع�����̨�Ǳ������� payload: summary(����/�û�/���� + ����/7d/30d ��Ƭ) + 6 ̬�ֲ� + ��Դ�ֲ� + ����汾�ֲ� + ����/7d/30d �������� (������, 0 ���)��`,
    requestFormat: "json",
    response: DashboardResponse,
  },
  {
    method: "get",
    path: "/api/stats/orders",
    alias: "get_order_stats_api_stats_orders_get",
    description: `����ά��ͳ��:T6.1 �׶�Ϊռλ,T6.2 ������ʵ SQL �ۺϡ��ֶ������� T6.1 stub �׶β���,ǰ�˾���Լ���ơ�`,
    requestFormat: "json",
    response: OrderStatsResponse,
  },
  {
    method: "get",
    path: "/health",
    alias: "health_health_get",
    description: `�����˵㡣ֻ���� readiness, ����¶����/·��/�汾ϸ�ڡ�

���ؽṹ:
- status: &quot;ok&quot; �� &quot;degraded&quot;����һ readiness ���ʧ��ʱ������
- checks: {db_writable, disk_writable, settings_valid} �Ӷ���

readiness ���壨2026-06-27 P1-4 �޸���:
- ���� checks ͨ�� �� status&#x3D;&quot;ok&quot;, HTTP 200
- ��һ check ʧ�� �� status&#x3D;&quot;degraded&quot;, HTTP 503
- K8s/systemd readiness probe Ӧ�� HTTP status����ֻ�� status �ֶ�`,
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/portal/:token/attachments",
    alias: "upload_order_attachment_portal__token__attachments_post",
    requestFormat: "form-data",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: Body_upload_order_attachment_portal__token__attachments_post,
      },
      {
        name: "token",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: PortalAttachmentUploaded,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/portal/:token/deletion-request",
    alias: "submit_deletion_request_portal__token__deletion_request_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: DeletionRequestCreate,
      },
      {
        name: "token",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: DeletionRequestCreated,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/portal/:token/info",
    alias: "submit_order_info_portal__token__info_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: IntakePayload,
      },
      {
        name: "token",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: PortalIntakeResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/portal/share-link",
    alias: "portal_create_share_link_portal_share_link_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({}).partial().passthrough(),
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/portal/share-link/:code/revoke",
    alias: "portal_revoke_share_link_portal_share_link__code__revoke_post",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({}).partial().passthrough(),
      },
      {
        name: "code",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/portal/share-link/latest",
    alias: "portal_latest_share_link_portal_share_link_latest_get",
    requestFormat: "json",
    parameters: [
      {
        name: "result_type",
        type: "Query",
        schema: z.string(),
      },
      {
        name: "target_token",
        type: "Query",
        schema: z.string(),
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
]);

export const api = new Zodios(endpoints);

export function createApiClient(baseUrl: string, options?: ZodiosOptions) {
  return new Zodios(baseUrl, endpoints, options);
}
