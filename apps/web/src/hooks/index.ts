/**
 * V10 选项 B · TanStack Query 5 hooks barrel
 * 5 模块 × 3 hook = 15 个 hooks, 全部 0 any
 *
 * V10 hooks 集合: TanStack Query + 真实 API client + 流式聊天 mutation。
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

// V10 Sprint 3 模块
export { useShareLinkCreate, useShareLinkDelete, useShareLinkLatestQuery, useShareLinkStatsQuery } from './useShareLink';
export { useScoreLineQuery, useRankEstimatorQuery, useMajorsQuery, useSchoolsQuery } from './useDataQuery';
export { useReviewStartMutation, useReviewStatusQuery, useReviewActionMutation } from './useReviewFlow';
export { usePortalCWBQuery, usePortalFullPlanQuery } from './usePortal';
export { usePosterGenerateMutation } from './usePosterGenerate';
export { useLLMConfig, useAuditEnhanceMutation } from './useLLMEnhanceMutation';
