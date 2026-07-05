import { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';

type ToastVariant = 'success' | 'error' | 'info';

interface ToastOptions {
  description?: string;
  durationMs?: number;
}

interface ToastMessage extends ToastOptions {
  id: string;
  title: string;
  variant: ToastVariant;
}

const TOAST_EVENT = 'gaokao:toast';
const DEFAULT_DURATION_MS = 3200;

function createToast(variant: ToastVariant, title: string, options: ToastOptions = {}): void {
  if (typeof window === 'undefined') return;

  const message: ToastMessage = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    title,
    variant,
    ...options,
  };

  window.dispatchEvent(new CustomEvent<ToastMessage>(TOAST_EVENT, { detail: message }));
}

export const toast = {
  success: (title: string, options?: ToastOptions) => createToast('success', title, options),
  error: (title: string, options?: ToastOptions) => createToast('error', title, options),
  info: (title: string, options?: ToastOptions) => createToast('info', title, options),
};

const variantClass: Record<ToastVariant, string> = {
  success: 'border-green-200 bg-green-50 text-green-900 dark:border-green-500/30 dark:bg-green-500/10 dark:text-green-100',
  error: 'border-red-200 bg-red-50 text-red-900 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-100',
  info: 'border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-100',
};

const variantLabelKey: Record<ToastVariant, string> = {
  success: 'toast.variant.success',
  error: 'toast.variant.error',
  info: 'toast.variant.info',
};

export function Toaster() {
  const intl = useIntl();
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const handleToast = (event: Event): void => {
      const message = (event as CustomEvent<ToastMessage>).detail;
      setMessages((current) => [...current, message].slice(-3));

      window.setTimeout(() => {
        setMessages((current) => current.filter((item) => item.id !== message.id));
      }, message.durationMs ?? DEFAULT_DURATION_MS);
    };

    window.addEventListener(TOAST_EVENT, handleToast);
    return () => window.removeEventListener(TOAST_EVENT, handleToast);
  }, []);

  return (
    <div className="fixed right-4 top-4 z-[60] flex w-[min(360px,calc(100vw-32px))] flex-col gap-2" aria-live="polite" aria-label={intl.formatMessage({ id: 'toast.containerAriaLabel' })}>
      {messages.map((message) => (
        <div key={message.id} role="status" className={`rounded-2xl border px-4 py-3 text-sm shadow-lg backdrop-blur ${variantClass[message.variant]}`}>
          <p className="font-semibold">
            <span className="sr-only">{intl.formatMessage({ id: variantLabelKey[message.variant] })}: </span>
            {message.title}
          </p>
          {message.description && <p className="mt-1 text-xs leading-5 opacity-80">{message.description}</p>}
        </div>
      ))}
    </div>
  );
}
