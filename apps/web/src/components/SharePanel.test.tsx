import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { SharePanel } from './SharePanel';
import { renderWithProviders } from '@/test/renderWithProviders';
import { server } from '@/test/mocks/server';

describe('SharePanel', () => {
  it('creates a share link and renders the generated URL', async () => {
    const { user } = renderWithProviders(<SharePanel planId="p1" planTitle="测试方案" />);

    expect(screen.getByRole('region', { name: '分享面板' })).toHaveTextContent('测试方案');
    await user.click(screen.getByRole('button', { name: '创建分享链接（30天有效）' }));

    expect(await screen.findByLabelText('分享链接')).toHaveValue('https://example.test/s/ABC123');
  });

  it('creates a share link with English labels', async () => {
    const { user } = renderWithProviders(<SharePanel planId="p1" planTitle="Test plan" />, { locale: 'en-US' });

    expect(screen.getByRole('region', { name: 'Share panel' })).toHaveTextContent('Test plan');
    await user.click(screen.getByRole('button', { name: 'Create share link (valid for 30 days)' }));

    expect(await screen.findByLabelText('Share link')).toHaveValue('https://example.test/s/ABC123');
  });

  it('shows safe poster generation fallback without backend details', async () => {
    server.use(
      http.post('/api/poster/generate', () => {
        return HttpResponse.json({ message: 'raw poster stack trace' }, { status: 503 });
      }),
    );

    const { user } = renderWithProviders(<SharePanel planId="p1" planTitle="Test plan" />, { locale: 'en-US' });

    await user.click(screen.getByRole('button', { name: 'Generate share poster' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to generate the poster. Try again later.');
    expect(screen.queryByText(/raw poster stack trace/i)).not.toBeInTheDocument();
  });

  it('shows retry fallback when creation fails', async () => {
    server.use(
      http.post('/api/share-link', () => {
        return HttpResponse.json({ message: 'share service unavailable' }, { status: 503 });
      }),
    );

    const { user } = renderWithProviders(<SharePanel planId="p1" planTitle="测试方案" />);

    await user.click(screen.getByRole('button', { name: '创建分享链接（30天有效）' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('分享链接创建失败');
  });
});
