/**
 * V10 option B · apiClient.
 * Unified fetch wrapper replacing scattered fetch calls from the legacy useChat prototype.
 *
 * G1 gate:
 *  - 0 any; every response is strongly typed and validated through Zod.
 *  - Error codes map to i18n copy.
 */
import { ZodError, type ZodType, type ZodTypeDef } from 'zod';
import { getLocalizedApiErrorMessage, type ApiErrorSeverity } from './error-messages';

export interface ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;
  suggestion?: string;
  severity?: ApiErrorSeverity;
  retryable?: boolean;
}

export class HttpError extends Error implements ApiError {
  readonly status: number;
  readonly code: string | undefined;
  readonly details: unknown;
  readonly suggestion: string | undefined;
  readonly severity: ApiErrorSeverity | undefined;
  readonly retryable: boolean | undefined;

  constructor(
    message: string,
    status: number,
    code?: string,
    details?: unknown,
    options: Pick<ApiError, 'suggestion' | 'severity' | 'retryable'> = {},
  ) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.suggestion = options.suggestion;
    this.severity = options.severity;
    this.retryable = options.retryable;
  }
}

const BASE_URL = (import.meta.env['VITE_API_BASE_URL'] as string | undefined) ?? '/api';

interface RequestOptions<TBody> {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: TBody;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

function isBrowserOffline(): boolean {
  return typeof navigator !== 'undefined' && navigator.onLine === false;
}

function isWriteMethod(method: RequestOptions<unknown>['method']): boolean {
  return method !== undefined && method !== 'GET';
}

function waitUntilOnline(signal: AbortSignal | undefined): Promise<void> {
  if (!isBrowserOffline() || typeof window === 'undefined') {
    return Promise.resolve();
  }

  return new Promise<void>((resolve, reject) => {
    const cleanup = (): void => {
      window.removeEventListener('online', handleOnline);
      signal?.removeEventListener('abort', handleAbort);
    };
    const handleOnline = (): void => {
      cleanup();
      resolve();
    };
    const handleAbort = (): void => {
      cleanup();
      reject(new DOMException('The request was aborted while waiting for the network to recover.', 'AbortError'));
    };

    window.addEventListener('online', handleOnline, { once: true });
    signal?.addEventListener('abort', handleAbort, { once: true });

    if (!isBrowserOffline()) {
      handleOnline();
    } else if (signal?.aborted) {
      handleAbort();
    }
  });
}

async function request<TResponse, TBody = unknown>(
  path: string,
  schema: ZodType<TResponse, ZodTypeDef, unknown>,
  options: RequestOptions<TBody> = {},
): Promise<TResponse> {
  const { method = 'GET', body, signal, headers = {} } = options;

  const init: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...headers,
    },
    signal,
  };

  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  if (isWriteMethod(method)) {
    await waitUntilOnline(signal);
  }

  const res = await fetch(`${BASE_URL}${path}`, init);

  if (!res.ok) {
    let errorBody: { code?: string; message?: string; details?: unknown } = {};
    try {
      errorBody = (await res.json()) as { code?: string; message?: string; details?: unknown };
    } catch {
      // Response body is not JSON.
    }
    const localizedError = getLocalizedApiErrorMessage(errorBody.code);
    throw new HttpError(
      localizedError?.message ?? errorBody.message ?? `HTTP ${res.status}`,
      res.status,
      errorBody.code,
      errorBody.details,
      localizedError,
    );
  }

  const raw: unknown = await res.json();

  try {
    return schema.parse(raw);
  } catch (err) {
    if (err instanceof ZodError) {
      throw new HttpError(
        `Response schema validation failed: ${err.issues.map((i) => i.path.join('.')).join(', ')}`,
        500,
        'SCHEMA_VALIDATION_FAILED',
        err.issues,
      );
    }
    throw err;
  }
}

export const apiClient = {
  get: <T>(path: string, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'GET', signal }),
  post: <T, B = unknown>(path: string, body: B, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'POST', body, signal }),
  put: <T, B = unknown>(path: string, body: B, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'PUT', body, signal }),
  patch: <T, B = unknown>(path: string, body: B, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'PATCH', body, signal }),
  delete: <T>(path: string, schema: ZodType<T, ZodTypeDef, unknown>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'DELETE', signal }),
};
