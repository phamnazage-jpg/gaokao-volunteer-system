/**
 * useSimulation — 模拟异步操作
 * 负责：打字动画延迟、方案生成分步提示
 */

import { useState, useCallback } from "react";

export function useSimulation() {
  const [isTyping, setIsTyping] = useState(false);

  const simulateTyping = useCallback(
    (duration: number): Promise<void> => {
      setIsTyping(true);
      return new Promise((resolve) => {
        setTimeout(() => {
          setIsTyping(false);
          resolve();
        }, duration);
      });
    },
    []
  );

  /** 分步模拟 — 带文本提示的渐进式进度 */
  const simulateSteps = useCallback(
    async (
      steps: { text: string; duration: number }[],
      onStep: (text: string) => void
    ): Promise<void> => {
      for (const step of steps) {
        onStep(step.text);
        await simulateTyping(step.duration);
      }
    },
    [simulateTyping]
  );

  return {
    isTyping,
    simulateTyping,
    simulateSteps,
  };
}
