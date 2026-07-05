/**
 * V10 选项 B · Zustand stores 单测
 */
import { describe, it, expect } from 'vitest';
import { useChatStore, selectMessages } from '@/stores/chat';
import { useFormStore } from '@/stores/form';
import { useUIStore } from '@/stores/ui';
import { useUserStore } from '@/stores/user';

describe('useChatStore', () => {
  it('初始状态', () => {
    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.isStreaming).toBe(false);
    expect(state.streamStatus).toBe('idle');
  });

  it('appendUserMessage 添加用户消息', () => {
    const id = useChatStore.getState().appendUserMessage('hello');
    expect(id).toMatch(/^user-/);
    const messages = selectMessages(useChatStore.getState());
    expect(messages).toHaveLength(1);
    expect(messages[0]?.role).toBe('user');
    expect(messages[0]?.content).toBe('hello');
  });

  it('appendAssistantMessage 添加 assistant 消息', () => {
    const id = useChatStore.getState().appendAssistantMessage('reply');
    const messages = useChatStore.getState().messages;
    expect(messages[0]?.role).toBe('assistant');
    expect(messages[0]?.isStreaming).toBe(true);
    expect(id).toMatch(/^assistant-/);
  });

  it('updateLastMessage 更新最后一条', () => {
    useChatStore.getState().appendAssistantMessage('first');
    useChatStore.getState().updateLastMessage('updated');
    const last = useChatStore.getState().messages.at(-1);
    expect(last?.content).toBe('updated');
  });

  it('clearMessages 清空', () => {
    useChatStore.getState().appendUserMessage('test');
    useChatStore.getState().clearMessages();
    expect(useChatStore.getState().messages).toEqual([]);
  });
});

describe('useFormStore', () => {
  it('updateDraft 累加 hasAnyInfo / hasCoreInfo', () => {
    useFormStore.getState().updateDraft({ province: '广东' });
    expect(useFormStore.getState().hasAnyInfo).toBe(true);
    expect(useFormStore.getState().hasCoreInfo).toBe(false);

    useFormStore.getState().updateDraft({ score: 620 });
    expect(useFormStore.getState().hasCoreInfo).toBe(false);

    useFormStore.getState().updateDraft({ subjects: ['物理'] });
    expect(useFormStore.getState().hasCoreInfo).toBe(true);
  });
});

describe('useUIStore', () => {
  it('setTheme 改变主题', () => {
    useUIStore.getState().setTheme('dark');
    expect(useUIStore.getState().theme).toBe('dark');
  });

  it('toggleSidebar 翻转状态', () => {
    useUIStore.getState().setSidebar(false);
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(true);
  });

  it('setLocale changes the active locale', () => {
    useUIStore.getState().setLocale('en-US');
    expect(useUIStore.getState().locale).toBe('en-US');
  });
});

describe('useUserStore', () => {
  it('sets admin role for backend sessions and resets it on logout', () => {
    useUserStore.getState().setUser({
      id: 'admin-1',
      name: '管理员',
      phone: '13800138000',
      role: 'admin',
    });

    expect(useUserStore.getState()).toMatchObject({
      isLoggedIn: true,
      role: 'admin',
      phone: '13800138000',
    });

    useUserStore.getState().logout();

    expect(useUserStore.getState()).toMatchObject({
      isLoggedIn: false,
      role: 'user',
      phone: null,
    });
  });
});
