import { act, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { toast, Toaster } from './Toast';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders emitted toast messages', () => {
    renderWithProviders(<Toaster />);

    act(() => {
      toast.success('保存成功', { description: '资料已更新。' });
    });

    expect(screen.getByRole('status')).toHaveTextContent('保存成功');
    expect(screen.getByText('资料已更新。')).toBeInTheDocument();
  });

  it('renders toaster chrome with English labels', () => {
    renderWithProviders(<Toaster />, { locale: 'en-US' });

    act(() => {
      toast.error('Save failed', { description: 'Try again later.' });
    });

    expect(screen.getByLabelText('Notifications')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Save failed');
    expect(screen.getByText('Try again later.')).toBeInTheDocument();
  });

  it('auto dismisses messages after duration', () => {
    renderWithProviders(<Toaster />);

    act(() => {
      toast.info('科类已切换', { durationMs: 100 });
    });
    expect(screen.getByRole('status')).toHaveTextContent('科类已切换');

    act(() => {
      vi.advanceTimersByTime(101);
    });

    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
  it('includes dark mode toast variants', () => {
    renderWithProviders(<Toaster />, { locale: 'en-US' });

    act(() => {
      toast.info('Sync queued');
    });

    expect(screen.getByRole('status')).toHaveClass('dark:border-blue-500/30', 'dark:bg-blue-500/10', 'dark:text-blue-100');
  });
});
