/**
 * V10 · Sprint 3 · ShareDialog 单测
 */
import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { ShareDialog } from './ShareDialog';
import { renderWithProviders } from '@/test/renderWithProviders';
import { server } from '@/test/mocks/server';

describe('ShareDialog', () => {
  it('renders nothing when closed', () => {
    renderWithProviders(<ShareDialog planId="p1" planTitle="测试方案" open={false} onClose={() => {}} />);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('opens and shows create button when open=true', () => {
    renderWithProviders(<ShareDialog planId="p1" planTitle="广东物理 620 方案" open onClose={() => {}} />);
    expect(screen.getByRole('dialog', { name: '分享方案' })).toBeInTheDocument();
    expect(screen.getByText('广东物理 620 方案')).toBeInTheDocument();
  });

  it('closes when X button clicked', async () => {
    const onClose = vi.fn();
    renderWithProviders(<ShareDialog planId="p1" planTitle="测试" open onClose={onClose} />);
    await userEvent.click(screen.getByRole('button', { name: '关闭' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('shows a retryable fallback when share-link creation fails', async () => {
    server.use(
      http.post('/api/share-link', () => {
        return HttpResponse.json({ message: 'share service unavailable' }, { status: 503 });
      }),
    );

    renderWithProviders(<ShareDialog planId="p1" planTitle="测试" open onClose={() => {}} />);

    await userEvent.click(screen.getByRole('button', { name: '创建分享链接（30天有效）' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('分享链接创建失败');
    expect(screen.getByRole('button', { name: '重试创建分享链接' })).toBeInTheDocument();
  });
});
