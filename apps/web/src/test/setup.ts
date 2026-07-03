/**
 * V10 选项 B · Vitest + RTL + MSW 全局 setup
 *
 * G1 闸门:
 *  - 每个测试前 reset 所有 Zustand store
 *  - 启动 MSW server 拦截 fetch
 *  - 注入 @testing-library/jest-dom 断言
 */
import '@testing-library/jest-dom/vitest';
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest';
import { resetAllStores } from '@/stores';
import { server } from './mocks/server';

// ====== MSW 启动 / 关闭 ======
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
});

afterAll(() => {
  server.close();
});

// ====== 每个测试后清理 ======
afterEach(() => {
  server.resetHandlers();
});

// ====== 每个测试前重置所有 store ======
beforeEach(() => {
  resetAllStores();
});

// ====== 模拟 matchMedia (jsdom 默认没有) ======
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => undefined,
    removeListener: () => undefined,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  }),
});

// ====== 模拟 ResizeObserver (jsdom 默认没有) ======
class MockResizeObserver {
  private readonly callback: ResizeObserverCallback;

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }

  observe(target: Element): void {
    this.callback(
      [
        {
          target,
          contentRect: {
            x: 0,
            y: 0,
            width: 320,
            height: 128,
            top: 0,
            right: 320,
            bottom: 128,
            left: 0,
            toJSON: () => ({}),
          },
        } as ResizeObserverEntry,
      ],
      this,
    );
  }
  unobserve(): void {
    /* noop */
  }
  disconnect(): void {
    /* noop */
  }
}
(globalThis as unknown as { ResizeObserver: typeof MockResizeObserver }).ResizeObserver = MockResizeObserver;

// ====== 模拟 IntersectionObserver ======
class MockIntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin = '';
  readonly thresholds: ReadonlyArray<number> = [];
  observe(): void {
    /* noop */
  }
  unobserve(): void {
    /* noop */
  }
  disconnect(): void {
    /* noop */
  }
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}
(globalThis as unknown as { IntersectionObserver: typeof MockIntersectionObserver }).IntersectionObserver = MockIntersectionObserver;


// ====== 模拟 scrollIntoView (jsdom 默认没有) ======
Object.defineProperty(Element.prototype, 'scrollIntoView', {
  writable: true,
  value: () => undefined,
});
