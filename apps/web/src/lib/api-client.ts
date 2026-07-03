/**
 * V10 选项 B · apiClient
 * 统一 fetch 封装 (替代原型 useChat 中的 4 处散落 fetch)
 *
 * G1 闸门:
 *  - 0 any (所有 response 强类型, 通过 zod 校验)
 *  - 错误码 → i18n 文案 (Sprint 4 完善映射, 现在先返回原始错误)
 */
import { ZodError, type ZodSchema } from 'zod';

export interface ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;
}

export class HttpError extends Error implements ApiError {
  readonly status: number;
  readonly code: string | undefined;
  readonly details: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

const BASE_URL = (import.meta.env['VITE_API_BASE_URL'] as string | undefined) ?? '/api';

interface RequestOptions<TBody> {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: TBody;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

async function request<TResponse, TBody = unknown>(
  path: string,
  schema: ZodSchema<TResponse>,
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

  const res = await fetch(`${BASE_URL}${path}`, init);

  if (!res.ok) {
    let errorBody: { code?: string; message?: string; details?: unknown } = {};
    try {
      errorBody = (await res.json()) as { code?: string; message?: string; details?: unknown };
    } catch {
      // response body 不是 JSON
    }
    throw new HttpError(
      errorBody.message ?? `HTTP ${res.status}`,
      res.status,
      errorBody.code,
      errorBody.details,
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
  get: <T>(path: string, schema: ZodSchema<T>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'GET', signal }),
  post: <T, B = unknown>(path: string, body: B, schema: ZodSchema<T>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'POST', body, signal }),
  put: <T, B = unknown>(path: string, body: B, schema: ZodSchema<T>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'PUT', body, signal }),
  patch: <T, B = unknown>(path: string, body: B, schema: ZodSchema<T>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'PATCH', body, signal }),
  delete: <T>(path: string, schema: ZodSchema<T>, signal?: AbortSignal): Promise<T> =>
    request(path, schema, { method: 'DELETE', signal }),
};
