/**
 * V10 选项 B · CareerCard 组件 (重写)
 * 使用 CareerCardMessageData 类型, 0 any
 */
import { useState } from 'react';
import { SafeMarkdown } from './shared/SafeMarkdown';
import type { CareerCardMessageData } from '@/types/message';

interface Props {
  data: CareerCardMessageData;
}

const PROSPECT_STYLES: Record<'好' | '中' | '差', { color: string; bg: string; label: string }> = {
  好: { color: 'text-green-700', bg: 'bg-green-50', label: '前景好' },
  中: { color: 'text-yellow-700', bg: 'bg-yellow-50', label: '前景一般' },
  差: { color: 'text-red-700', bg: 'bg-red-50', label: '前景较差' },
};

export function CareerCard({ data }: Props) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? data.careers : data.careers.slice(0, 3);

  return (
    <div className="mt-2 bg-white border border-gray-200 rounded-2xl rounded-tl-md shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-bold text-gray-800">💼 相关职业推荐</h3>
        <p className="text-xs text-gray-500 mt-0.5">点击展开查看更多</p>
      </div>

      <div className="divide-y divide-gray-100">
        {visible.map((career, idx) => {
          const style = PROSPECT_STYLES[career.prospect];
          return (
            <div key={`${career.name}-${idx}`} className="px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-800">{career.name}</h4>
                  <SafeMarkdown content={career.description} />
                </div>
                <div className="flex flex-col items-end gap-0.5 flex-shrink-0">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${style.bg} ${style.color}`}>{style.label}</span>
                  <span className="text-xs text-gray-500">{career.salary}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {data.careers.length > 3 && (
        <div className="px-4 py-2 text-center border-t border-gray-100">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            {expanded ? '收起' : `展开剩余 ${data.careers.length - 3} 个职业`}
          </button>
        </div>
      )}
    </div>
  );
}