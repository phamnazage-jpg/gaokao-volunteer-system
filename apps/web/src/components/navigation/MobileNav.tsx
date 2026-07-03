'use client';

/**
 * MobileNav — 移动端底部 Tab 导航
 * 3 个核心入口：对话、方案、探索
 */

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function MobileNav() {
  const pathname = usePathname();

  const tabs = [
    {
      href: '/',
      label: '对话',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      ),
    },
    {
      href: '/plans',
      label: '方案',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      href: '/consultations',
      label: '记录',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ];

  return (
    <nav
      className="lg:hidden flex items-center justify-around bg-white border-t border-gray-200 pb-safe"
      aria-label="移动端导航"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
    >
      {tabs.map((tab) => {
        const isActive = tab.href === '/'
          ? pathname === '/'
          : pathname.startsWith(tab.href);

        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`flex flex-col items-center gap-0.5 py-2 px-4 text-xs transition-colors min-w-[64px] min-h-[48px] justify-center ${
              isActive
                ? 'text-brand-600 font-medium'
                : 'text-gray-400'
            }`}
            style={isActive ? { color: 'var(--brand-600)' } : {}}
            aria-current={isActive ? 'page' : undefined}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
