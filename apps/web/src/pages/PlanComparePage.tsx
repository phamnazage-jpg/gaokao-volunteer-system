/**
 * V10 选项 B · PlanComparePage
 * 保留原型“方案对比”入口，后续 Sprint 接真实方案选择与对比表。
 */
import { Link } from 'react-router-dom';
import { usePlansQuery } from '@/hooks/usePlanQueries';

export function PlanComparePage() {
  const { data, isLoading, error } = usePlansQuery();
  const plans = data?.plans ?? [];

  return (
    <main className="flex-1 overflow-y-auto px-4 py-6 pb-20 lg:pb-6">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-gray-900">⚖️ 方案对比</h1>
          <p className="mt-1 text-xs text-gray-500">对比冲稳保结构、风险项和专业覆盖度。</p>
        </div>
        <Link to="/plans" className="rounded-xl border border-gray-200 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50">
          我的方案
        </Link>
      </div>

      {isLoading && <p className="text-sm text-gray-500">加载中...</p>}
      {error && <p className="text-sm text-red-500">加载失败: {error.message}</p>}

      {!isLoading && !error && plans.length === 0 && (
        <section className="rounded-3xl border border-dashed border-gray-300 bg-white p-8 text-center">
          <div className="text-4xl" aria-hidden="true">📋</div>
          <h2 className="mt-3 text-sm font-semibold text-gray-900">还没有可对比的方案</h2>
          <p className="mt-2 text-xs text-gray-500">先在对话中生成或保存方案，再回到这里做横向对比。</p>
          <Link to="/" className="mt-5 inline-flex rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            去生成方案
          </Link>
        </section>
      )}

      {plans.length > 0 && (
        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500">
              <tr>
                <th className="px-4 py-3 font-medium">方案</th>
                <th className="px-4 py-3 font-medium">冲刺</th>
                <th className="px-4 py-3 font-medium">稳妥</th>
                <th className="px-4 py-3 font-medium">保底</th>
              </tr>
            </thead>
            <tbody>
              {plans.map((plan) => (
                <tr key={plan.id} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-medium text-gray-900">{plan.name}</td>
                  <td className="px-4 py-3 text-gray-600">{plan.rush.length}</td>
                  <td className="px-4 py-3 text-gray-600">{plan.stable.length}</td>
                  <td className="px-4 py-3 text-gray-600">{plan.safe.length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
