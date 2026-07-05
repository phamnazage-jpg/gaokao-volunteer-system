import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { Modal } from './Modal';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('Modal', () => {
  it('renders dialog with title and description when open', () => {
    renderWithProviders(
      <Modal open title="数据查询口径" description="辅助判断说明" onClose={vi.fn()}>
        口径内容
      </Modal>,
    );

    expect(screen.getByRole('dialog', { name: '数据查询口径' })).toHaveTextContent('口径内容');
    expect(screen.getByRole('button', { name: '关闭弹窗' })).toBeInTheDocument();
    expect(screen.getByText('辅助判断说明')).toBeInTheDocument();
  });

  it('renders English close label when locale is en-US', () => {
    renderWithProviders(
      <Modal open title="Data methodology" onClose={vi.fn()}>
        Content
      </Modal>,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('button', { name: 'Close dialog' })).toBeInTheDocument();
  });

  it('calls onClose when pressing Escape', async () => {
    const onClose = vi.fn();
    const { user } = renderWithProviders(
      <Modal open title="数据查询口径" onClose={onClose}>
        口径内容
      </Modal>,
    );

    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not render when closed', () => {
    renderWithProviders(
      <Modal open={false} title="数据查询口径" onClose={vi.fn()}>
        口径内容
      </Modal>,
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
  it('includes dark mode dialog surfaces', () => {
    renderWithProviders(
      <Modal open title="Data methodology" description="How data is calculated." onClose={vi.fn()}>
        Content
      </Modal>,
      { locale: 'en-US' },
    );

    expect(screen.getByRole('dialog', { name: 'Data methodology' })).toHaveClass('dark:bg-gray-900');
    expect(screen.getByRole('heading', { name: 'Data methodology' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByText('How data is calculated.')).toHaveClass('dark:text-gray-400');
    expect(screen.getByText('Content')).toHaveClass('dark:text-gray-300');
    expect(screen.getByRole('button', { name: 'Close dialog' })).toHaveClass('dark:text-gray-400', 'dark:hover:bg-gray-800');
  });
});
