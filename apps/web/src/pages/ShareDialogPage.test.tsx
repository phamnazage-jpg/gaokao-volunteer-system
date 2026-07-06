/**
 * Sprint 4 T-B-40 · Share Link 状态面板
 */
import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { ShareDialogPage } from './ShareDialogPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { server } from '@/test/mocks/server';

describe('ShareDialogPage', () => {
  it('renders the latest share-link status panel with real stats', async () => {
    renderWithProviders(<ShareDialogPage />);

    const panel = await screen.findByRole('region', { name: '分享状态面板' });

    expect(within(panel).getByText('ABC123')).toBeInTheDocument();
    expect(within(panel).getByText('https://example.test/s/ABC123')).toBeInTheDocument();
    expect(await within(panel).findByText('12')).toBeInTheDocument();
    expect(within(panel).getByText('5')).toBeInTheDocument();
    expect(within(panel).getByText(/创建于/)).toBeInTheDocument();
  });

  it('renders English page and status panel labels', async () => {
    renderWithProviders(<ShareDialogPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Share management' })).toBeInTheDocument();
    const panel = await screen.findByRole('region', { name: 'Share status panel' });
    expect(within(panel).getByText('Latest link')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'New share link' })).toBeInTheDocument();
  });

  it('treats unauthenticated latest share-link status as no existing link', async () => {
    server.use(
      http.get('/api/share-link/latest', () => {
        return HttpResponse.json({ message: 'unauthenticated' }, { status: 401 });
      }),
    );

    renderWithProviders(<ShareDialogPage />);

    expect(await screen.findByText('暂无分享链接')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建第一个分享链接' })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByText('分享状态暂不可用')).not.toBeInTheDocument();
  });

  it('shows a fallback when the latest share-link status fails', async () => {
    server.use(
      http.get('/api/share-link/latest', () => {
        return HttpResponse.json({ message: 'share status unavailable' }, { status: 503 });
      }),
    );

    renderWithProviders(<ShareDialogPage />);

    expect(await screen.findByRole('alert')).toHaveTextContent('分享状态暂不可用');
    expect(screen.getByRole('button', { name: '重试加载分享状态' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建分享链接' })).toBeInTheDocument();
  });
  it('includes dark mode page header styles', () => {
    renderWithProviders(<ShareDialogPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Share management' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByText('Manage shared plan links and view access stats.')).toHaveClass('dark:text-gray-400');
  });
});
