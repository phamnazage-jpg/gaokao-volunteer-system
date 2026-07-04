/**
 * V10 · Sprint 3 · ShareDialogPage
 * 分享管理页：列出所有已创建的分享链接 + 统计
 */
import { useState } from 'react';
import { Share2, BarChart3 } from 'lucide-react';
import { useShareLinkLatestQuery } from '@/hooks/useShareLink';
import { ShareDialog } from '@/components/ShareDialog';
import { StatsCard } from '@/components/StatsCard';
import { AccessTrendChart } from '@/components/AccessTrendChart';
import type { AccessDataPoint } from '@/components/AccessTrendChart';

const SAMPLE_TREND: ReadonlyArray<AccessDataPoint> = [
  { date: '07-01', views: 3 },
  { date: '07-02', views: 7 },
  { date: '07-03', views: 12 },
  { date: '07-04', views: 18 },
  { date: '07-05', views: 25 },
  { date: '07-06', views: 31 },
  { date: '07-07', views: 42 },
];

export function ShareDialogPage() {
  const [open, setOpen] = useState(false);
  const latest = useShareLinkLatestQuery();

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <Share2 className="w-6 h-6" aria-hidden="true" />
        分享管理
      </h1>
      <p className="mt-1 text-sm text-gray-500">管理你分享出去的方案链接，查看访问统计</p>

      <div className="mt-6 grid gap-4">
        {latest.data ? (
          <section
            className="grid gap-4"
            role="region"
            aria-label="分享状态面板"
          >
            <StatsCard code={latest.data.code} />
            <AccessTrendChart data={SAMPLE_TREND} />
            <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold text-gray-400 mb-2">最近链接</p>
              <div className="mb-3 inline-flex items-center rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
                {latest.data.code}
              </div>
              <p className="text-sm text-gray-800 break-all">{latest.data.url}</p>
              <p className="mt-2 text-xs text-gray-400">
                创建于 {new Date(latest.data.createdAt).toLocaleString('zh-CN', { hour12: false })}
              </p>
            </div>
          </section>
        ) : (
          <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 p-8 text-center">
            <BarChart3 className="w-12 h-12 mx-auto text-gray-300" aria-hidden="true" />
            <p className="mt-2 text-sm text-gray-500">暂无分享链接</p>
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="mt-4 inline-flex min-h-[48px] px-5 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
            >
              创建第一个分享链接
            </button>
          </div>
        )}

        <button
          type="button"
          onClick={() => setOpen(true)}
          className="w-full min-h-[48px] py-3 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700"
        >
          {latest.data ? '新建分享链接' : '创建分享链接'}
        </button>
      </div>

      <ShareDialog
        planId="plan-sample-001"
        planTitle="示例方案：广东物理 620 冲刺院校"
        open={open}
        onClose={() => setOpen(false)}
      />
    </div>
  );
}
