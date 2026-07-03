/**
 * useMessages — 消息列表管理
 * 负责：消息 CRUD、自动滚动、与咨询记录同步
 */

import { useState, useCallback, useRef, useEffect } from "react";
import type { Message } from "./useChat";

export function useMessages(initialMessages: Message[]) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const addMessage = useCallback((msg: Message) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const replaceMessages = useCallback((msgs: Message[]) => {
    setMessages(msgs);
  }, []);

  const updateLastMessage = useCallback(
    (updater: (msg: Message) => Message) => {
      setMessages((prev) => {
        if (prev.length === 0) return prev;
        const updated = [...prev];
        updated[updated.length - 1] = updater(updated[updated.length - 1]);
        return updated;
      });
    },
    []
  );

  const scrollToBottom = useCallback(() => {
    // Use requestAnimationFrame for smoother scroll after DOM update
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    });
  }, []);

  /** 按 id 更新指定消息的 data（用于方案卡片就地更新等场景） */
  const updateMessageData = useCallback(
    (messageId: string, newData: any) => {
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, data: newData } : m))
      );
    },
    []
  );

  /** 按类型查找最后一个匹配的消息并就地更新其 data */
  const updateLastMessageOfType = useCallback(
    (type: string, newData: any) => {
      setMessages((prev) => {
        const idx = [...prev].reverse().findIndex((m) => m.type === type);
        if (idx === -1) return prev;
        const realIdx = prev.length - 1 - idx;
        const updated = [...prev];
        updated[realIdx] = { ...updated[realIdx], data: newData };
        return updated;
      });
    },
    []
  );

  return {
    messages,
    setMessages: replaceMessages,
    addMessage,
    updateLastMessage,
    updateMessageData,
    updateLastMessageOfType,
    messagesEndRef,
    scrollToBottom,
  };
}

/**
 * 自动滚动到最新消息
 */
export function useAutoScroll(
  messages: Message[],
  isTyping: boolean,
  scrollToBottom: () => void
) {
  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);
}
