'use client';

/**
 * Sidebar — 桌面端侧边栏
 * 包含：Logo、导航菜单、最近对话、主题切换
 */

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ThemeToggle } from '@/components/shared/ThemeToggle';

interface RecentChat {
  id: string;
  title: string;
}

interface Props {
  recentChats: RecentChat[];
  activeChatId?: string;
  onNewChat: () => void;
  onSelectChat: (id: string) => void;
}

export function Sidebar({ recentChats, activeChatId, onNewChat, onSelectChat }: Props) {
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: '对话', icon: '💬' },
    { href: '/plans', label: '我的方案', icon: '📋' },
    { href: '/consultations', label: '咨询记录', icon: '📖' },
    { href: '/plans/compare', label: '方案对比', icon: '⚖️' },
    { href: '/about', label: '帮助', icon: '❓' },
  ];

  return (
    <aside className="sidebar">
      {/* Logo + 新建 */}
      <div className="flex items-center justify-between mb-2">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white text-sm">
            🎓
          </div>
          <span className="text-sm font-bold text-gray-800">升学助手</span>
        </Link>
        <ThemeToggle />
      </div>

      {/* 新建对话 */}
      <button
        onClick={onNewChat}
        className="w-full py-2.5 rounded-xl bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 transition-colors flex items-center justify-center gap-1"
        style={{
          background: 'var(--brand-500)',
        }}
      >
        ✨ 新建对话
      </button>

      {/* 导航 */}
      <nav className="flex flex-col gap-0.5" aria-label="主导航">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-brand-50 text-brand-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
              style={isActive ? { backgroundColor: 'var(--brand-50)', color: 'var(--brand-700)' } : {}}
            >
              <span aria-hidden="true">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* 最近对话 */}
      {recentChats.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2 px-1">
            最近对话
          </h3>
          <div className="flex flex-col gap-0.5">
            {recentChats.slice(0, 10).map((chat) => (
              <button
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`text-left px-3 py-2 rounded-lg text-sm truncate transition-colors ${
                  chat.id === activeChatId
                    ? 'bg-brand-50 text-brand-700 font-medium'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                }`}
                style={chat.id === activeChatId ? { backgroundColor: 'var(--brand-50)', color: 'var(--brand-700)' } : {}}
              >
                {chat.title || '未命名对话'}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 底部信息 */}
      <div className="mt-auto pt-4">
        <p className="text-xs text-gray-400 text-center">
          AI辅助决策，请以官方信息为准
        </p>
      </div>
    </aside>
  );
}
