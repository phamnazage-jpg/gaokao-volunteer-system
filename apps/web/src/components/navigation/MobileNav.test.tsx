import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { MemoryRouter } from 'react-router-dom';
import { MobileNav } from '@/components/navigation/MobileNav';
import { messages } from '@/i18n/messages';

describe('MobileNav i18n shell navigation', () => {
  it('renders translated bottom tabs', () => {
    render(
      <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
        <MemoryRouter>
          <MobileNav />
        </MemoryRouter>
      </IntlProvider>,
    );

    expect(screen.getByRole('navigation', { name: 'Mobile navigation' })).toBeInTheDocument();
    expect(screen.getByText('对话')).toBeInTheDocument();
    expect(screen.getByText('方案')).toBeInTheDocument();
    expect(screen.getByText('记录')).toBeInTheDocument();
  });

  it('includes dark mode variants for mobile navigation shell and tabs', () => {
    render(
      <IntlProvider locale="en-US" messages={messages['en-US']} onError={() => undefined}>
        <MemoryRouter>
          <MobileNav />
        </MemoryRouter>
      </IntlProvider>,
    );

    expect(screen.getByRole('navigation', { name: 'Mobile navigation' })).toHaveClass('dark:bg-gray-950', 'dark:border-gray-800');
    expect(screen.getByRole('link', { name: /Chat/ })).toHaveClass('dark:text-blue-300');
    expect(screen.getByRole('link', { name: /Plans/ })).toHaveClass('dark:text-gray-500', 'dark:hover:text-gray-300');
  });
});
