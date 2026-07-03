/**
 * V10 选项 B · API Schemas (Zod)
 * 对应后端 OpenAPI 自动生成的 schemas/api.ts
 * 现阶段手写, Sprint 2 中接 openapi-zod-client 替换为 codegen
 */
import { z } from 'zod';

// ====== Chat ======
export const ChatSendInputSchema = z.object({
  message: z.string().min(1).max(2000),
  sessionId: z.string().uuid().optional(),
  userName: z.string().optional(),
  profile: z
    .object({
      province: z.string().optional(),
      score: z.number().int().min(0).max(750).optional(),
      rank: z.number().int().min(1).optional(),
      subjects: z.array(z.string()).optional(),
    })
    .optional(),
});
export type ChatSendInput = z.infer<typeof ChatSendInputSchema>;

export const ChatMessageSchema = z.object({
  id: z.string(),
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  data: z.unknown().optional(),
  timestamp: z.string(),
});
export type ChatMessage = z.infer<typeof ChatMessageSchema>;

export const ChatSendResponseSchema = z.object({
  sessionId: z.string().uuid(),
  userMessageId: z.string(),
  assistantMessageId: z.string(),
  assistantMessage: ChatMessageSchema,
});
export type ChatSendResponse = z.infer<typeof ChatSendResponseSchema>;

export const ChatHistoryResponseSchema = z.object({
  sessionId: z.string().uuid(),
  messages: z.array(ChatMessageSchema),
});
export type ChatHistoryResponse = z.infer<typeof ChatHistoryResponseSchema>;

// ====== Plan ======
export const PlanSchema = z.object({
  id: z.string(),
  name: z.string(),
  rush: z.array(
    z.object({
      university: z.string(),
      major: z.string(),
      estScore: z.number(),
      probability: z.number(),
      risk: z.string(),
      riskType: z.string(),
      reason: z.string(),
    }),
  ),
  stable: z.array(z.unknown()),
  safe: z.array(z.unknown()),
  createdAt: z.string(),
});
export type Plan = z.infer<typeof PlanSchema>;

export const PlanListResponseSchema = z.object({
  plans: z.array(PlanSchema),
  total: z.number().int(),
});
export type PlanListResponse = z.infer<typeof PlanListResponseSchema>;

export const PlanCreateInputSchema = z.object({
  name: z.string().min(1).max(100),
  profile: z.object({
    province: z.string(),
    score: z.number().int().min(0).max(750),
    rank: z.number().int().min(1),
    subjects: z.array(z.string()).min(1),
  }),
  rush: z.array(z.unknown()),
  stable: z.array(z.unknown()),
  safe: z.array(z.unknown()),
});
export type PlanCreateInput = z.infer<typeof PlanCreateInputSchema>;

// ====== Consultation ======
export const ConsultationSchema = z.object({
  id: z.string(),
  title: z.string(),
  messageCount: z.number().int(),
  createdAt: z.string(),
  updatedAt: z.string(),
});
export type Consultation = z.infer<typeof ConsultationSchema>;

export const ConsultationListResponseSchema = z.object({
  consultations: z.array(ConsultationSchema),
  total: z.number().int(),
});
export type ConsultationListResponse = z.infer<typeof ConsultationListResponseSchema>;

// ====== Assessment ======
export const AssessmentInputSchema = z.object({
  province: z.string().min(1),
  score: z.number().int().min(0).max(750),
  rank: z.number().int().min(1),
  subjects: z.array(z.string()).min(1),
});
export type AssessmentInput = z.infer<typeof AssessmentInputSchema>;

export const AssessmentResponseSchema = z.object({
  assessmentId: z.string(),
  estimatedRank: z.number().int(),
  recommendedPlans: z.array(PlanSchema),
});
export type AssessmentResponse = z.infer<typeof AssessmentResponseSchema>;

// ====== Audit ======
export const AuditSubmitInputSchema = z.object({
  planId: z.string(),
  planContent: z.string().min(1),
});
export type AuditSubmitInput = z.infer<typeof AuditSubmitInputSchema>;

export const AuditResponseSchema = z.object({
  auditId: z.string(),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
  risks: z.array(
    z.object({
      index: z.number(),
      level: z.enum(['低', '中', '高']),
      title: z.string(),
      description: z.string(),
    }),
  ),
  score: z.number().min(0).max(100),
});
export type AuditResponse = z.infer<typeof AuditResponseSchema>;

// ====== Upload ======
export const UploadResponseSchema = z.object({
  fileId: z.string(),
  url: z.string().url(),
  size: z.number().int(),
  mimeType: z.string(),
});
export type UploadResponse = z.infer<typeof UploadResponseSchema>;

// ====== LLM Audit Enhance (Sprint 3 · T-B-17 / T-B-26) ======
export const AuditEnhanceInputSchema = z.object({
  planId: z.string(),
  baseAudit: AuditResponseSchema.optional(),
  enhancementType: z.enum(['detail', 'risk', 'suggestion']).default('detail'),
});
export type AuditEnhanceInput = z.infer<typeof AuditEnhanceInputSchema>;

export const AuditEnhancementSchema = z.object({
  summary: z.string(),
  recommendations: z.array(
    z.object({
      title: z.string(),
      detail: z.string(),
      priority: z.enum(['low', 'medium', 'high']),
    }),
  ),
  provider: z.enum(['claude', 'gpt', 'gemini', 'deepseek']).optional(),
});
export type AuditEnhancement = z.infer<typeof AuditEnhancementSchema>;
