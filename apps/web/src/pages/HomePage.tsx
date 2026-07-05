import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FormattedMessage, useIntl } from 'react-intl';
import { ChatMessage } from '@/components/ChatMessage';
import { UploadBar } from '@/components/UploadBar';
import { ModeIndicator, deriveMode } from '@/components/navigation/ModeIndicator';
import { InfoCollectionProgress } from '@/components/shared/ProgressSteps';
import { ThemeToggle } from '@/components/shared/ThemeToggle';
import { Dropdown, type DropdownItem } from '@/components/shared/Dropdown';
import { useChatStore, selectMessages, selectIsStreaming } from '@/stores/chat';
import { useFormStore } from '@/stores/form';
import { useChatStreamMutation } from '@/hooks/useChatMutations';
import type { FormCardData } from '@/components/FormCard';
import type { Message } from '@/types/message';

export function HomePage() {
  const intl = useIntl();
  const [searchParams, setSearchParams] = useSearchParams();
  const messages = useChatStore(selectMessages);
  const isStreaming = useChatStore(selectIsStreaming);
  const lastError = useChatStore((s) => s.lastError);
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

  useEffect(() => {
    if (searchParams.get('new') === '1') {
      clearMessages();
      setActiveRecordId(null);
      setSearchParams({});
    }
  }, [searchParams, clearMessages, setActiveRecordId, setSearchParams]);

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
    appendUserMessage(
      intl.formatMessage(
        { id: 'home.formSubmittedMessage' },
        { province: data.province, score: data.score, rank: data.rank, subjects: data.subjects.join('+') },
      ),
    );
  };

  const handleFixRequest = (_riskIndex: number, riskText: string): void => {
    appendUserMessage(intl.formatMessage({ id: 'home.fixRequestMessage' }, { riskText }));
  };

  const quickPrompts = useMemo(() => {
    if (hasCoreInfo) {
      return [
        intl.formatMessage({ id: 'home.prompts.generatePlan' }),
        intl.formatMessage({ id: 'home.prompts.reviewPlan' }),
        intl.formatMessage({ id: 'home.prompts.adjustPearlRiver' }),
        intl.formatMessage({ id: 'home.prompts.aiEngineer' }),
      ];
    }
    if (hasAnyInfo) {
      return [
        intl.formatMessage({ id: 'home.prompts.provinceGuangdong' }),
        intl.formatMessage({ id: 'home.prompts.physicsCandidate' }),
        intl.formatMessage({ id: 'home.prompts.parallelApplication' }),
        intl.formatMessage({ id: 'home.prompts.reviewPlan' }),
      ];
    }
    return [
      intl.formatMessage({ id: 'home.prompts.aiEngineer' }),
      intl.formatMessage({ id: 'home.prompts.parallelAdmission' }),
      intl.formatMessage({ id: 'home.prompts.guandongPhysicsCandidate' }),
      intl.formatMessage({ id: 'home.prompts.reviewPlan' }),
    ];
  }, [hasCoreInfo, hasAnyInfo, intl]);

  const quickNavItems: DropdownItem[] = useMemo(
    () => [
      {
        href: '/consultations',
        label: intl.formatMessage({ id: 'home.quickNav.consultations.label' }),
        description: intl.formatMessage({ id: 'home.quickNav.consultations.description' }),
      },
      {
        href: '/plans',
        label: intl.formatMessage({ id: 'home.quickNav.plans.label' }),
        description: intl.formatMessage({ id: 'home.quickNav.plans.description' }),
      },
      {
        href: '/data-query',
        label: intl.formatMessage({ id: 'home.quickNav.dataQuery.label' }),
        description: intl.formatMessage({ id: 'home.quickNav.dataQuery.description' }),
      },
      {
        href: '/review',
        label: intl.formatMessage({ id: 'home.quickNav.review.label' }),
        description: intl.formatMessage({ id: 'home.quickNav.review.description' }),
      },
      {
        href: '/poster',
        label: intl.formatMessage({ id: 'home.quickNav.poster.label' }),
        description: intl.formatMessage({ id: 'home.quickNav.poster.description' }),
      },
    ],
    [intl],
  );

  const hasAuditPending = messages.some((m: Message) => m.data?.type === 'file_upload_prompt' || m.data?.type === 'audit_report');
  const chatMode = deriveMode(formDraft, null, hasAuditPending);

  return (
    <>
      <header className="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 bg-white/95 backdrop-blur sticky top-0 z-10 dark:border-gray-800 dark:bg-gray-950/95">
        <div className="flex items-center gap-3">
          <div className="lg:hidden flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white text-sm">🎓</div>
            <h1 className="text-sm font-bold text-gray-800 dark:text-gray-100">
              <FormattedMessage id="shell.appName" />
            </h1>
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
            className="lg:hidden px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
            aria-label={intl.formatMessage({ id: 'shell.newChat' })}
          >
            ✨
          </button>
          <div className="hidden lg:inline-flex">
            <Dropdown label={intl.formatMessage({ id: 'home.quickNav.label' })} items={quickNavItems} />
          </div>
        </div>
      </header>

      {!hasCoreInfo && hasAnyInfo && (
        <div className="px-4 py-2 bg-blue-50/50 border-b border-blue-100 flex items-center dark:border-blue-500/20 dark:bg-blue-500/10">
          <InfoCollectionProgress
            province={formDraft.province}
            score={formDraft.score}
            subjects={formDraft.subjects}
            labels={{
              province: intl.formatMessage({ id: 'home.progress.province' }),
              score: intl.formatMessage({ id: 'home.progress.score' }),
              subjects: intl.formatMessage({ id: 'home.progress.subjects' }),
            }}
            ariaLabel={intl.formatMessage({ id: 'home.progress.ariaLabel' })}
          />
          <span className="ml-3 text-xs text-blue-600 dark:text-blue-200">
            <FormattedMessage id="home.progress.hint" />
          </span>
        </div>
      )}

      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 && (
          <div className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>
              <FormattedMessage
                id="home.empty.greeting"
                values={{ appName: <strong key="app-name">{intl.formatMessage({ id: 'shell.appName' })}</strong> }}
              />
            </p>
            <p className="mt-2 text-xs">
              <FormattedMessage id="home.empty.tryPrompt" />
            </p>
          </div>
        )}
        {messages.map((msg: Message) => (
          <ChatMessage key={msg.id} message={msg} onSubmitForm={handleSubmitForm} onFixRequest={handleFixRequest} userScore={formDraft.score} savedPlanId={activeRecordId ?? undefined} />
        ))}

        {lastError && (
          <div className="px-4 mb-4">
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200" role="alert">
              {lastError}
            </div>
          </div>
        )}

        {isStreaming && (
          <div className="px-4 mb-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                AI
              </div>
              <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm flex gap-1.5 dark:border-gray-800 dark:bg-gray-900">
                <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot dark:bg-gray-500" />
                <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot dark:bg-gray-500" />
                <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot dark:bg-gray-500" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="px-4 py-2 flex gap-2 overflow-x-auto scrollbar-none">
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => {
              setInput(prompt);
              inputRef.current?.focus();
            }}
            className="flex-shrink-0 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-full text-xs text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
          >
            💡 {prompt}
          </button>
        ))}
      </div>

      <UploadBar
        onUpload={(_type, _file, textContent) => {
          if (textContent) appendUserMessage(textContent);
        }}
        collapsed={uploadCollapsed}
        onToggleCollapse={() => setUploadCollapsed((prev) => !prev)}
      />

      <div className="px-4 py-3 border-t border-gray-100 bg-white dark:border-gray-800 dark:bg-gray-950">
        <div className="flex items-end gap-2">
          <button
            type="button"
            onClick={() => setUploadCollapsed((prev) => !prev)}
            className={`p-2.5 rounded-xl transition-colors flex-shrink-0 ${uploadCollapsed ? 'text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-500 dark:hover:bg-gray-800 dark:hover:text-gray-300' : 'text-blue-600 bg-blue-50 dark:bg-blue-500/10 dark:text-blue-200'}`}
            aria-label={intl.formatMessage({ id: uploadCollapsed ? 'home.upload.expand' : 'home.upload.collapse' })}
            title={intl.formatMessage({ id: 'home.upload.title' })}
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
            placeholder={intl.formatMessage({ id: 'home.input.placeholder' })}
            rows={1}
            aria-label={intl.formatMessage({ id: 'home.input.ariaLabel' })}
            className="flex-1 resize-none border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent max-h-[180px] dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:placeholder:text-gray-500"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || chatStreamMutation.isPending}
            aria-label={intl.formatMessage({ id: input.trim() ? 'home.input.send' : 'home.input.requireContent' })}
            className={`p-2.5 rounded-xl flex-shrink-0 transition-all ${
              input.trim() && !chatStreamMutation.isPending ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md' : 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-500'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-400 text-center mt-2 hidden lg:block dark:text-gray-500">
          <FormattedMessage id="shell.officialInfoDisclaimer" />
        </p>
      </div>
    </>
  );
}
