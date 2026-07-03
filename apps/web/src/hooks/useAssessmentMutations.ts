/**
 * V10 选项 B · useAssessmentMutations
 * 替代原型 useChat.submitForm 中的 mock 评估逻辑
 */
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { AssessmentResponseSchema, type AssessmentInput, type AssessmentResponse } from '@/lib/api-schemas';

export function useAssessmentMutation() {
  return useMutation<AssessmentResponse, Error, AssessmentInput>({
    mutationFn: (input) => apiClient.post<AssessmentResponse, AssessmentInput>('/assessment', input, AssessmentResponseSchema),
  });
}