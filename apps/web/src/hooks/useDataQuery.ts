/**
 * V10 · Sprint 3 · Data Query API hooks
 */
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { apiClient } from '@/lib/api-client';

export const ScoreLineResponseSchema = z.object({
  province: z.string(),
  year: z.number().int(),
  scoreType: z.enum(['physics', 'history']),
  lines: z.array(
    z.object({
      batch: z.string(),
      score: z.number(),
      rank: z.number().int(),
    }),
  ),
});

export const RankEstimatorResponseSchema = z.object({
  province: z.string(),
  year: z.number().int(),
  scoreType: z.enum(['physics', 'history']),
  rank: z.number().int(),
  equivalentScore: z.number(),
});

export const MajorsResponseSchema = z.object({
  majors: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      category: z.string(),
    }),
  ),
  total: z.number().int(),
});

export const SchoolsResponseSchema = z.object({
  schools: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      province: z.string(),
      is985: z.boolean(),
      is211: z.boolean(),
    }),
  ),
  total: z.number().int(),
});

export type ScoreLineResponse = z.infer<typeof ScoreLineResponseSchema>;
export type RankEstimatorResponse = z.infer<typeof RankEstimatorResponseSchema>;
export type MajorsResponse = z.infer<typeof MajorsResponseSchema>;
export type SchoolsResponse = z.infer<typeof SchoolsResponseSchema>;

export const dataQueryKeys = {
  all: ['data-query'] as const,
  scoreLine: (params: { province: string; year: number; scoreType: 'physics' | 'history' }) =>
    [...dataQueryKeys.all, 'score-line', params] as const,
  rankEstimator: (params: { province: string; year: number; scoreType: 'physics' | 'history'; rank: number }) =>
    [...dataQueryKeys.all, 'rank-estimator', params] as const,
  majors: (keyword?: string) => [...dataQueryKeys.all, 'majors', keyword ?? ''] as const,
  schools: (keyword?: string) => [...dataQueryKeys.all, 'schools', keyword ?? ''] as const,
};

export function useScoreLineQuery(params: { province: string; year: number; scoreType: 'physics' | 'history' } | null) {
  return useQuery<ScoreLineResponse>({
    queryKey: params ? dataQueryKeys.scoreLine(params) : ['data-query', 'score-line', 'noop'],
    queryFn: () =>
      apiClient.get<ScoreLineResponse>(
        `/data-query/score-line?province=${encodeURIComponent(params!.province)}&year=${params!.year}&scoreType=${params!.scoreType}`,
        ScoreLineResponseSchema,
      ),
    enabled: Boolean(params),
    staleTime: 10 * 60 * 1000,
  });
}

export function useRankEstimatorQuery(
  params: { province: string; year: number; scoreType: 'physics' | 'history'; rank: number } | null,
) {
  return useQuery<RankEstimatorResponse>({
    queryKey: params ? dataQueryKeys.rankEstimator(params) : ['data-query', 'rank-estimator', 'noop'],
    queryFn: () =>
      apiClient.get<RankEstimatorResponse>(
        `/data-query/rank-estimator?province=${encodeURIComponent(params!.province)}&year=${params!.year}&scoreType=${params!.scoreType}&rank=${params!.rank}`,
        RankEstimatorResponseSchema,
      ),
    enabled: Boolean(params),
    select: (data) => ({
      ...data,
      equivalentScore: Math.round(data.equivalentScore),
    }),
  });
}

export function useMajorsQuery(keyword?: string) {
  return useQuery<MajorsResponse>({
    queryKey: dataQueryKeys.majors(keyword),
    queryFn: () => {
      const q = keyword ? `?keyword=${encodeURIComponent(keyword)}` : '';
      return apiClient.get<MajorsResponse>(`/data-query/majors${q}`, MajorsResponseSchema);
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useSchoolsQuery(keyword?: string) {
  return useQuery<SchoolsResponse>({
    queryKey: dataQueryKeys.schools(keyword),
    queryFn: () => {
      const q = keyword ? `?keyword=${encodeURIComponent(keyword)}` : '';
      return apiClient.get<SchoolsResponse>(`/data-query/schools${q}`, SchoolsResponseSchema);
    },
    staleTime: 5 * 60 * 1000,
  });
}