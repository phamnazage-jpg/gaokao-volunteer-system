/**
 * usePlan — 志愿方案管理
 * 负责：方案状态、保存/删除/重命名、导出
 */

import { useState, useCallback } from "react";
import type { UserProfile } from "./useChat";

export interface SavedPlan {
  id: string;
  name: string;
  createdAt: string;
  plan: any;
  profile: UserProfile;
}

const SAVED_PLANS_KEY = "savedPlans";

function loadSavedPlans(): SavedPlan[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(SAVED_PLANS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function persistPlans(plans: SavedPlan[]) {
  try {
    localStorage.setItem(SAVED_PLANS_KEY, JSON.stringify(plans));
  } catch {
    /* quota exceeded — silently ignore */
  }
}

export function usePlan() {
  const [currentPlan, setCurrentPlan] = useState<any>(null);
  const [savedPlans, setSavedPlans] = useState<SavedPlan[]>(loadSavedPlans);

  const savePlan = useCallback(
    (plan: any, profile: UserProfile, customName?: string) => {
      const now = new Date();
      const pad = (n: number) => String(n).padStart(2, "0");
      const defaultName = `方案_${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}`;
      const newPlan: SavedPlan = {
        id: `plan-${Date.now()}`,
        name: customName || defaultName,
        createdAt: now.toISOString(),
        plan,
        profile,
      };
      const updated = [...savedPlans, newPlan];
      setSavedPlans(updated);
      persistPlans(updated);
      return newPlan;
    },
    [savedPlans]
  );

  const deletePlan = useCallback(
    (id: string) => {
      const updated = savedPlans.filter((p) => p.id !== id);
      setSavedPlans(updated);
      persistPlans(updated);
    },
    [savedPlans]
  );

  const updatePlanName = useCallback(
    (id: string, name: string) => {
      const updated = savedPlans.map((p) =>
        p.id === id ? { ...p, name } : p
      );
      setSavedPlans(updated);
      persistPlans(updated);
    },
    [savedPlans]
  );

  return {
    currentPlan,
    setCurrentPlan,
    savedPlans,
    savePlan,
    deletePlan,
    updatePlanName,
  };
}
