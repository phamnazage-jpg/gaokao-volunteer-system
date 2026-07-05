import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { ShareStatusPanel } from './ShareStatusPanel';
import { renderWithProviders } from '@/test/renderWithProviders';
import type { ShareLinkResponse } from '@/hooks/useShareLink';

const latest: ShareLinkResponse = {
  id: 'ABC123',
  code: 'ABC123',
  url: 'https://example.test/s/ABC123',
  planId: 'p1',
  createdAt: '2026-07-04T00:00:00.000Z',
  expiresAt: null,
  revoked: false,
};

describe('ShareStatusPanel', () => {
  it('renders loading state without showing the empty action', () => {
    renderWithProviders(<ShareStatusPanel latest={undefined} isLoading trend={[]} onCreate={vi.fn()} />);

    expect(screen.getByRole('status')).toHaveTextContent('正在加载最新分享状态...');
    expect(screen.queryByRole('button', { name: '创建第一个分享链接' })).not.toBeInTheDocument();
  });

  it('renders latest share state', async () => {
    renderWithProviders(<ShareStatusPanel latest={latest} trend={[{ date: '07-04', views: 12 }]} onCreate={vi.fn()} />);

    const panel = screen.getByRole('region', { name: '分享状态面板' });
    expect(panel).toHaveTextContent('ABC123');
    expect(panel).toHaveTextContent('https://example.test/s/ABC123');
    expect(await screen.findByText('访问数')).toBeInTheDocument();
  });

  it('renders unavailable fallback and create action', async () => {
    const onCreate = vi.fn();
    const onRetry = vi.fn();
    const { user } = renderWithProviders(<ShareStatusPanel latest={null} isError trend={[]} onCreate={onCreate} onRetry={onRetry} />);

    expect(screen.getByRole('alert')).toHaveTextContent('分享状态暂不可用');
    await user.click(screen.getByRole('button', { name: '重试加载分享状态' }));
    await user.click(screen.getByRole('button', { name: '创建第一个分享链接' }));

    expect(onRetry).toHaveBeenCalledTimes(1);
    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  it('renders English empty state and create action', async () => {
    const onCreate = vi.fn();
    const { user } = renderWithProviders(<ShareStatusPanel latest={null} trend={[]} onCreate={onCreate} />, { locale: 'en-US' });

    expect(screen.getByText('No share links yet')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Create the first share link' }));

    expect(onCreate).toHaveBeenCalledTimes(1);
  });
});
