/**
 * V10 option B · Message types.
 * Replaces Message from the legacy useChat.ts prototype, which used data?: any.
 *
 * Uses a Zod discriminated union instead of any. G1 gate requires 0 any.
 */
import { z } from 'zod';

// ====== Message subtype schemas ======

export const TextMessageDataSchema = z.object({
  type: z.literal('text'),
});
export type TextMessageData = z.infer<typeof TextMessageDataSchema>;

export const FormCardMessageDataSchema = z.object({
  type: z.literal('form_card'),
  fields: z.array(
    z.object({
      key: z.string(),
      label: z.string(),
      kind: z.enum(['text', 'number', 'select']),
      options: z.array(z.string()).optional(),
      required: z.boolean().default(false),
    }),
  ),
});
export type FormCardMessageData = z.infer<typeof FormCardMessageDataSchema>;

export const PlanCardMessageDataSchema = z.object({
  type: z.literal('plan_card'),
  rush: z.array(
    z.object({
      university: z.string(),
      major: z.string(),
      estScore: z.number(),
      probability: z.number().min(0).max(100),
      risk: z.string(),
      riskType: z.string(),
      reason: z.string(),
    }),
  ),
  stable: z.array(
    z.object({
      university: z.string(),
      major: z.string(),
      estScore: z.number(),
      probability: z.number().min(0).max(100),
      risk: z.string(),
      riskType: z.string(),
      reason: z.string(),
    }),
  ),
  safe: z.array(
    z.object({
      university: z.string(),
      major: z.string(),
      estScore: z.number(),
      probability: z.number().min(0).max(100),
      risk: z.string(),
      riskType: z.string(),
      reason: z.string(),
    }),
  ),
});
export type PlanCardMessageData = z.infer<typeof PlanCardMessageDataSchema>;

export const CareerCardMessageDataSchema = z.object({
  type: z.literal('career_card'),
  careers: z.array(
    z.object({
      name: z.string(),
      description: z.string(),
      salary: z.string(),
      prospect: z.enum(['\u597d', '\u4e2d', '\u5dee']),
    }),
  ),
});
export type CareerCardMessageData = z.infer<typeof CareerCardMessageDataSchema>;

export const AuditReportMessageDataSchema = z.object({
  type: z.literal('audit_report'),
  risks: z.array(
    z.object({
      index: z.number(),
      level: z.enum(['\u4f4e', '\u4e2d', '\u9ad8']),
      title: z.string(),
      description: z.string(),
    }),
  ),
  score: z.number().min(0).max(100),
});
export type AuditReportMessageData = z.infer<typeof AuditReportMessageDataSchema>;

export const FileUploadPromptMessageDataSchema = z.object({
  type: z.literal('file_upload_prompt'),
  acceptedFormats: z.array(z.string()),
  maxSize: z.number(),
});
export type FileUploadPromptMessageData = z.infer<typeof FileUploadPromptMessageDataSchema>;

export const SystemMessageDataSchema = z.object({
  type: z.literal('system'),
  level: z.enum(['info', 'warning', 'error']),
});
export type SystemMessageData = z.infer<typeof SystemMessageDataSchema>;

// ====== Discriminated Union ======

export const MessageTypeSchema = z.discriminatedUnion('type', [
  TextMessageDataSchema,
  FormCardMessageDataSchema,
  PlanCardMessageDataSchema,
  CareerCardMessageDataSchema,
  AuditReportMessageDataSchema,
  FileUploadPromptMessageDataSchema,
  SystemMessageDataSchema,
]);
export type MessageTypeData = z.infer<typeof MessageTypeSchema>;

export const MessageRoleSchema = z.enum(['user', 'assistant', 'system']);
export type MessageRole = z.infer<typeof MessageRoleSchema>;

// ====== Top-level Message schema (G1 gate: 0 any) ======

export const MessageSchema = z.object({
  id: z.string(),
  role: MessageRoleSchema,
  content: z.string(),
  data: MessageTypeSchema.optional(),
  timestamp: z.date(),
  /** Streaming intermediate-state marker. */
  isStreaming: z.boolean().optional(),
});
export type Message = z.infer<typeof MessageSchema>;

// ====== Type guard helpers ======

export const isTextMessage = (m: Message): m is Message & { data: TextMessageData } => m.data?.type === 'text';
export const isFormCard = (m: Message): m is Message & { data: FormCardMessageData } => m.data?.type === 'form_card';
export const isPlanCard = (m: Message): m is Message & { data: PlanCardMessageData } => m.data?.type === 'plan_card';
export const isCareerCard = (m: Message): m is Message & { data: CareerCardMessageData } => m.data?.type === 'career_card';
export const isAuditReport = (m: Message): m is Message & { data: AuditReportMessageData } => m.data?.type === 'audit_report';
export const isFileUploadPrompt = (m: Message): m is Message & { data: FileUploadPromptMessageData } => m.data?.type === 'file_upload_prompt';
export const isSystemMessage = (m: Message): m is Message & { data: SystemMessageData } => m.data?.type === 'system';
