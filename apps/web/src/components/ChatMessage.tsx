'use client';

import React from 'react';
import type { Message } from '@/lib/useChat';
import { PlanCard } from './PlanCard';
import { CareerCard } from './CareerCard';
import { AuditReportCard } from './AuditReportCard';
import { FormCard } from './FormCard';
import { FileUploadPrompt } from './FileUploadPrompt';
import { SafeMarkdown } from './shared/SafeMarkdown';

interface Props {
  message: Message;
  onSubmitForm?: (data: Record<string, any>) => void;
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
        <div className="bg-gray-100 text-gray-500 text-xs px-4 py-1.5 rounded-full">
          {message.content}
        </div>
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

  // Assistant messages — different types
  return (
    <div className="mb-4 px-4">
      <div className="flex items-start gap-3 max-w-[90%] md:max-w-[80%]">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-0.5">
          AI
        </div>
        <div className="flex-1">
          {message.type === 'text' && (
            <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
              <SafeMarkdown content={message.content} compact />
            </div>
          )}
          {message.type === 'form_card' && message.data && (
            <FormCard data={message.data} onSubmit={onSubmitForm!} />
          )}
          {message.type === 'plan_card' && message.data && (
            <PlanCard
              plan={message.data.plan}
              profile={message.data.profile}
              onSave={onSavePlan}
              onExport={onExportPlan}
              savedPlanId={savedPlanId}
              adjusted={message.data.adjusted}
            />
          )}
          {message.type === 'career_card' && message.data && (
            <CareerCard
              content={message.content}
              relatedMajors={message.data.relatedMajors}
              careerName={message.data.careerName}
              userScore={userScore}
            />
          )}
          {message.type === 'audit_report' && message.data && (
            <AuditReportCard
              report={message.data}
              onFixRequest={onFixRequest}
            />
          )}
          {message.type === 'file_upload_prompt' && message.data && (
            <FileUploadPrompt modes={message.data.modes} />
          )}
        </div>
      </div>
    </div>
  );
}
