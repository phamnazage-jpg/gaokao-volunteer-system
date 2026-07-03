/**
 * V10 选项 B · PlanDetailPage
 */
import { useParams } from 'react-router-dom';
import { usePlanQuery } from '@/hooks/usePlanQueries';

export function PlanDetailPage() {
  const { planId } = useParams<{ planId: string }>();
  const { data, isLoading, error } = usePlanQuery(planId ?? null);

  if (isLoading) return <div className="p-4 text-sm text-gray-500">加载中...</div>;
  if (error) return <div className="p-4 text-sm text-red-500">错误: {error.message}</div>;
  if (!data) return <div className="p-4 text-sm text-gray-500">方案不存在</div>;

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <h1 className="text-lg font-bold mb-4">{data.name}</h1>
      <div className="space-y-4">
        <section>
          <h2 className="text-sm font-semibold mb-2">🚀 冲刺 ({data.rush.length})</h2>
        </section>
        <section>
          <h2 className="text-sm font-semibold mb-2">🎯 稳妥 ({data.stable.length})</h2>
        </section>
        <section>
          <h2 className="text-sm font-semibold mb-2">🛡️ 保底 ({data.safe.length})</h2>
        </section>
      </div>
    </div>
  );
}