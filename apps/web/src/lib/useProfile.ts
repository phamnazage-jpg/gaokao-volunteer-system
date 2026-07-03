/**
 * useProfile — 用户画像管理
 * 负责：画像状态、从文本解析信息、完整性检查
 */

import { useState, useCallback } from "react";
import type { UserProfile } from "./useChat";

/** 从用户输入文本中提取画像信息 */
export function extractProfileFromText(
  text: string,
  currentProfile: UserProfile
): UserProfile {
  const next = { ...currentProfile };

  const scoreMatch = text.match(/(\d{3})\s*分/);
  if (scoreMatch) next.score = parseInt(scoreMatch[1], 10);

  const rankMatch = text.match(/位次\s*(\d+)/);
  if (rankMatch) next.rank = parseInt(rankMatch[1], 10);

  const provinceMatch = text.match(
    /(广东|河南|山东|四川|江苏|浙江|湖北|湖南|北京|上海|天津|重庆|福建|安徽|河北|辽宁|吉林|黑龙江|陕西|山西|江西|广西|云南|贵州|海南|甘肃|宁夏|青海|西藏|新疆|内蒙古)/
  );
  if (provinceMatch) next.province = provinceMatch[1];

  if (text.includes("物理")) {
    next.subjects = ["物理", "化学", "生物"];
  } else if (text.includes("历史")) {
    next.subjects = ["历史", "政治", "地理"];
  }

  return next;
}

/** 检查是否已具备核心信息（省份 + 分数 + 选科） */
export function hasCoreInfo(profile: UserProfile): boolean {
  return Boolean(profile.province && profile.score && profile.subjects);
}

/** 检查是否有任何信息 */
export function hasAnyInfo(profile: UserProfile): boolean {
  return Boolean(profile.province || profile.score || profile.subjects);
}

/** 获取缺失的核心字段名 */
export function getMissingFields(profile: UserProfile): string[] {
  const missing: string[] = [];
  if (!profile.province) missing.push("省份");
  if (!profile.score) missing.push("分数");
  if (!profile.subjects) missing.push("选科");
  return missing;
}

export function useProfile(initialProfile: UserProfile = {}) {
  const [userProfile, setUserProfile] = useState<UserProfile>(initialProfile);

  const updateProfile = useCallback(
    (partial: Partial<UserProfile>) => {
      setUserProfile((prev) => ({ ...prev, ...partial }));
    },
    []
  );

  const updateFromText = useCallback(
    (text: string) => {
      const next = extractProfileFromText(text, userProfile);
      setUserProfile(next);
      return next;
    },
    [userProfile]
  );

  const isComplete = hasCoreInfo(userProfile);
  const hasPartial = hasAnyInfo(userProfile);
  const missing = getMissingFields(userProfile);

  return {
    userProfile,
    setUserProfile,
    updateProfile,
    updateFromText,
    isComplete,
    hasPartial,
    missing,
  };
}
