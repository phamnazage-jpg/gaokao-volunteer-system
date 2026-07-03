/**
 * V10 · Sprint 3 · chat fixtures
 *
 * 3 套高考场景 mock，用于 chat 编排器 + Review Panel 集成测试
 */
import type { Message } from '@/types/message';

export interface ChatFixture {
  readonly id: string;
  readonly title: string;
  readonly province: string;
  readonly subjects: 'physics' | 'history';
  readonly score: number;
  readonly messages: ReadonlyArray<Message>;
  readonly draft: {
    readonly province: string;
    readonly subjects: 'physics' | 'history';
    readonly score: number;
    readonly rank: number;
    readonly preferences: ReadonlyArray<string>;
  };
}

export const CHAT_FIXTURES: ReadonlyArray<ChatFixture> = [
  {
    id: 'fixture-gd-physics-620',
    title: '广东物理 620 分方案咨询',
    province: '广东',
    subjects: 'physics',
    score: 620,
    messages: [
      {
        id: 'm1',
        role: 'user',
        content: '我是广东理科生，高考 620 分，想学计算机相关专业，能帮我推荐一些学校吗？',
        timestamp: new Date('2026-07-03T09:00:00.000Z'),
      },
      {
        id: 'm2',
        role: 'assistant',
        content: '根据您的情况，我为您推荐以下几所院校……',
        timestamp: new Date('2026-07-03T09:00:02.000Z'),
      },
    ],
    draft: {
      province: '广东',
      subjects: 'physics',
      score: 620,
      rank: 12500,
      preferences: ['计算机', '人工智能'],
    },
  },
  {
    id: 'fixture-gd-history-580',
    title: '广东历史 580 分方案咨询',
    province: '广东',
    subjects: 'history',
    score: 580,
    messages: [
      {
        id: 'm1',
        role: 'user',
        content: '广东历史类 580 分，倾向财经类专业，请帮忙做志愿规划。',
        timestamp: new Date('2026-07-03T10:30:00.000Z'),
      },
    ],
    draft: {
      province: '广东',
      subjects: 'history',
      score: 580,
      rank: 8400,
      preferences: ['财经', '金融'],
    },
  },
  {
    id: 'fixture-hb-physics-600',
    title: '河北物理 600 分方案咨询',
    province: '河北',
    subjects: 'physics',
    score: 600,
    messages: [
      {
        id: 'm1',
        role: 'user',
        content: '河北物理 600 分，985 边缘冲一下，能给点建议吗？',
        timestamp: new Date('2026-07-03T11:15:00.000Z'),
      },
    ],
    draft: {
      province: '河北',
      subjects: 'physics',
      score: 600,
      rank: 22000,
      preferences: ['工科', '电气'],
    },
  },
];