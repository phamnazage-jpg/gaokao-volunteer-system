'use client';

import React, { useState } from 'react';
import Link from 'next/link';

interface AccordionItem {
  id: string;
  title: string;
  content: React.ReactNode;
}

const accordionItems: AccordionItem[] = [
  {
    id: 'how-to-use',
    title: '如何使用升学助手？',
    content: (
      <div className="space-y-4">
        <div className="flex gap-3">
          <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold shrink-0 mt-0.5">1</div>
          <div>
            <p className="text-sm font-medium text-gray-700">输入你的基本信息</p>
            <p className="text-sm text-gray-500 mt-0.5">在对话中告诉助手你的省份、选科/文理科、高考分数（或预估分数）和全省位次，这些信息将用于精准匹配合适的院校和专业。</p>
          </div>
        </div>
        <div className="flex gap-3">
          <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold shrink-0 mt-0.5">2</div>
          <div>
            <p className="text-sm font-medium text-gray-700">提出你的需求</p>
            <p className="text-sm text-gray-500 mt-0.5">你可以询问推荐院校、专业解读、职业规划、志愿填报策略等问题。助手会根据你的分数位次和历史录取数据，给出冲刺/稳妥/保底三档建议。</p>
          </div>
        </div>
        <div className="flex gap-3">
          <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold shrink-0 mt-0.5">3</div>
          <div>
            <p className="text-sm font-medium text-gray-700">查看和保存方案</p>
            <p className="text-sm text-gray-500 mt-0.5">生成的志愿方案可以保存到「我的方案」中，支持查看详情、导出、多方案对比等功能，帮助你做出最优选择。</p>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: 'data-source',
    title: '数据来源说明',
    content: (
      <div className="space-y-3">
        <p className="text-sm text-gray-500">本助手的数据综合自以下权威来源，力求准确可靠：</p>
        <ul className="space-y-2">
          {[
            { name: '各省教育考试院', desc: '官方发布的历年录取分数线、一分一段表、招生计划等' },
            { name: '阳光高考网', desc: '教育部指定的高考信息发布平台，提供院校库、专业库查询' },
            { name: '高校官方网站', desc: '各高校招生办发布的招生章程、专业介绍、录取数据' },
            { name: '教育部学科评估', desc: '全国高校学科评估结果，反映各校学科实力排名' },
            { name: '国家统计局/人社部', desc: '行业薪资、就业率等宏观数据，辅助职业规划参考' },
          ].map((source, i) => (
            <li key={i} className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-1.5 shrink-0" />
              <div>
                <span className="text-sm font-medium text-gray-700">{source.name}</span>
                <span className="text-sm text-gray-500"> — {source.desc}</span>
              </div>
            </li>
          ))}
        </ul>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-3">
          <p className="text-xs text-yellow-800">
            数据更新时间以各来源为准，部分历史数据可能存在延迟。建议以当年官方发布的最新数据为最终参考。
          </p>
        </div>
      </div>
    ),
  },
  {
    id: 'disclaimer',
    title: '免责声明',
    content: (
      <div className="space-y-3 text-sm text-gray-500">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-red-800 mb-2">重要提示</p>
          <p className="text-sm text-red-700 leading-relaxed">
            本助手提供的所有建议和分析结果均为AI辅助生成，仅供用户参考，不构成任何正式的志愿填报指导意见。
            最终的志愿填报决策应以各省教育考试院官方发布的招生政策、录取规则和数据为准。
          </p>
        </div>
        <ul className="space-y-2 ml-1">
          <li className="flex items-start gap-2">
            <span className="text-gray-300">—</span>
            <span>升学助手不保证推荐结果的绝对准确性，录取结果受当年考生人数、试题难度、报考热度等多因素影响。</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gray-300">—</span>
            <span>用户在使用本助手前应自行核实相关数据，并咨询学校老师、招生办等专业人士的意见。</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gray-300">—</span>
            <span>本助手不承担因使用推荐结果而产生的任何直接或间接损失的责任。</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gray-300">—</span>
            <span>职业兴趣测评结果仅供参考，不代表最终职业发展建议。</span>
          </li>
        </ul>
      </div>
    ),
  },
  {
    id: 'faq',
    title: '常见问题',
    content: (
      <div className="space-y-4">
        {[
          {
            q: '升学助手适合哪些省份的考生？',
            a: '目前支持全国各省份的考生使用，覆盖新高考（3+1+2、3+3）和传统文理分科模式。系统会根据你输入的省份和选科信息自动匹配合适的推荐逻辑。',
          },
          {
            q: '推荐结果的准确性如何？',
            a: '推荐基于历年录取数据、位次法和AI分析模型综合计算。建议将推荐结果作为参考框架，结合个人兴趣、地域偏好、专业发展前景等因素综合决策。冲刺、稳妥、保底三档策略可有效降低滑档风险。',
          },
          {
            q: '如何解读"冲刺/稳妥/保底"三个档次？',
            a: '冲刺：往年录取位次略高于你的位次，有一定难度但有希望录取；稳妥：往年录取位次与你的位次相近，录取概率较高；保底：往年录取位次低于你的位次，录取把握很大。建议三个档次合理搭配。',
          },
          {
            q: '可以同时保存多个方案吗？',
            a: '可以。每次生成方案后都可以保存，所有方案会显示在「我的方案」页面中。你还可以对方案重命名、导出、对比两个方案的差异，方便在不同选择间做决策。',
          },
          {
            q: '专业推荐依据什么标准？',
            a: '专业推荐综合考虑了你的学科特长、选科组合、兴趣测评结果、就业前景和院校学科实力等因素。你也可以直接询问特定专业的详细解读，包括课程设置、就业方向、考研前景等。',
          },
          {
            q: '如何修改已保存的偏好设置？',
            a: '在对话界面中，你可以随时更新个人信息（省份、分数、位次等）和偏好设置。新的对话会基于最新的设置生成推荐结果。已有的方案不受影响。',
          },
          {
            q: '数据多久更新一次？',
            a: '录取数据通常在每年高考录取结束后由各省教育考试院发布，我们会尽快同步更新。建议在正式填报前，以当年最新发布的官方数据为准。',
          },
        ].map((faq, i) => (
          <div key={i} className="border-b border-gray-100 pb-4 last:border-0 last:pb-0">
            <p className="text-sm font-medium text-gray-700 mb-1">Q: {faq.q}</p>
            <p className="text-sm text-gray-500 leading-relaxed">{faq.a}</p>
          </div>
        ))}
      </div>
    ),
  },
];

export default function AboutPage() {
  const [openIds, setOpenIds] = useState<string[]>(['how-to-use']);

  const toggle = (id: string) => {
    setOpenIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Header */}
      <header className="flex items-center px-4 py-3 bg-white border-b border-gray-100">
        <Link href="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>返回对话</span>
        </Link>
        <h1 className="flex-1 text-center text-sm font-bold text-gray-800 -ml-8">使用帮助</h1>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="w-full max-w-2xl mx-auto space-y-3">
          {accordionItems.map((item) => {
            const isOpen = openIds.includes(item.id);
            return (
              <div
                key={item.id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
              >
                <button
                  onClick={() => toggle(item.id)}
                  className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-50 transition-colors"
                >
                  <span className="text-sm font-semibold text-gray-800">{item.title}</span>
                  <svg
                    className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
                      isOpen ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {isOpen && (
                  <div className="px-5 pb-5 pt-0">{item.content}</div>
                )}
              </div>
            );
          })}

          {/* Contact section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mt-6">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">联系我们</h3>
            <div className="space-y-2 text-sm text-gray-500">
              <p>如有任何问题或建议，欢迎通过以下方式联系我们：</p>
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span>support@zhiyuan-assistant.cn</span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                <span>400-888-6789（工作日 9:00-18:00）</span>
              </div>
            </div>
          </div>

          <p className="text-center text-xs text-gray-400 py-4">
            升学助手 v1.0.0 · AI志愿规划师
          </p>
        </div>
      </div>
    </div>
  );
}
