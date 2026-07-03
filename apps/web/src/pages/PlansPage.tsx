/**
 * V10 选项 B · PlansPage
 * 列出所有方案 (使用 TanStack Query)
 */
import { usePlansQuery } from '@/hooks/usePlanQueries';

export function PlansPage() {
  const { data, isLoading, error } = usePlansQuery();

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <h1 className="text-lg font-bold mb-4">📋 我的方案</h1>

      {isLoading && <p className="text-sm text-gray-500">加载中...</p>}
      {error && <p className="text-sm text-red-500">加载失败: {error.message}</p>}

      <div className="space-y-3">
        {data?.plans.map((plan) => (
          <a key={plan.id} href={`/plans/${plan.id}`} className="block bg-white border border-gray-200 rounded-2xl p-4 hover:shadow-md transition-shadow">
            <h2 className="text-sm font-medium text-gray-800">{plan.name}</h2>
            <p className="text-xs text-gray-500 mt-1">创建于 {new Date(plan.createdAt).toLocaleString('zh-CN')}</p>
          </a>
        ))}

        {data?.plans.length === 0 && (
          <div className="text-center py-12 text-sm text-gray-500">
            <p>暂无方案</p>
            <p className="mt-2 text-xs">在对话中生成你的第一个方案</p>
          </div>
        )}
      </div>
    </div>
  );
}