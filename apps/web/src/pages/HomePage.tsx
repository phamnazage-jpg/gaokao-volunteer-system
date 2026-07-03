/**
 * V10 选项 B · HomePage (主页 / 对话)
 *
 * 替代原型 src/app/page.tsx
 * UI/交互 1:1 复现:
 *  - L1 桌面三栏 / L2 移动单栏 + 48px Tab
 *  - C2 ModeIndicator 4-mode 决策
 *  - C3 FormCard 3-step guards (RHF 版)
 *  - B1 Typing 三态
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ChatMessage } from '@/components/ChatMessage';
import { UploadBar } from '@/components/UploadBar';
import { ModeIndicator, deriveMode } from '@/components/navigation/ModeIndicator';
import { InfoCollectionProgress } from '@/components/shared/ProgressSteps';
import { ThemeToggle } from '@/components/shared/ThemeToggle';
import { useChatStore, selectMessages, selectIsStreaming } from '@/stores/chat';
import { useFormStore } from '@/stores/form';
import { useChatStreamMutation } from '@/hooks/useChatMutations';
import type { FormCardData } from '@/components/FormCard';
import type { Message } from '@/types/message';

export function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const messages = useChatStore(selectMessages);
  const isStreaming = useChatStore(selectIsStreaming);
  const clearMessages = useChatStore((s) => s.clearMessages);
  const activeRecordId = useChatStore((s) => s.activeRecordId);
  const setActiveRecordId = useChatStore((s) => s.setActiveRecordId);
  const appendUserMessage = useChatStore((s) => s.appendUserMessage);

  const formDraft = useFormStore((s) => s.draft);
  const hasCoreInfo = useFormStore((s) => s.hasCoreInfo);
  const hasAnyInfo = useFormStore((s) => s.hasAnyInfo);
  const updateDraft = useFormStore((s) => s.updateDraft);

  const [input, setInput] = useState('');
  const [uploadCollapsed, setUploadCollapsed] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const chatStreamMutation = useChatStreamMutation();

  // 处理 ?new=1
  useEffect(() => {
    if (searchParams.get('new') === '1') {
      clearMessages();
      setActiveRecordId(null);
      setSearchParams({});
    }
  }, [searchParams, clearMessages, setActiveRecordId, setSearchParams]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  const handleSend = (): void => {
    const text = input.trim();
    if (!text || chatStreamMutation.isPending) return;
    setInput('');
    const selectedSubjects = formDraft.subjects ?? [];
    chatStreamMutation.mutate({
      message: text,
      sessionId: activeRecordId ?? undefined,
      profile: {
        province: formDraft.province || undefined,
        score: formDraft.score || undefined,
        rank: formDraft.rank || undefined,
        subjects: selectedSubjects.length > 0 ? selectedSubjects : undefined,
      },
    });
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>): void => {
    setInput(e.target.value);
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 180)}px`;
    }
  };

  const handleSubmitForm = (data: FormCardData): void => {
    updateDraft({
      province: data.province,
      score: data.score,
      rank: data.rank,
      subjects: data.subjects,
    });
    appendUserMessage(`我已填写: 省份=${data.province}, 分数=${data.score}, 位次=${data.rank}, 选科=${data.subjects.join('+')}`);
  };

  const handleFixRequest = (_riskIndex: number, riskText: string): void => {
    appendUserMessage(`请帮我修复: ${riskText}`);
  };

  const quickPrompts = useMemo(() => {
    if (hasCoreInfo) return ['生成志愿方案', '审核我的方案', '调整方案(只看珠三角)', '了解人工智能工程师'];
    if (hasAnyInfo) return ['我是广东省的', '物理类考生', '了解一下平行志愿', '审核我的方案'];
    return ['了解人工智能工程师', '平行志愿怎么录取', '广东省物理类考生', '审核我的方案'];
  }, [hasCoreInfo, hasAnyInfo]);

  const hasAuditPending = messages.some((m: Message) => m.data?.type === 'file_upload_prompt' || m.data?.type === 'audit_report');
  const chatMode = deriveMode(formDraft, null, hasAuditPending);

  return (
    <>
      <header className="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 bg-white/95 backdrop-blur sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="lg:hidden flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white text-sm">🎓</div>
            <h1 className="text-sm font-bold text-gray-800">升学助手</h1>
          </div>
          <ModeIndicator mode={chatMode} />
        </div>

        <div className="flex items-center gap-1.5">
          <div className="lg:hidden">
            <ThemeToggle />
          </div>
          <button
            type="button"
            onClick={() => {
              clearMessages();
              setActiveRecordId(null);
            }}
            className="lg:hidden px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="新建对话"
          >
            ✨
          </button>
          <Link to="/consultations" className="hidden lg:inline-flex px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            💬 咨询记录
          </Link>
          <Link to="/plans" className="hidden lg:inline-flex px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            📋 我的方案
          </Link>
        </div>
      </header>

      {/* 进度感知条 */}
      {!hasCoreInfo && hasAnyInfo && (
        <div className="px-4 py-2 bg-blue-50/50 border-b border-blue-100 flex items-center">
          <InfoCollectionProgress province={formDraft.province} score={formDraft.score} subjects={formDraft.subjects} />
          <span className="ml-3 text-xs text-blue-600">继续对话即可自动补充信息</span>
        </div>
      )}

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 && (
          <div className="px-4 py-8 text-center text-sm text-gray-500">
            <p>👋 你好！我是<strong>升学助手</strong>，你的 AI 志愿规划师 🎓</p>
            <p className="mt-2 text-xs">直接试试对我说: 「广东省物理类 620 分」～</p>
          </div>
        )}
        {messages.map((msg: Message) => (
          <ChatMessage key={msg.id} message={msg} onSubmitForm={handleSubmitForm} onFixRequest={handleFixRequest} userScore={formDraft.score} savedPlanId={activeRecordId ?? undefined} />
        ))}

        {/* 打字动画三态 (V10 不变量 B1) */}
        {isStreaming && (
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
            type="button"
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

      {/* 文件上传条 */}
      <UploadBar
        onUpload={(_type, _file, textContent) => {
          if (textContent) appendUserMessage(textContent);
        }}
        collapsed={uploadCollapsed}
        onToggleCollapse={() => setUploadCollapsed((prev) => !prev)}
      />

      {/* 输入区域 */}
      <div className="px-4 py-3 border-t border-gray-100 bg-white">
        <div className="flex items-end gap-2">
          <button
            type="button"
            onClick={() => setUploadCollapsed((prev) => !prev)}
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
            placeholder="输入你的问题... (Enter 发送, Shift+Enter 换行)"
            rows={1}
            aria-label="输入你的问题"
            className="flex-1 resize-none border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent max-h-[180px]"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || chatStreamMutation.isPending}
            aria-label={input.trim() ? '发送消息' : '请先输入内容'}
            className={`p-2.5 rounded-xl flex-shrink-0 transition-all ${
              input.trim() && !chatStreamMutation.isPending ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md' : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-400 text-center mt-2 hidden lg:block">AI 辅助决策，请以官方信息为准</p>
      </div>
    </>
  );
}