'use client';

import React, { useState } from 'react';
import { SafeMarkdown } from './shared/SafeMarkdown';

interface Major {
  name: string;
  match: number;
}

interface Props {
  content: string;
  relatedMajors: Major[];
  careerName: string;
  userScore?: number;
}

export function CareerCard({ content, relatedMajors, careerName, userScore }: Props) {
  const [showMajors, setShowMajors] = useState(false);

  const stars = (n: number) => '⭐'.repeat(n);

  return (
    <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md shadow-sm overflow-hidden">
      <div className="px-5 py-4">
        {/* 使用 SafeMarkdown 替代 dangerouslySetInnerHTML，消除 XSS 风险 */}
        <SafeMarkdown content={content} compact />
      </div>

      {!showMajors ? (
        <div className="px-5 pb-4 flex gap-2">
          <button
            onClick={() => setShowMajors(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors"
            aria-expanded={false}
          >
            📚 推荐相关专业
          </button>
          <button
            className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            title="即将支持"
          >
            ⚖️ 对比其他职业
          </button>
        </div>
      ) : (
        <div className="border-t border-gray-100 px-5 py-4">
          <h4 className="text-sm font-semibold text-gray-800 mb-3">
            {careerName}对应的主要专业：
          </h4>
          <div className="space-y-2">
            {relatedMajors.map((major, idx) => (
              <div key={idx} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                <span className="text-sm text-gray-700">{major.name}</span>
                <span className="text-xs text-yellow-500" aria-label={`匹配度 ${major.match} 星`}>{stars(major.match)}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3">
            {userScore
              ? `💡 结合你的分数（${userScore}分），广东开设这些专业的院校已经显示在你的志愿方案中。需要进一步筛选吗？`
              : '💡 广东开设这些专业的院校信息可以在志愿方案中查看。'}
          </p>
        </div>
      )}
    </div>
  );
}

// 移除旧的不安全的 formatCareerMd 函数
