import { useIntl } from 'react-intl';

interface SkeletonProps {
  className?: string;
  label?: string;
}

export function Skeleton({ className = '', label }: SkeletonProps) {
  const intl = useIntl();
  const resolvedLabel = label ?? intl.formatMessage({ id: 'skeleton.contentLoading' });

  return <span className={`block animate-pulse rounded-2xl bg-gray-200/80 dark:bg-gray-800 ${className}`} role="status" aria-label={resolvedLabel} />;
}

export function CardListSkeleton({ count = 3, label }: { count?: number; label?: string }) {
  const intl = useIntl();
  const resolvedLabel = label ?? intl.formatMessage({ id: 'skeleton.listLoading' });

  return (
    <div className="space-y-3" role="status" aria-label={resolvedLabel}>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <Skeleton className="h-4 w-2/5" label={intl.formatMessage({ id: 'skeleton.listItem' }, { label: resolvedLabel, index: index + 1 })} />
          <Skeleton
            className="mt-3 h-3 w-3/5"
            label={intl.formatMessage({ id: 'skeleton.listItemMeta' }, { label: resolvedLabel, index: index + 1 })}
          />
        </div>
      ))}
    </div>
  );
}
