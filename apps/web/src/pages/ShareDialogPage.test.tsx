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
    expect(within(panel).getByText(/2026\/7\/3/)).toBeInTheDocument();
  });

  it('shows a fallback when the latest share-link status fails', async () => {
    server.use(
      http.get('/api/share-link/latest', () => {
        return HttpResponse.json({ message: 'share status unavailable' }, { status: 503 });
      }),
    );

    renderWithProviders(<ShareDialogPage />);

    expect(await screen.findByRole('alert')).toHaveTextContent('分享状态暂不可用');
    expect(screen.getByRole('button', { name: '创建分享链接' })).toBeInTheDocument();
  });
});
