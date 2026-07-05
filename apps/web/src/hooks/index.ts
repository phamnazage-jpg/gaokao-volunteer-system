/**
 * V10 option B · TanStack Query 5 hooks barrel.
 * 5 modules × 3 hooks = 15 hooks, all 0 any.
 *
 * V10 hooks collection: TanStack Query + real API client + streaming chat mutation.
 */
export { useChatSendMutation, useChatStreamMutation } from './useChatMutations';
export { useChatHistoryQuery, useConsultationsQuery } from './useChatQueries';

export { useChatOrchestrator } from './useChatOrchestrator';
export { useScrollRecovery } from './useScrollRecovery';

export { useConsultationsQuery as _useConsultationsQuery, useConsultationQuery } from './useConsultationQueries';
export { useConsultationCreateMutation, useConsultationUpdateMutation, useConsultationDeleteMutation } from './useConsultationMutations';

export { usePlansQuery, usePlanQuery } from './usePlanQueries';
export { usePlanCreateMutation, usePlanUpdateMutation, usePlanDeleteMutation } from './usePlanMutations';

export { useAssessmentMutation } from './useAssessmentMutations';

export { useAuditSubmitMutation, useAuditStatusQuery } from './useAuditMutations';

export { useUploadMutation } from './useUploadMutations';

// V10 Sprint 3 modules.
export { useShareLinkCreate, useShareLinkDelete, useShareLinkLatestQuery, useShareLinkStatsQuery } from './useShareLink';
export { useScoreLineQuery, useRankEstimatorQuery, useMajorsQuery, useSchoolsQuery } from './useDataQuery';
export { useReviewStartMutation, useReviewStatusQuery, useReviewActionMutation } from './useReviewFlow';
export { usePortalCWBQuery, usePortalFullPlanQuery } from './usePortal';
export { usePosterGenerateMutation, usePosterStatusQuery } from './usePosterGenerate';
export { useLLMConfig, useAuditEnhanceMutation, useAuditEnhanceStatusQuery } from './useLLMEnhanceMutation';
export { useAdminOrdersQuery } from './useAdminOrders';
export { useAdminCasesQuery, useAdminCaseQuery } from './useAdminCases';
export { useAdminShareLinkDetailQuery, useAdminShareLinksQuery } from './useAdminShareLinks';
export { useAdminPostersQuery } from './useAdminPosters';
