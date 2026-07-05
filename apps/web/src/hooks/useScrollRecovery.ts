/**
 * V10 · Sprint 3 · useScrollRecovery
 *
 * Scroll recovery hook: scrolls to bottom when sessionId/message count changes, without interrupting manual upward scrolls.
 * V10 invariant: 1:1 UI recreation (V2 Plan §3.1 L1).
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
    // Reset userScrolledUp when dependencies change, so new sessions can scroll to the bottom.
    userScrolledUp.current = false;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return ref;
}
