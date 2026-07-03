/**
 * V10 · Sprint 3 · useScrollRecovery
 *
 * 滚动恢复 hook：sessionId/消息数变化时滚到底部；用户上滑时不打断
 * V10 不变量：UI 1:1 复现（V2 Plan §3.1 L1）
 */
import { useEffect, useRef } from 'react';

export interface ScrollRecoveryOptions {
  readonly threshold?: number;
}

export function useScrollRecovery<T extends HTMLElement>(
  deps: ReadonlyArray<unknown>,
  options: ScrollRecoveryOptions = {},
): React.MutableRefObject<T | null> {
  const ref = useRef<T | null>(null);
  const userScrolledUp = useRef(false);
  const threshold = options.threshold ?? 80;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const handleScroll = (): void => {
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      userScrolledUp.current = distanceFromBottom > threshold;
    };
    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, [threshold]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!userScrolledUp.current) {
      requestAnimationFrame(() => {
        el.scrollTop = el.scrollHeight;
      });
    }
    // deps 变化时重置 userScrolledUp, 让新会话能滚到底
    userScrolledUp.current = false;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return ref;
}