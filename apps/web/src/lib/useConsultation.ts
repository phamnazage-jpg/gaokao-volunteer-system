/**
 * useConsultation — 咨询记录管理
 * 负责：多会话 CRUD、localStorage 持久化
 */

import { useState, useCallback, useEffect } from "react";
import type { Message, UserProfile } from "./useChat";

export interface ConsultationRecord {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
  userProfile: UserProfile;
  currentPlan?: any;
  currentAuditReport?: any;
}

const RECORDS_KEY = "consultationRecords";
const ACTIVE_ID_KEY = "activeConsultationId";
const MAX_RECORDS = 50;

function toDate(value: unknown): Date {
  if (value instanceof Date) return value;
  if (typeof value === "string" || typeof value === "number") {
    const d = new Date(value);
    if (!Number.isNaN(d.getTime())) return d;
  }
  return new Date();
}

function normalizeMessages(messages: Message[]): Message[] {
  return messages.map((msg) => ({
    ...msg,
    timestamp: toDate(msg.timestamp),
  }));
}

function loadRecords(): ConsultationRecord[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(RECORDS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ConsultationRecord[];
    return parsed.map((r) => ({
      ...r,
      messages: normalizeMessages(r.messages || []),
      userProfile: r.userProfile || {},
    }));
  } catch {
    return [];
  }
}

function persistRecords(records: ConsultationRecord[]) {
  try {
    localStorage.setItem(RECORDS_KEY, JSON.stringify(records));
  } catch {
    /* quota exceeded */
  }
}

export function createRecordId() {
  return `consult-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function buildRecordTitle(
  messages: Message[],
  profile: UserProfile
): string {
  const firstUserMsg = messages
    .find((m) => m.role === "user")
    ?.content?.trim();
  if (firstUserMsg) {
    return firstUserMsg.slice(0, 24) + (firstUserMsg.length > 24 ? "…" : "");
  }
  if (profile.province || profile.score || profile.subjects?.length) {
    return [
      profile.province,
      profile.subjects?.join("+"),
      profile.score ? `${profile.score}分` : undefined,
    ]
      .filter(Boolean)
      .join(" · ");
  }
  return "新的升学咨询";
}

export function useConsultation(
  messages: Message[],
  userProfile: UserProfile,
  currentPlan: any,
  currentAuditReport: any
) {
  const [activeRecordId, setActiveRecordId] = useState<string>(() => {
    if (typeof window === "undefined") return createRecordId();
    const records = loadRecords();
    const activeId = localStorage.getItem(ACTIVE_ID_KEY);
    return (
      records.find((r) => r.id === activeId)?.id ||
      records[0]?.id ||
      createRecordId()
    );
  });

  // Auto-persist on state changes (debounced by React batching)
  useEffect(() => {
    if (typeof window === "undefined") return;
    const now = new Date().toISOString();
    const records = loadRecords();
    const existing = records.find((r) => r.id === activeRecordId);

    const next: ConsultationRecord = {
      id: activeRecordId,
      title: buildRecordTitle(messages, userProfile),
      createdAt: existing?.createdAt || now,
      updatedAt: now,
      messages,
      userProfile,
      currentPlan,
      currentAuditReport,
    };

    const updated = [next, ...records.filter((r) => r.id !== activeRecordId)];
    persistRecords(updated.slice(0, MAX_RECORDS));

    try {
      localStorage.setItem(ACTIVE_ID_KEY, activeRecordId);
    } catch {
      /* ignore */
    }
  }, [activeRecordId, messages, userProfile, currentPlan, currentAuditReport]);

  const newConsultation = useCallback(() => {
    const id = createRecordId();
    setActiveRecordId(id);
    try {
      localStorage.setItem(ACTIVE_ID_KEY, id);
    } catch {
      /* ignore */
    }
    return id;
  }, []);

  const loadConsultation = useCallback(
    (id: string): ConsultationRecord | null => {
      const record = loadRecords().find((r) => r.id === id);
      if (!record) return null;
      setActiveRecordId(record.id);
      try {
        localStorage.setItem(ACTIVE_ID_KEY, record.id);
      } catch {
        /* ignore */
      }
      return record;
    },
    []
  );

  return {
    activeRecordId,
    setActiveRecordId,
    newConsultation,
    loadConsultation,
  };
}
