'use client';

/**
 * ModeIndicator — 对话区模式指示器
 * 显示当前对话处于什么模式（探索/生成/审核）
 */

import React from 'react';

type ChatMode = 'explore' | 'generating' | 'auditing' | 'adjusting';

interface Props {
  mode: ChatMode;
  text?: string;
}

const MODE_CONFIG: Record<ChatMode, { icon: string; label: string; bgClass: string; textClass: string }> = {
  explore: {
    icon: '🔍',
    label: '自由探索',
    bgClass: 'bg-blue-50',
    textClass: 'text-blue-700',
  },
  generating: {
    icon: '📊',
    label: '方案生成中',
    bgClass: 'bg-purple-50',
    textClass: 'text-purple-700',
  },
  auditing: {
    icon: '✅',
    label: '方案审核中',
    bgClass: 'bg-orange-50',
    textClass: 'text-orange-700',
  },
  adjusting: {
    icon: '🔄',
    label: '方案调整中',
    bgClass: 'bg-green-50',
    textClass: 'text-green-700',
  },
};

export function ModeIndicator({ mode, text }: Props) {
  const config = MODE_CONFIG[mode];

  return (
    <div
      className={`${config.bgClass} ${config.textClass} px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 rounded-full`}
      role="status"
      aria-live="polite"
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>{text || config.label}</span>
    </div>
  );
}

/**
 * 根据用户画像推导当前对话模式
 */
export function deriveMode(
  userProfile: { province?: unknown; score?: unknown; subjects?: unknown },
  currentPlan: unknown,
  isAuditActive: boolean
): ChatMode {
  if (isAuditActive) return 'auditing';
  if (currentPlan) {
    // 检查是否有调整中的状态
    return 'adjusting';
  }
  if (userProfile?.province && userProfile?.score) return 'generating';
  return 'explore';
}
