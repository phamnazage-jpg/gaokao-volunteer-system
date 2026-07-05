import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '@/components/navigation/Sidebar';
import { messages } from '@/i18n/messages';

vi.mock('@/hooks/usePrefetchLazyRoute', () => ({
  usePrefetchLazyRoute: () => vi.fn(),
}));

function renderSidebar() {
  const onNewChat = vi.fn();
  const onSelectChat = vi.fn();

  render(
    <IntlProvider locale="zh-CN" messages={messages['zh-CN']} onError={() => undefined}>
      <MemoryRouter>
        <Sidebar
          recentChats={[
            { id: 'c1', title: '' },
            { id: 'c2', title: '广东物理咨询' },
          ]}
          activeChatId="c2"
          onNewChat={onNewChat}
          onSelectChat={onSelectChat}
        />
      </MemoryRouter>
    </IntlProvider>,
  );

  return { onNewChat, onSelectChat };
}

describe('Sidebar i18n shell navigation', () => {
  it('renders translated global navigation and chat actions', () => {
    const { onNewChat, onSelectChat } = renderSidebar();

    expect(screen.getByText('升学助手')).toBeInTheDocument();
    expect(screen.getByText('我的方案')).toBeInTheDocument();
    expect(screen.getByText('最近对话')).toBeInTheDocument();
    expect(screen.getByText('未命名对话')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /新建对话/ }));
    expect(onNewChat).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: '广东物理咨询' }));
    expect(onSelectChat).toHaveBeenCalledWith('c2');
  });

  it('includes dark mode variants for sidebar chrome and links', () => {
    renderSidebar();

    const links = screen.getAllByRole('link');
    const logoLink = links[0];
    const plansLink = links.find((link) => link.getAttribute('href') === '/plans');

    expect(screen.getByRole('complementary')).toHaveClass('dark:bg-gray-950', 'dark:border-gray-800');
    expect(logoLink.querySelector('span')).toHaveClass('dark:text-gray-100');
    expect(plansLink).toHaveClass('dark:text-gray-300', 'dark:hover:bg-gray-900');
    expect(screen.getByRole('button', { name: '广东物理咨询' })).toHaveClass('dark:bg-blue-950/50', 'dark:text-blue-200');
  });
});
