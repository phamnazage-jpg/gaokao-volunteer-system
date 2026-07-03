'use client';

import React, { useState } from 'react';

interface School {
  university: string;
  major: string;
  estScore: number;
  probability: number;
  risk: string;
  riskType: string;
  reason: string;
}

interface Props {
  plan: {
    rush: School[];
    stable: School[];
    safe: School[];
  };
  profile: Record<string, any>;
  onSave?: () => void;
  onExport?: () => void;
  savedPlanId?: string;
  adjusted?: boolean;
}

const TABS = [
  { key: 'rush', label: '冲刺', mobileLabel: '冲', color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
  { key: 'stable', label: '稳妥', mobileLabel: '稳', color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
  { key: 'safe', label: '保底', mobileLabel: '保', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
];

function getProbColor(p: number): string {
  if (p >= 80) return 'bg-green-500';
  if (p >= 50) return 'bg-blue-500';
  if (p >= 30) return 'bg-yellow-500';
  return 'bg-orange-500';
}

function getRiskBadge(risk: string) {
  if (risk === '低') return 'bg-green-100 text-green-700';
  if (risk === '中') return 'bg-yellow-100 text-yellow-700';
  return 'bg-red-100 text-red-700';
}

export function PlanCard({ plan, profile, onSave, onExport, savedPlanId, adjusted }: Props) {
  const [activeTab, setActiveTab] = useState('stable');
  const [expandedSchool, setExpandedSchool] = useState<string | null>(null);

  const currentList = plan[activeTab as keyof typeof plan];

  return (
    <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-3.5 sm:px-5 py-3 sm:py-4 border-b border-gray-100">
        <div className="flex items-center gap-1.5 sm:gap-2 mb-0.5 sm:mb-1">
          <h3 className="text-xs sm:text-sm font-semibold text-gray-800">📊 你的志愿方案</h3>
          {adjusted && (
            <span className="inline-flex items-center gap-0.5 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-medium bg-blue-100 text-blue-700 animate-pulse">
              <svg className="w-2.5 h-2.5 sm:w-3 sm:h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              <span className="hidden sm:inline">已更新</span>
            </span>
          )}
        </div>
        <p className="text-[11px] sm:text-xs text-gray-500 truncate">
          {profile.province} · {profile.subjects?.join('+')} · {profile.score}分 · 位次{profile.rank}
        </p>
      </div>

      {/* Tabs — compact on mobile, full on desktop */}
      <div className="flex border-b border-gray-100" role="tablist" aria-label="志愿方案分类">
        {TABS.map(t => (
          <button
            key={t.key}
            role="tab"
            aria-selected={activeTab === t.key}
            aria-label={`${t.label}（${plan[t.key as keyof typeof plan].length}所院校）`}
            onClick={() => { setActiveTab(t.key); setExpandedSchool(null); }}
            className={`flex-1 py-2.5 sm:py-3 text-xs sm:text-xs font-medium transition-colors relative min-h-[44px] ${
              activeTab === t.key ? t.color : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            <span className="sm:hidden">{t.mobileLabel}</span>
            <span className="hidden sm:inline">{t.label}</span>
            <span className="ml-0.5 sm:ml-1 text-[10px] sm:text-xs text-gray-400">({plan[t.key as keyof typeof plan].length})</span>
            {activeTab === t.key && (
              <div className={`absolute bottom-0 left-3 right-3 sm:left-4 sm:right-4 h-0.5 ${t.color.replace('text-', 'bg-')}`} />
            )}
          </button>
        ))}
      </div>

      {/* School List */}
      <div className="divide-y divide-gray-50">
        {currentList.map((school, idx) => (
          <div key={`${school.university}-${idx}`}>
            <div
              role="button"
              tabIndex={0}
              aria-expanded={expandedSchool === `${activeTab}-${idx}`}
              aria-label={`${school.university} ${school.major}，预估${school.estScore}分，录取概率${school.probability}%，风险${school.risk}`}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpandedSchool(expandedSchool === `${activeTab}-${idx}` ? null : `${activeTab}-${idx}`); }}}
              onClick={() => setExpandedSchool(expandedSchool === `${activeTab}-${idx}` ? null : `${activeTab}-${idx}`)}
              className="px-3.5 sm:px-5 py-2.5 sm:py-3 hover:bg-gray-50 cursor-pointer transition-colors min-h-[44px] flex items-center"
            >
              {/* Mobile: stack vertically; Desktop: row with alignment */}
              <div className="flex-1 min-w-0">
                {/* University row */}
                <div className="flex items-center gap-1 sm:gap-2">
                  <span className="text-[10px] sm:text-xs text-gray-400 w-4 sm:w-5 flex-shrink-0">{idx + 1}</span>
                  <span className="text-xs sm:text-sm font-medium text-gray-800 truncate">{school.university}</span>
                  {(school as any).adjusted && (
                    <span className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-blue-50 text-blue-600 border border-blue-200 flex-shrink-0" title="此项在本次调整中更新">
                      调整
                    </span>
                  )}
                  <span className={`text-[10px] sm:text-xs px-1 sm:px-1.5 py-0.5 rounded flex-shrink-0 ${getRiskBadge(school.risk)}`}>
                    {school.risk}风险
                  </span>
                </div>

                {/* Major + details row */}
                <div className="flex items-center justify-between mt-0.5 sm:mt-0.5 ml-6 sm:ml-7">
                  <span className="text-[10px] sm:text-xs text-gray-500 truncate max-w-[55%] sm:max-w-[70%]">{school.major}</span>
                  <div className="flex items-center gap-1 sm:gap-1.5 flex-shrink-0">
                    {/* Probability bar — compact on mobile, with screen-reader text for color-blind */}
                    <div className="w-10 sm:w-16 h-1 sm:h-1.5 bg-gray-100 rounded-full overflow-hidden" role="progressbar" aria-valuenow={school.probability} aria-valuemin={0} aria-valuemax={100} aria-label={`录取概率 ${school.probability}%`}>
                      <div
                        className={`h-full rounded-full transition-all ${getProbColor(school.probability)}`}
                        style={{ width: `${school.probability}%` }}
                      />
                    </div>
                    <span className="text-[10px] sm:text-xs text-gray-500 w-6 sm:w-8 text-right">{school.probability}%</span>
                    <span className="text-[10px] sm:text-xs font-semibold text-gray-700 w-10 sm:w-12 text-right">{school.estScore}分</span>
                  </div>
                </div>
              </div>

              {/* Expand chevron */}
              <div className="ml-1 sm:ml-2 flex-shrink-0 flex items-center justify-center w-6 h-6 sm:w-5 sm:h-5">
                <svg
                  className={`w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-300 transition-transform ${expandedSchool === `${activeTab}-${idx}` ? 'rotate-180' : ''}`}
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            {/* Expanded details */}
            {expandedSchool === `${activeTab}-${idx}` && (
              <div className="px-3.5 sm:px-5 pb-3 ml-6 sm:ml-7">
                <div className="bg-gray-50 rounded-lg p-2.5 sm:p-3 space-y-1.5 sm:space-y-2">
                  <div>
                    <span className="text-[10px] sm:text-xs font-medium text-gray-600">推荐理由：</span>
                    <span className="text-[10px] sm:text-xs text-gray-600">{school.reason}</span>
                  </div>
                  {school.riskType !== '—' && (
                    <div>
                      <span className="text-[10px] sm:text-xs font-medium text-gray-600">风险提示：</span>
                      <span className="text-[10px] sm:text-xs text-red-600">{school.riskType}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer — stacked on mobile, row on desktop */}
      <div className="px-3.5 sm:px-5 py-2.5 sm:py-3 bg-gray-50 border-t border-gray-100 flex gap-1.5 sm:gap-2">
        <button
          onClick={onSave}
          className="flex-1 py-2 sm:py-2 bg-white border border-gray-200 rounded-lg text-[11px] sm:text-xs font-medium text-gray-600 hover:bg-gray-100 transition-colors min-h-[40px]"
        >
          💾 <span className="hidden sm:inline">保存方案</span>
        </button>
        <button
          onClick={onExport}
          className="flex-1 py-2 sm:py-2 bg-white border border-gray-200 rounded-lg text-[11px] sm:text-xs font-medium text-gray-600 hover:bg-gray-100 transition-colors min-h-[40px]"
        >
          📤 <span className="hidden sm:inline">导出方案</span>
        </button>
        <button className="flex-1 py-2 sm:py-2 bg-blue-600 text-white rounded-lg text-[11px] sm:text-xs font-medium hover:bg-blue-700 transition-colors min-h-[40px]">
          🔄 <span className="hidden sm:inline">调整方案</span>
        </button>
      </div>
    </div>
  );
}
