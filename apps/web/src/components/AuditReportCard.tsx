/**
 * V10 选项 B · AuditReportCard 组件 (重写)
 * 使用 AuditReportMessageData 类型, 0 any
 */
import type { AuditReportMessageData } from '@/types/message';

interface Props {
  data: AuditReportMessageData;
  onFixRequest?: (riskIndex: number, riskText: string) => void;
  savedPlanId?: string;
}

const LEVEL_STYLES: Record<'低' | '中' | '高', { color: string; bg: string; label: string }> = {
  低: { color: 'text-green-700', bg: 'bg-green-50', label: '低风险' },
  中: { color: 'text-yellow-700', bg: 'bg-yellow-50', label: '中风险' },
  高: { color: 'text-red-700', bg: 'bg-red-50', label: '高风险' },
};

export function AuditReportCard({ data, onFixRequest, savedPlanId }: Props) {
  const scoreColor = data.score >= 80 ? 'text-green-600' : data.score >= 60 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className="mt-2 bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-100">
        <div>
          <h3 className="text-sm font-bold text-amber-800">📋 方案审核报告</h3>
          {savedPlanId && <p className="text-xs text-amber-600 mt-0.5">方案 #{savedPlanId.slice(0, 6)}</p>}
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${scoreColor}`} aria-label={`审核分数 ${data.score}`}>
            {data.score}
          </div>
          <p className="text-xs text-gray-500">/ 100</p>
        </div>
      </div>

      {/* 风险项列表 */}
      <div className="divide-y divide-gray-100">
        {data.risks.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-green-600">🎉 没有发现风险，方案看起来很稳！</div>
        ) : (
          data.risks.map((risk) => {
            const style = LEVEL_STYLES[risk.level];
            return (
              <div key={risk.index} className={`px-4 py-3 ${style.bg}`}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold ${style.color}`}>{style.label}</span>
                      <span className="text-sm font-medium text-gray-800">{risk.title}</span>
                    </div>
                    <p className="mt-1 text-xs text-gray-600 leading-relaxed">{risk.description}</p>
                  </div>
                  {onFixRequest && (
                    <button
                      type="button"
                      onClick={() => onFixRequest(risk.index, risk.title)}
                      className="flex-shrink-0 px-2.5 py-1 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      一键修复
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}