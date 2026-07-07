import { describe, expect, it } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { PosterPreviewPage } from './PosterPreviewPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import { server } from '@/test/mocks/server';

describe('PosterPreviewPage', () => {
  it('does not generate a poster with a sample plan id when no real plan is selected', async () => {
    const posterGeneratePayloads: Array<{ planId?: string }> = [];
    const hasPlanSelectionPrompt = (): boolean =>
      Boolean(screen.queryByRole('alert') ?? screen.queryByText(/请选择.*方案|选择.*方案|select.*plan|choose.*plan/i));

    server.use(
      http.post('/api/poster/generate', async ({ request }) => {
        posterGeneratePayloads.push((await request.json()) as { planId?: string });
        return HttpResponse.json({
          status: 'queued',
          progress: 0,
          posterUrl: null,
          qrCode: null,
          expiresAt: null,
        });
      }),
    );

    renderWithProviders(<PosterPreviewPage />);

    const generateButton = screen.getByRole('button', { name: /生成海报/ });
    if (generateButton.hasAttribute('disabled')) {
      expect(generateButton).toBeDisabled();
      expect(posterGeneratePayloads).toHaveLength(0);
      return;
    }

    await userEvent.click(generateButton);

    await waitFor(() => {
      expect(hasPlanSelectionPrompt() || posterGeneratePayloads.length > 0).toBe(true);
    });
    expect(
      hasPlanSelectionPrompt() ||
        posterGeneratePayloads.some((payload) => payload.planId !== undefined && payload.planId !== 'plan-sample-001'),
    ).toBe(true);
    expect(posterGeneratePayloads).not.toContainEqual(expect.objectContaining({ planId: 'plan-sample-001' }));
  });

  it('renders poster generation progress while async job is processing', async () => {
    server.use(
      http.post('/api/poster/generate', () => {
        return HttpResponse.json({
          jobId: 'poster-async-1',
          status: 'queued',
          progress: 5,
          posterUrl: 'https://example.test/poster-placeholder.png',
          qrCode: 'https://example.test/qr.png',
          expiresAt: '2026-08-01T00:00:00Z',
        });
      }),
      http.get('/api/poster/poster-async-1/status', () => {
        return HttpResponse.json({
          jobId: 'poster-async-1',
          status: 'processing',
          progress: 40,
          posterUrl: null,
          qrCode: null,
          expiresAt: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
    );

    renderWithProviders(<PosterPreviewPage />);

    await userEvent.click(screen.getByRole('button', { name: /生成海报/ }));

    const progress = await screen.findByRole('progressbar', { name: '海报生成进度' });
    expect(progress).toHaveAttribute('aria-valuenow', '40');
    expect(screen.getByText('生成中')).toBeInTheDocument();
    expect(screen.queryByAltText('海报预览')).not.toBeInTheDocument();
  });

  it('renders preview actions after async job completes', async () => {
    server.use(
      http.post('/api/poster/generate', () => {
        return HttpResponse.json({
          jobId: 'poster-async-2',
          status: 'queued',
          progress: 0,
          posterUrl: null,
          qrCode: null,
          expiresAt: null,
        });
      }),
      http.get('/api/poster/poster-async-2/status', () => {
        return HttpResponse.json({
          jobId: 'poster-async-2',
          status: 'completed',
          progress: 100,
          posterUrl: 'https://example.test/poster-completed.png',
          qrCode: 'https://example.test/qr-completed.png',
          expiresAt: '2026-08-01T00:00:00Z',
          updatedAt: '2026-07-04T00:00:02.000Z',
        });
      }),
    );

    renderWithProviders(<PosterPreviewPage />);

    await userEvent.click(screen.getByRole('button', { name: /生成海报/ }));

    expect(await screen.findByAltText('海报预览')).toHaveAttribute(
      'src',
      'https://example.test/poster-completed.png',
    );
    expect(screen.getByRole('link', { name: /下载/ })).toHaveAttribute(
      'href',
      'https://example.test/poster-completed.png',
    );
    expect(screen.getByRole('button', { name: '复制二维码' })).toBeEnabled();
  });

  it('renders poster page and generation flow with English labels', async () => {
    server.use(
      http.post('/api/poster/generate', () => {
        return HttpResponse.json({
          jobId: 'poster-async-en',
          status: 'queued',
          progress: 5,
          posterUrl: 'https://example.test/poster-placeholder.png',
          qrCode: 'https://example.test/qr.png',
          expiresAt: '2026-08-01T00:00:00Z',
        });
      }),
      http.get('/api/poster/poster-async-en/status', () => {
        return HttpResponse.json({
          jobId: 'poster-async-en',
          status: 'processing',
          progress: 40,
          posterUrl: null,
          qrCode: null,
          expiresAt: null,
          updatedAt: '2026-07-04T00:00:00.000Z',
        });
      }),
    );

    renderWithProviders(<PosterPreviewPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Poster generator' })).toBeInTheDocument();
    expect(screen.getByText('Choose a template and generate a share poster for your plan.')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /Generate poster/ }));

    const progress = await screen.findByRole('progressbar', { name: 'Poster generation progress' });
    expect(progress).toHaveAttribute('aria-valuenow', '40');
    expect(screen.getByText('Generating')).toBeInTheDocument();
  });

  it('shows a safe failure message when poster generation request fails', async () => {
    server.use(
      http.post('/api/poster/generate', () => {
        return HttpResponse.json({ message: 'raw poster backend failure' }, { status: 503 });
      }),
    );

    renderWithProviders(<PosterPreviewPage />);

    await userEvent.click(screen.getByRole('button', { name: /生成海报/ }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('海报生成失败，请稍后重试。');
    expect(screen.queryByText('raw poster backend failure')).not.toBeInTheDocument();
  });
  it('includes dark mode page header styles', () => {
    renderWithProviders(<PosterPreviewPage />, { locale: 'en-US' });

    expect(screen.getByRole('heading', { name: 'Poster generator' })).toHaveClass('dark:text-gray-100');
    expect(screen.getByText('Choose a template and generate a share poster for your plan.')).toHaveClass('dark:text-gray-400');
  });
});
