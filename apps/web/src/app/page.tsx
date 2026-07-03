'use client';

import React, { Suspense, useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useChat } from '@/lib/useChat';
import { ChatMessage } from '@/components/ChatMessage';
import { UploadBar } from '@/components/UploadBar';
import { Sidebar } from '@/components/navigation/Sidebar';
import { MobileNav } from '@/components/navigation/MobileNav';
import { ModeIndicator, deriveMode } from '@/components/navigation/ModeIndicator';
import { InfoCollectionProgress } from '@/components/shared/ProgressSteps';
import type { Message } from '@/lib/useChat';

function HomeContent() {
  const {
    messages, isTyping, sendMessage, submitForm, handleFileUpload,
    messagesEndRef, userProfile, currentPlan, currentAuditReport,
    savePlan, savedPlans, newConsultation, loadConsultation, activeRecordId,
  } = useChat();

  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const [uploadCollapsed, setUploadCollapsed] = useState(false);

  useEffect(() => {
    if (searchParams.get('new') === '1') {
      newConsultation();
      router.replace('/');
    }
  }, [searchParams, newConsultation, router]);

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    sendMessage(text);
    setInput('');
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 180) + 'px';
    }
  };

  // 动态快捷提示
  const hasCoreInfo = userProfile.province && userProfile.score && userProfile.subjects;
  const hasAnyInfo = userProfile.province || userProfile.score || userProfile.subjects;
  const quickPrompts = hasCoreInfo
    ? ['生成志愿方案', '审核我的方案', '调整方案（只看珠三角）', '了解人工智能工程师']
    : hasAnyInfo
    ? ['我是广东省的', '物理类考生', '了解一下平行志愿', '审核我的方案']
    : ['了解人工智能工程师', '平行志愿怎么录取', '广东省物理类考生', '审核我的方案'];

  // 方案保存
  const [savedPlanId, setSavedPlanId] = useState<string | null>(null);

  const handleSavePlan = () => {
    if (!currentPlan) return;
    const newPlan = savePlan(currentPlan, userProfile);
    setSavedPlanId(newPlan.id);
  };

  const handleExportPlan = () => {
    if (savedPlanId) {
      router.push(`/plans/${savedPlanId}?action=export`);
    } else if (currentPlan) {
      const newPlan = savePlan(currentPlan, userProfile);
      setSavedPlanId(newPlan.id);
      router.push(`/plans/${newPlan.id}?action=export`);
    }
  };

  // 模式推导
  const hasAuditPending = messages.some((m: Message) =>
    m.type === 'file_upload_prompt' || m.type === 'audit_report'
  );
  const chatMode = deriveMode(userProfile, currentPlan, hasAuditPending);

  return (
    <div className="app-layout">
      {/* === 桌面端侧边栏（≥1024px 可见） === */}
      <Sidebar
        recentChats={[]}
        activeChatId={activeRecordId}
        onNewChat={newConsultation}
        onSelectChat={(id) => loadConsultation(id)}
      />

      {/* === 主聊天区 === */}
      <div className="flex flex-col h-screen max-w-5xl lg:border-r border-gray-100">
        {/* 顶部导航 — 精简版 */}
        <header className="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 bg-white/95 backdrop-blur sticky top-0 z-10">
          <div className="flex items-center gap-3">
            {/* Logo — 移动端可见，桌面端隐藏 */}
            <div className="lg:hidden flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white text-sm">
                🎓
              </div>
              <h1 className="text-sm font-bold text-gray-800">升学助手</h1>
            </div>

            {/* 模式指示器 */}
            <ModeIndicator mode={chatMode} />
          </div>

          <div className="flex items-center gap-1.5">
            {/* 新建对话 — 移动端 */}
            <button
              onClick={newConsultation}
              className="lg:hidden px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="新建对话"
            >
              ✨
            </button>
            {/* 桌面端导航链接 */}
            <Link href="/consultations" className="hidden lg:inline-flex px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
              💬 咨询记录
            </Link>
            <Link href="/plans" className="hidden lg:inline-flex px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
              📋 我的方案
            </Link>
          </div>
        </header>

        {/* 进度感知条 — 信息收集阶段显示 */}
        {!hasCoreInfo && hasAnyInfo && (
          <div className="px-4 py-2 bg-blue-50/50 border-b border-blue-100">
            <InfoCollectionProgress
              province={userProfile.province}
              score={userProfile.score}
              subjects={userProfile.subjects}
            />
            <span className="ml-3 text-xs text-blue-600">
              继续对话即可自动补充信息
            </span>
          </div>
        )}

          {/* 消息区域 */}
        <div className="flex-1 overflow-y-auto py-4">
          {messages.map((msg: Message) => (
            <ChatMessage
              key={msg.id}
              message={msg}
              onSubmitForm={submitForm}
              onSavePlan={handleSavePlan}
              onExportPlan={handleExportPlan}
              onFixRequest={(riskIndex, riskText) => {
                // 一键修复：将风险项的文本作为调整请求发送
                sendMessage(`请帮我修复这个问题：${riskText.slice(0, 40)}…`);
              }}
              userScore={userProfile.score}
              savedPlanId={savedPlanId || undefined}
            />
          ))}

          {/* 打字动画 */}
          {isTyping && (
            <div className="px-4 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                  AI
                </div>
                <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm flex gap-1.5">
                  <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 提示词 */}
        <div className="px-4 py-2 flex gap-2 overflow-x-auto scrollbar-none">
          {quickPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => {
                setInput(prompt);
                inputRef.current?.focus();
              }}
              className="flex-shrink-0 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-full text-xs text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
            >
              💡 {prompt}
            </button>
          ))}
        </div>

        {/* 文件上传条 — 默认折叠，点击附件按钮展开 */}
        <UploadBar
          onUpload={handleFileUpload}
          collapsed={uploadCollapsed}
          onToggleCollapse={() => setUploadCollapsed(prev => !prev)}
        />

        {/* 输入区域 */}
        <div className="px-4 py-3 border-t border-gray-100 bg-white">
          <div className="flex items-end gap-2">
            <button
              onClick={() => setUploadCollapsed(prev => !prev)}
              className={`p-2.5 rounded-xl transition-colors flex-shrink-0 ${uploadCollapsed ? 'text-gray-400 hover:text-gray-600 hover:bg-gray-100' : 'text-blue-600 bg-blue-50'}`}
              aria-label={uploadCollapsed ? '展开文件上传' : '收起文件上传'}
              title="上传方案文件"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            </button>
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="输入你的问题... (Enter发送，Shift+Enter换行)"
              rows={1}
              aria-label="输入你的问题"
              className="flex-1 resize-none border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent max-h-[180px]"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              aria-label={input.trim() ? '发送消息' : '请先输入内容'}
              className={`p-2.5 rounded-xl flex-shrink-0 transition-all ${
                input.trim()
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          <p className="text-xs text-gray-400 text-center mt-2 hidden lg:block">
            AI辅助决策，请以官方信息为准
          </p>
        </div>

        {/* === 移动端底部导航（<1024px 可见） === */}
        <MobileNav />
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-sm text-gray-500">正在加载升学助手...</div>}>
      <HomeContent />
    </Suspense>
  );
}
