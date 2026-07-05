/**
 * V10 option B: four-mode chat status indicator.
 */

import { FormattedMessage } from 'react-intl';

export type ChatMode = 'explore' | 'generating' | 'auditing' | 'adjusting';

interface Props {
  mode: ChatMode;
  text?: string;
}

interface ModeConfig {
  readonly icon: string;
  readonly labelId: string;
  readonly bgClass: string;
  readonly textClass: string;
}

const MODE_CONFIG: Record<ChatMode, ModeConfig> = {
  explore: {
    icon: '🔍',
    labelId: 'shell.mode.explore',
    bgClass: 'bg-blue-50',
    textClass: 'text-blue-700',
  },
  generating: {
    icon: '📊',
    labelId: 'shell.mode.generating',
    bgClass: 'bg-purple-50',
    textClass: 'text-purple-700',
  },
  auditing: {
    icon: '✅',
    labelId: 'shell.mode.auditing',
    bgClass: 'bg-orange-50',
    textClass: 'text-orange-700',
  },
  adjusting: {
    icon: '🔄',
    labelId: 'shell.mode.adjusting',
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
      <span>{text ?? <FormattedMessage id={config.labelId} />}</span>
    </div>
  );
}

/**
 * Derives the active chat mode with O(1) short-circuit checks.
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
