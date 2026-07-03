import zhCNErrorMessages from '../../../../packages/i18n/zh-CN/errors.json';

export type ApiErrorSeverity = 'info' | 'warn' | 'error';

export interface LocalizedApiErrorMessage {
  code: string;
  message: string;
  suggestion: string;
  severity: ApiErrorSeverity;
  retryable: boolean;
}

const errorMessages = zhCNErrorMessages as Record<string, LocalizedApiErrorMessage>;

export function getLocalizedApiErrorMessage(code: string | undefined): LocalizedApiErrorMessage | undefined {
  if (code === undefined) {
    return undefined;
  }
  return errorMessages[code];
}
