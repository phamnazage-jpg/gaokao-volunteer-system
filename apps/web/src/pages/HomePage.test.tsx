/**
 * V10 · HomePage chat send integration
 * Verifies page send uses the real stream mutation instead of local delayed text.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
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

function renderHomePage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
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
});
