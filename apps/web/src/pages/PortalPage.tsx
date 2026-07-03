/**
 * V10 · Sprint 3 · PortalPage
 * 招生门户入口：通过 token 访问分享的方案
 */
import { useParams } from 'react-router-dom';
import { ExternalLink, TrendingUp } from 'lucide-react';
import { usePortalCWBQuery, usePortalFullPlanQuery } from '@/hooks/usePortal';

export function PortalPage() {
  const { token = '' } = useParams<{ token: string }>();
  const cwb = usePortalCWBQuery(token);
  const fullPlan = usePortalFullPlanQuery(token);

  if (cwb.isLoading || fullPlan.isLoading) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <p className="text-sm text-gray-500">正在加载方案…</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800">招生门户</h1>
      <p className="mt-1 text-sm text-gray-500">通过分享链接查看的方案</p>

      {cwb.data && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
          <p className="text-xs text-gray-400">考生位次信息</p>
          <div className="mt-2 grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-gray-400">省份</p>
              <p className="text-sm font-semibold text-gray-800">{cwb.data.province}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">年份</p>
              <p className="text-sm font-semibold text-gray-800">{cwb.data.year}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">分数</p>
              <p className="text-sm font-semibold text-gray-800">{cwb.data.score}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">位次</p>
              <p className="text-sm font-semibold text-gray-800">{cwb.data.rank.toLocaleString()}</p>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2 text-blue-600 text-sm">
            <TrendingUp className="w-4 h-4" />
            <span>等效分数：{cwb.data.equivalentScore}</span>
          </div>
        </div>
      )}

      {fullPlan.data && (
        <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 mb-3">{fullPlan.data.plan.title}</p>
          <ul className="space-y-3">
            {fullPlan.data.plan.schools.map((s) => (
              <li key={s.id} className="border-b last:border-0 pb-3 last:pb-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-800">{s.name}</p>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      s.admissionProbability === '冲'
                        ? 'bg-red-50 text-red-600'
                        : s.admissionProbability === '稳'
                        ? 'bg-blue-50 text-blue-600'
                        : 'bg-green-50 text-green-600'
                    }`}
                  >
                    {s.admissionProbability}
                  </span>
                </div>
                <p className="mt-1 text-xs text-gray-500">专业：{s.majors.join('、')}</p>
              </li>
            ))}
          </ul>
          <a
            href="/portal/full"
            className="mt-4 inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
          >
            前往完整方案 <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      )}
    </div>
  );
}