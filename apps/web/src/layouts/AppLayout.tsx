/**
 * V10 选项 B · AppLayout (Sidebar + Outlet + MobileNav)
 */
import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/components/navigation/Sidebar';
import { MobileNav } from '@/components/navigation/MobileNav';
import { useChatStore } from '@/stores/chat';
import { useFormStore } from '@/stores/form';
import { useUserStore } from '@/stores/user';
import { useConsultationsQuery } from '@/hooks/useConsultationQueries';

export function AppLayout() {
  const activeRecordId = useChatStore((s) => s.activeRecordId);
  const clearMessages = useChatStore((s) => s.clearMessages);
  const setActiveRecordId = useChatStore((s) => s.setActiveRecordId);
  const resetForm = useFormStore((s) => s.resetDraft);
  const userName = useUserStore((s) => s.name);
  const { data: consultationsData } = useConsultationsQuery();

  const handleNewChat = (): void => {
    clearMessages();
    resetForm();
    setActiveRecordId(null);
  };

  const handleSelectChat = (id: string): void => {
    setActiveRecordId(id);
  };

  const recentChatsList = (consultationsData?.consultations ?? [])
    .slice(0, 10)
    .map((consultation) => ({ id: consultation.id, title: consultation.title }));

  return (
    <div className="app-layout flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-fg)]">
      <Sidebar recentChats={recentChatsList} activeChatId={activeRecordId ?? undefined} onNewChat={handleNewChat} onSelectChat={handleSelectChat} />
      <div className="flex flex-col flex-1 min-w-0 max-w-5xl mx-auto lg:border-r border-gray-100">
        <Outlet />
      </div>
      {userName && (
        <aside className="hidden xl:flex w-56 shrink-0 border-l border-gray-100 bg-white/80 px-4 py-4" aria-label="用户信息">
          <div className="h-fit w-full rounded-2xl border border-gray-100 bg-white p-3 shadow-sm">
            <p className="text-xs text-gray-400">当前用户</p>
            <p className="mt-1 truncate text-sm font-medium text-gray-800">{userName}</p>
            <p className="mt-2 text-xs leading-relaxed text-gray-500">AI 辅助决策，请以官方信息为准。</p>
          </div>
        </aside>
      )}
      <MobileNav />
    </div>
  );
}
