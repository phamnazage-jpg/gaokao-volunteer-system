/**
 * V10 · chat stream reader
 * Supports SSE, NDJSON, and plain JSON fallback responses.
 */
import type { StreamStatus } from '@/stores/chat';

type StreamPayload = {
  delta?: string;
  content?: string;
  status?: StreamStatus;
  done?: boolean;
  error?: string;
};

export interface ChatStreamCallbacks {
  onDelta?: (delta: string) => void;
  onStatus?: (status: StreamStatus) => void;
}

function parsePayload(raw: string): StreamPayload | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  if (trimmed === '[DONE]') return { done: true };

  try {
    return JSON.parse(trimmed) as StreamPayload;
  } catch {
    return { delta: trimmed };
  }
}

function applyPayload(payload: StreamPayload | null, callbacks: ChatStreamCallbacks, acc: string): string {
  if (!payload || payload.done) return acc;
  if (payload.error) throw new Error(payload.error);
  if (payload.status) callbacks.onStatus?.(payload.status);

  const delta = payload.delta ?? payload.content;
  if (!delta) return acc;

  callbacks.onDelta?.(delta);
  return acc + delta;
}

function parseSseEvent(block: string): StreamPayload | null {
  const dataLines: string[] = [];
  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
  }
  if (dataLines.length === 0) return null;
  return parsePayload(dataLines.join('\n'));
}

async function readStreamBody(body: ReadableStream<Uint8Array>, callbacks: ChatStreamCallbacks): Promise<string> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let content = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split(/\r?\n\r?\n/);
    buffer = parts.pop() ?? '';

    for (const block of parts) {
      content = applyPayload(parseSseEvent(block), callbacks, content);
    }
  }

  buffer += decoder.decode();
  if (buffer.trim()) {
    if (buffer.includes('data:')) {
      content = applyPayload(parseSseEvent(buffer), callbacks, content);
    } else {
      for (const line of buffer.split(/\r?\n/).filter(Boolean)) {
        content = applyPayload(parsePayload(line), callbacks, content);
      }
    }
  }

  return content;
}

export async function readChatStream(response: Response, callbacks: ChatStreamCallbacks = {}): Promise<string> {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  const contentType = response.headers.get('Content-Type') ?? '';
  if (!response.body || contentType.includes('application/json')) {
    const raw = (await response.json()) as StreamPayload;
    const content = raw.content ?? raw.delta ?? '';
    if (content) callbacks.onDelta?.(content);
    if (raw.status) callbacks.onStatus?.(raw.status);
    return content;
  }

  return readStreamBody(response.body, callbacks);
}
