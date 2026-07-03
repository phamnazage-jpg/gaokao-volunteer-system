/**
 * useAudit — 方案审核管理
 * 负责：审核报告状态、文件上传处理
 */

import { useState, useCallback } from "react";

export function useAudit() {
  const [currentAuditReport, setCurrentAuditReport] = useState<any>(null);

  const clearReport = useCallback(() => {
    setCurrentAuditReport(null);
  }, []);

  return {
    currentAuditReport,
    setCurrentAuditReport,
    clearReport,
  };
}
