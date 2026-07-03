/**
 * V10 选项 B · ModeIndicator 组件 (4-mode 决策树)
 *
 * V10 不变量 C2: 4-mode 互斥显示, 决策延迟 < 50ms
 *
 * 决策树:
 *  - isAuditActive → auditing
 *  - currentPlan + no audit → adjusting
 *  - province + score → generating
 *  - 其他 → explore
 */

export type ChatMode = 'explore' | 'generating' | 'auditing' | 'adjusting';

interface Props {
  mode: ChatMode;
  text?: string;
}

interface ModeConfig {
  readonly icon: string;
  readonly label: string;
  readonly bgClass: string;
  readonly textClass: string;
}

const MODE_CONFIG: Record<ChatMode, ModeConfig> = {
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
      <span>{text ?? config.label}</span>
    </div>
  );
}

/**
 * 推导当前对话模式
 * 决策延迟 < 50ms (O(1) 短路求值)
 */
export function deriveMode(
  userProfile: { province?: string | undefined; score?: number | undefined; subjects?: string[] | undefined },
  currentPlan: unknown,
  isAuditActive: boolean
): ChatMode {
  if (isAuditActive) return 'auditing';
  if (currentPlan) return 'adjusting';
  if (userProfile?.province && userProfile?.score) return 'generating';
  return 'explore';
}