/**
 * V10 选项 B · ChatMessage 组件 (重写)
 *
 * 关键变化:
 *  - 移除 'use client' (Vite 不需要)
 *  - Message 类型改为 @/types/message
 *  - 0 any (onSubmitForm 用 FormCardData 类型)
 */
import type { Message, FormCardMessageData, PlanCardMessageData, CareerCardMessageData, AuditReportMessageData, FileUploadPromptMessageData } from '@/types/message';
import { PlanCard } from './PlanCard';
import { CareerCard } from './CareerCard';
import { AuditReportCard } from './AuditReportCard';
import { FormCard, type FormCardData } from './FormCard';
import { FileUploadPrompt } from './FileUploadPrompt';
import { SafeMarkdown } from './shared/SafeMarkdown';

interface Props {
  message: Message;
  onSubmitForm?: (data: FormCardData) => void;
  onSavePlan?: () => void;
  onExportPlan?: () => void;
  onFixRequest?: (riskIndex: number, riskText: string) => void;
  userScore?: number;
  savedPlanId?: string;
}

export function ChatMessage({ message, onSubmitForm, onSavePlan, onExportPlan, onFixRequest, userScore, savedPlanId }: Props) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <div className="bg-gray-100 text-gray-500 text-xs px-4 py-1.5 rounded-full">{message.content}</div>
      </div>
    );
  }

  if (isUser) {
    return (
      <div className="flex justify-end mb-4 px-4">
        <div className="max-w-[85%] md:max-w-[70%] bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-sm">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  // assistant message
  const data = message.data;
  const dataType = data?.type;

  return (
    <div className="flex justify-start mb-4 px-4">
      <div className="max-w-[90%] md:max-w-[80%] flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
          AI
        </div>
        <div className="flex-1">
          {/* 默认 markdown 渲染 */}
          {message.content && (
            <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
              <SafeMarkdown content={message.content} />
            </div>
          )}

          {/* 各类型卡片 */}
          {dataType === 'form_card' && onSubmitForm && (
            <div className="mt-2">
              <FormCard onSubmit={onSubmitForm} initialData={(data as FormCardMessageData).fields as Partial<FormCardData>} />
            </div>
          )}

          {dataType === 'plan_card' && (
            <div className="mt-2">
              <PlanCard data={data as PlanCardMessageData} userScore={userScore} onSave={onSavePlan} onExport={onExportPlan} savedPlanId={savedPlanId} />
            </div>
          )}

          {dataType === 'career_card' && <CareerCard data={data as CareerCardMessageData} />}

          {dataType === 'audit_report' && (
            <AuditReportCard data={data as AuditReportMessageData} onFixRequest={onFixRequest} savedPlanId={savedPlanId} />
          )}

          {dataType === 'file_upload_prompt' && (
            <FileUploadPrompt data={data as FileUploadPromptMessageData} />
          )}
        </div>
      </div>
    </div>
  );
}