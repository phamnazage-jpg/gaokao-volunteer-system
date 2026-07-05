/**
 * V10 option B · useAssessmentMutations.
 * Replaces mock assessment logic from the legacy useChat.submitForm prototype.
 */
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { AssessmentResponseSchema, type AssessmentInput, type AssessmentResponse } from '@/lib/api-schemas';

export function useAssessmentMutation() {
  return useMutation<AssessmentResponse, Error, AssessmentInput>({
    mutationFn: (input) => apiClient.post<AssessmentResponse, AssessmentInput>('/assessment', input, AssessmentResponseSchema),
  });
}
