/**
 * V10 · HomePage chat send integration
 * Verifies page send uses the real stream mutation instead of local delayed text.
 */
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderWithProviders } from '@/test/renderWithProviders';
import type { AppLocale } from '@/i18n/messages';
import { HomePage } from './HomePage';

function streamFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
}

function renderHomePage(locale?: AppLocale) {
  return renderWithProviders(<HomePage />, locale ? { locale } : undefined);
}

describe('HomePage chat send', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('sends input through /api/chat/stream and renders streamed assistant deltas', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(streamFromChunks([
        'event: status\ndata: {"status":"thinking"}\n\n',
        'data: {"delta":"真实"}\n\n',
        'data: {"delta":"流式回复"}\n\n',
        'event: done\ndata: {"done":true}\n\n',
      ]), { headers: { 'Content-Type': 'text/event-stream' } }),
    );

    renderHomePage();
    await userEvent.type(screen.getByLabelText('输入你的问题'), '广东物理 620 分怎么报');
    await userEvent.click(screen.getByLabelText('发送消息'));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/api/chat/stream', expect.objectContaining({ method: 'POST' })));
    expect(await screen.findByText(/广东物理 620 分怎么报/)).toBeInTheDocument();
    expect(await screen.findByText(/真实流式回复/)).toBeInTheDocument();
  });

  it('renders safe copy when chat stream fails without leaking backend details', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ message: 'raw backend stack trace' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    renderHomePage('en-US');
    await userEvent.type(screen.getByLabelText('Enter your question'), 'Guangdong physics 620');
    await userEvent.click(screen.getByLabelText('Send message'));

    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to send');
    expect(screen.getAllByText('Failed to send')).toHaveLength(2);
    expect(screen.queryByText(/raw backend stack trace/i)).not.toBeInTheDocument();
  });

  it('renders desktop quick entry dropdown', async () => {
    renderHomePage();

    await userEvent.click(screen.getByRole('button', { name: /快捷入口/ }));

    expect(screen.getByRole('menu', { name: '快捷入口' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /数据查询/ })).toHaveAttribute('href', '/data-query');
  });

  it('renders desktop quick entry dropdown with English labels', async () => {
    renderHomePage('en-US');

    await userEvent.click(screen.getByRole('button', { name: /Quick entry/ }));

    expect(screen.getByRole('menu', { name: 'Quick entry' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /Data query/ })).toHaveAttribute('href', '/data-query');
  });
});
