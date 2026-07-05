import { describe, expect, it, vi } from 'vitest';
import { fireEvent, screen } from '@testing-library/react';
import { ErrorFallback } from '@/components/shared/ErrorFallback';
import { renderWithProviders } from '@/test/renderWithProviders';

describe('ErrorFallback i18n', () => {
  it('renders localized retry and home actions', () => {
    const resetErrorBoundary = vi.fn();

    renderWithProviders(<ErrorFallback error={new Error('boom')} resetErrorBoundary={resetErrorBoundary} />);

    expect(screen.getByRole('heading', { name: '页面暂时无法显示' })).toBeInTheDocument();
    expect(screen.getByText('错误详情已隐藏，避免暴露内部信息。请重试或返回首页。')).toBeInTheDocument();
    expect(screen.queryByText('boom')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '重试' }));
    expect(resetErrorBoundary).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('link', { name: '回到首页' })).toHaveAttribute('href', '/');
  });

  it('renders English copy and safe detail fallback', () => {
    renderWithProviders(<ErrorFallback error="not-an-error" resetErrorBoundary={vi.fn()} />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Page is temporarily unavailable' })).toBeInTheDocument();
    expect(screen.getByText('Error details are hidden to avoid exposing internal information. Retry or return home.')).toBeInTheDocument();
    expect(screen.queryByText('not-an-error')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back home' })).toHaveAttribute('href', '/');
  });
});
