/**
 * V10 option B: mobile bottom-tab navigation.
 */
import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { FormattedMessage } from 'react-intl';

interface Tab {
  readonly to: string;
  readonly labelId: string;
  readonly icon: ReactNode;
}

const TABS: ReadonlyArray<Tab> = [
  {
    to: '/',
    labelId: 'shell.nav.chat',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
  },
  {
    to: '/plans',
    labelId: 'shell.mobileNav.plans',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    to: '/consultations',
    labelId: 'shell.mobileNav.records',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

export function MobileNav() {
  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around bg-white border-t border-gray-200 shadow-[0_-2px_8px_rgba(0,0,0,0.04)] dark:border-gray-800 dark:bg-gray-950"
      aria-label="Mobile navigation"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
    >
      {TABS.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          end={tab.to === '/'}
          className={({ isActive }) =>
            `flex flex-col items-center gap-0.5 py-2 px-4 text-xs transition-colors min-w-[64px] min-h-[48px] justify-center ${
              isActive ? 'text-blue-600 font-medium dark:text-blue-300' : 'text-gray-400 dark:text-gray-500 dark:hover:text-gray-300'
            }`
          }
        >
          {tab.icon}
          <span>
            <FormattedMessage id={tab.labelId} />
          </span>
        </NavLink>
      ))}
    </nav>
  );
}
