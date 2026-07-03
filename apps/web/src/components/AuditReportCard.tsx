'use client';

import React from 'react';

interface RiskItem {
  level: 'high' | 'medium' | 'low';
  text: string;
}

interface Props {
  report: {
    overallScore: number;
    summary: string;
    riskItems: RiskItem[];
    distribution: { rush: number; stable: number; safe: number };
    goodPoints: string[];
  };
  onFixRequest?: (riskIndex: number, riskText: string) => void;
}

function ScoreStars(score: number) {
  const full = Math.floor(score);
  const empty = 5 - full;
  return (
    <span className="text-yellow-500" role="img" aria-label={`${score} out of 5 stars`}>
      {'⭐'.repeat(full)}
      {'☆'.repeat(empty)}
    </span>
  );
}

function getRiskStyle(level: string) {
  if (level === 'high') return {
    bg: 'bg-red-50',
    text: 'text-red-700',
    border: 'border-red-100',
    badge: 'text-red-700 bg-red-100',
    icon: '🔴',
    label: '高风险',
  };
  if (level === 'medium') return {
    bg: 'bg-yellow-50',
    text: 'text-yellow-700',
    border: 'border-yellow-100',
    badge: 'text-yellow-700 bg-yellow-100',
    icon: '🟡',
    label: '中风险',
  };
  return {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-100',
    badge: 'text-blue-700 bg-blue-100',
    icon: '🔵',
    label: '低风险',
  };
}

export function AuditReportCard({ report, onFixRequest }: Props) {
  const total = report.distribution.rush + report.distribution.stable + report.distribution.safe;

  return (
    <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md shadow-sm overflow-hidden">
      {/* 总体评分 */}
      <div className="px-5 py-4 border-b border-gray-100 text-center" role="region" aria-label="方案评分">
        <div className="text-lg mb-1">{ScoreStars(report.overallScore)}</div>
        <div className="text-sm font-semibold text-gray-800">总体评分 {report.overallScore}/5</div>
        <p className="text-xs text-gray-500 mt-1">{report.summary}</p>
      </div>

      {/* 风险项 — 每项附带"建议修复"按钮 */}
      <div className="px-5 py-4 border-b border-gray-100" role="region" aria-label="风险项列表">
        <h4 className="text-sm font-semibold text-gray-800 mb-3">⚠️ 风险项</h4>
        <div className="space-y-2">
          {report.riskItems.map((item, idx) => {
            const style = getRiskStyle(item.level);
            return (
              <div
                key={idx}
                className={`rounded-lg px-3 py-2.5 text-xs leading-relaxed ${style.bg} ${style.text} ${style.border} border`}
                role="alert"
              >
                <div className="flex items-start gap-2">
                  <span className="flex-shrink-0 mt-0.5" aria-hidden="true">{style.icon}</span>
                  <div className="flex-1 min-w-0">
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium mr-1.5" style={{ backgroundColor: style.text === 'text-red-700' ? '#fecaca' : style.text === 'text-yellow-700' ? '#fef08a' : '#bfdbfe', color: style.text.replace('700', '800') }}>
                      {style.label}
                    </span>
                    {item.text}
                  </div>
                </div>
                {/* 一键修复按钮 */}
                {onFixRequest && (
                  <button
                    onClick={() => onFixRequest(idx, item.text)}
                    className="mt-1.5 w-full py-1.5 rounded-md text-[11px] font-medium bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-blue-200 hover:text-blue-600 transition-colors flex items-center justify-center gap-1"
                    aria-label={`建议修复：${item.text}`}
                  >
                    🔧 建议修复此项
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 冲稳保分布 */}
      <div className="px-5 py-4 border-b border-gray-100" role="region" aria-label="冲稳保分布">
        <h4 className="text-sm font-semibold text-gray-800 mb-3">冲稳保分布</h4>
        <div className="flex h-6 rounded-lg overflow-hidden" role="img" aria-label={`冲刺 ${report.distribution.rush} 所，稳妥 ${report.distribution.stable} 所，保底 ${report.distribution.safe} 所`}>
          {report.distribution.rush > 0 && (
            <div style={{ width: `${(report.distribution.rush / total) * 100}%` }} className="bg-orange-400 flex items-center justify-center text-white text-xs font-medium">
              🚀 {report.distribution.rush}
            </div>
          )}
          {report.distribution.stable > 0 && (
            <div style={{ width: `${(report.distribution.stable / total) * 100}%` }} className="bg-blue-500 flex items-center justify-center text-white text-xs font-medium">
              ✅ {report.distribution.stable}
            </div>
          )}
          {report.distribution.safe > 0 && (
            <div style={{ width: `${(report.distribution.safe / total) * 100}%` }} className="bg-green-500 flex items-center justify-center text-white text-xs font-medium">
              🛡️ {report.distribution.safe}
            </div>
          )}
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-2">
          <span>冲刺 {report.distribution.rush}所</span>
          <span>稳妥 {report.distribution.stable}所</span>
          <span>保底 {report.distribution.safe}所</span>
        </div>
      </div>

      {/* 表现良好 */}
      <div className="px-5 py-4 border-b border-gray-100" role="region" aria-label="表现良好项">
        <h4 className="text-sm font-semibold text-gray-800 mb-2">✅ 表现良好</h4>
        <div className="space-y-1">
          {report.goodPoints.map((point, idx) => (
            <div key={idx} className="text-xs text-green-700 flex items-start gap-1.5">
              <span aria-hidden="true">✓</span>
              <span>{point}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="px-5 py-3 bg-gray-50 flex gap-2">
        <button className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors">
          🔧 优化方案
        </button>
        <button className="flex-1 py-2 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 transition-colors">
          📤 导出报告
        </button>
      </div>
    </div>
  );
}
