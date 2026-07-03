/**
 * V10 · chat stream parser
 *
 * RED first: stream parser should consume SSE/NDJSON chunks and emit incremental deltas.
 */
import { describe, expect, it } from 'vitest';
import { readChatStream } from '@/lib/chat-stream';

function streamFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

describe('readChatStream', () => {
  it('parses SSE delta/status/done events incrementally', async () => {
    const deltas: string[] = [];
    const statuses: string[] = [];

    const content = await readChatStream(
      new Response(streamFromChunks([
        'event: status\ndata: {"status":"thinking"}\n\n',
        'data: {"delta":"你好"}\n\n',
        'data: {"delta":"，同学"}\n\n',
        'event: done\ndata: {"done":true}\n\n',
      ]), { headers: { 'Content-Type': 'text/event-stream' } }),
      {
        onDelta: (delta) => deltas.push(delta),
        onStatus: (status) => statuses.push(status),
      },
    );

    expect(content).toBe('你好，同学');
    expect(deltas).toEqual(['你好', '，同学']);
    expect(statuses).toEqual(['thinking']);
  });

  it('falls back to JSON content responses for non-stream endpoints', async () => {
    const content = await readChatStream(
      new Response(JSON.stringify({ content: '完整回复' }), { headers: { 'Content-Type': 'application/json' } }),
      { onDelta: () => undefined },
    );

    expect(content).toBe('完整回复');
  });
});
