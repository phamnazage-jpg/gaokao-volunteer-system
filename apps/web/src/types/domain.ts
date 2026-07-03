/**
 * V10 选项 B · 共享类型定义
 * 替代原型 useChat.ts 中的 UserProfile (用 any 字段)
 */
import { z } from 'zod';

export const UserProfileSchema = z.object({
  province: z.string().optional(),
  score: z.number().int().min(0).max(750).optional(),
  rank: z.number().int().min(1).optional(),
  subjects: z.array(z.string()).optional(),
  preferences: z
    .object({
      region: z.array(z.string()).optional(),
      majorDirection: z.array(z.string()).optional(),
      tuition: z.string().optional(),
      careerPlan: z.string().optional(),
    })
    .optional(),
});
export type UserProfile = z.infer<typeof UserProfileSchema>;

export const SavedPlanSchema = z.object({
  id: z.string(),
  name: z.string(),
  profile: UserProfileSchema,
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
  stable: z.array(
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
  safe: z.array(
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
  createdAt: z.date(),
});
export type SavedPlan = z.infer<typeof SavedPlanSchema>;

export const ConsultationRecordSchema = z.object({
  id: z.string(),
  title: z.string(),
  messages: z.array(z.lazy(() => z.any())), // 循环引用，运行时再校验
  createdAt: z.date(),
  updatedAt: z.date(),
});
export type ConsultationRecord = z.infer<typeof ConsultationRecordSchema>;

export const AuditReportSchema = z.object({
  id: z.string(),
  planId: z.string(),
  risks: z.array(
    z.object({
      index: z.number(),
      level: z.enum(['低', '中', '高']),
      title: z.string(),
      description: z.string(),
    }),
  ),
  score: z.number(),
  createdAt: z.date(),
});
export type AuditReport = z.infer<typeof AuditReportSchema>;
