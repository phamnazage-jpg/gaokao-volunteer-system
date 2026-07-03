import { WifiOff } from 'lucide-react';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

export function OfflineBanner() {
  const isOnline = useOnlineStatus();

  if (isOnline) {
    return null;
  }

  return (
    <div
      role="status"
      aria-label="离线状态"
      className="flex min-h-12 shrink-0 items-center justify-center gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-900"
    >
      <WifiOff className="h-4 w-4 shrink-0" aria-hidden="true" />
      <span>当前处于离线状态，写入操作将在恢复联网后自动继续。</span>
    </div>
  );
}
