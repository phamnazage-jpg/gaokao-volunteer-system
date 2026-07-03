/**
 * V10 选项 B · PlanCard 组件 (3-Tab)
 *
 * V10 不变量 C1: 3-Tab 切换不重渲染父组件 (用 useState + 内部条件渲染)
 */
import { useState } from 'react';
import type { PlanCardMessageData } from '@/types/message';

type TabKey = 'rush' | 'stable' | 'safe';

interface Props {
  data: PlanCardMessageData;
  userScore?: number;
  onSave?: () => void;
  onExport?: () => void;
  savedPlanId?: string;
  adjusted?: boolean;
}

const TABS: ReadonlyArray<{ key: TabKey; label: string; mobileLabel: string; color: string; bg: string; border: string }> = [
  { key: 'rush', label: '冲刺', mobileLabel: '冲', color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
  { key: 'stable', label: '稳妥', mobileLabel: '稳', color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
  { key: 'safe', label: '保底', mobileLabel: '保', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
];

export function PlanCard({ data, userScore, onSave, onExport, savedPlanId, adjusted }: Props) {
  const [activeTab, setActiveTab] = useState<TabKey>('rush');
  const activeConfig = TABS.find((t) => t.key === activeTab);
  const items = data[activeTab];

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div>
          <h3 className="text-sm font-bold text-gray-800">
            {adjusted ? '🎯 调整后志愿方案' : '🎯 你的志愿方案'}
          </h3>
          {userScore !== undefined && (
            <p className="text-xs text-gray-500 mt-0.5">基于你的 {userScore} 分生成</p>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {savedPlanId ? (
            <span className="text-xs text-green-600">✓ 已保存</span>
          ) : onSave ? (
            <button
              onClick={onSave}
              className="px-3 py-1.5 text-xs bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
              type="button"
            >
              💾 保存
            </button>
          ) : null}
          {onExport && (
            <button
              onClick={onExport}
              className="px-3 py-1.5 text-xs bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100 transition-colors"
              type="button"
            >
              📤 导出
            </button>
          )}
        </div>
      </div>

      {/* 3-Tab 切换 */}
      <div className="flex border-b border-gray-100" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={activeTab === tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 px-3 py-2.5 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? `${tab.color} ${tab.bg} border-b-2 ${tab.border.replace('border-', 'border-b-')}`
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="hidden sm:inline">{tab.label}</span>
            <span className="sm:hidden">{tab.mobileLabel}</span>
            <span className="ml-1 text-xs">({data[tab.key].length})</span>
          </button>
        ))}
      </div>

      {/* 列表 */}
      <div className="divide-y divide-gray-100">
        {items.length === 0 ? (
          <div className="px-4 py-8 text-center text-xs text-gray-500">该分组暂无院校</div>
        ) : (
          items.map((item, idx) => (
            <div key={`${item.university}-${idx}`} className="px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-gray-800 truncate">{item.university}</span>
                    <span className="text-xs text-gray-500">·</span>
                    <span className="text-xs text-gray-600 truncate">{item.major}</span>
                  </div>
                  <p className="mt-1 text-xs text-gray-500 leading-relaxed line-clamp-2">{item.reason}</p>
                </div>
                <div className="flex flex-col items-end gap-0.5 flex-shrink-0">
                  <span className={`text-xs font-bold ${activeConfig?.color}`}>{item.probability}%</span>
                  <span className="text-xs text-gray-400">预估 {item.estScore}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}