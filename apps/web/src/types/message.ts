/**
 * V10 选项 B · Message 类型
 * 替代原型 useChat.ts 中的 Message (其中 data?: any)
 *
 * 用 Zod discriminated union 替代 any, G1 闸门要求 0 any
 */
import { z } from 'zod';

// ====== 消息子类型 schemas ======

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
      prospect: z.enum(['好', '中', '差']),
    }),
  ),
});
export type CareerCardMessageData = z.infer<typeof CareerCardMessageDataSchema>;

export const AuditReportMessageDataSchema = z.object({
  type: z.literal('audit_report'),
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

// ====== Message 顶层 schema (G1 闸门: 0 any) ======

export const MessageSchema = z.object({
  id: z.string(),
  role: MessageRoleSchema,
  content: z.string(),
  data: MessageTypeSchema.optional(),
  timestamp: z.date(),
  /** 流式中间态标识 */
  isStreaming: z.boolean().optional(),
});
export type Message = z.infer<typeof MessageSchema>;

// ====== 类型守卫 helpers ======

export const isTextMessage = (m: Message): m is Message & { data: TextMessageData } => m.data?.type === 'text';
export const isFormCard = (m: Message): m is Message & { data: FormCardMessageData } => m.data?.type === 'form_card';
export const isPlanCard = (m: Message): m is Message & { data: PlanCardMessageData } => m.data?.type === 'plan_card';
export const isCareerCard = (m: Message): m is Message & { data: CareerCardMessageData } => m.data?.type === 'career_card';
export const isAuditReport = (m: Message): m is Message & { data: AuditReportMessageData } => m.data?.type === 'audit_report';
export const isFileUploadPrompt = (m: Message): m is Message & { data: FileUploadPromptMessageData } => m.data?.type === 'file_upload_prompt';
export const isSystemMessage = (m: Message): m is Message & { data: SystemMessageData } => m.data?.type === 'system';
