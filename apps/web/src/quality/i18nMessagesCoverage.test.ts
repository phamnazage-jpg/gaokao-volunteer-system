import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { messages } from '@/i18n/messages';

const sprint7I18nSourceFiles = [
  'layouts/AppLayout.tsx',
  'layouts/AdminLayout.tsx',
  'components/navigation/Sidebar.tsx',
  'components/navigation/MobileNav.tsx',
  'components/navigation/ModeIndicator.tsx',
  'pages/AboutPage.tsx',
  'pages/NotFoundPage.tsx',
  'components/shared/ErrorFallback.tsx',
  'pages/PlansPage.tsx',
  'pages/PlanComparePage.tsx',
  'pages/PlanDetailPage.tsx',
  'pages/ConsultationsPage.tsx',
  'pages/ShareDialogPage.tsx',
  'components/ShareDialog.tsx',
  'components/SharePanel.tsx',
  'components/ShareStatusPanel.tsx',
  'components/StatsCard.tsx',
  'components/AccessTrendChart.tsx',
  'pages/PosterPreviewPage.tsx',
  'components/PosterPreview.tsx',
  'pages/DataQueryPage.tsx',
  'components/DataQueryForm.tsx',
  'components/DataQueryResult.tsx',
  'pages/HomePage.tsx',
  'components/FormCard.tsx',
  'components/shared/ProgressSteps.tsx',
  'pages/ReviewPage.tsx',
  'components/ReviewFlow.tsx',
  'components/LLMEnhancement.tsx',
  'components/AuditReportCard.tsx',
  'components/PlanCard.tsx',
  'components/CareerCard.tsx',
  'components/FileUploadPrompt.tsx',
  'components/UploadBar.tsx',
  'pages/PortalPage.tsx',
  'components/shared/ThemeToggle.tsx',
  'components/shared/Toast.tsx',
  'components/shared/Pagination.tsx',
  'components/shared/RouteFallback.tsx',
  'components/shared/OfflineBanner.tsx',
  'components/shared/DataTable.tsx',
  'components/shared/Skeleton.tsx',
  'components/shared/Charts.tsx',
  'components/shared/Modal.tsx',
  'components/shared/Stepper.tsx',
  'components/shared/Tree.tsx',
  'components/shared/Accordion.tsx',
  'components/shared/SubmitButton.tsx',
  'components/shared/Avatar.tsx',
  'pages/admin/ErrorPage.tsx',
  'pages/admin/LoginPage.tsx',
  'pages/admin/ForbiddenPage.tsx',
  'pages/admin/DashboardPage.tsx',
  'pages/admin/OrdersPage.tsx',
  'pages/admin/CasesPage.tsx',
  'pages/admin/ShareLinksPage.tsx',
  'pages/admin/ShareLinkDetailPage.tsx',
  'pages/admin/PostersPage.tsx',
  'pages/admin/ScoreLinesPage.tsx',
  'pages/admin/RankEstimatorPage.tsx',
  'pages/admin/MajorsPage.tsx',
  'pages/admin/SchoolsPage.tsx',
  'pages/admin/OrderDetailPage.tsx',
  'pages/admin/CaseDetailPage.tsx',
] as const;

function readSource(path: string): string {
  return readFileSync(join(process.cwd(), 'src', path), 'utf8');
}

describe('Sprint 7 i18n messages coverage', () => {
  it('keeps zh-CN and en-US message keys aligned', () => {
    const zhKeys = Object.keys(messages['zh-CN']).sort();
    const enKeys = Object.keys(messages['en-US']).sort();

    expect(enKeys).toEqual(zhKeys);
  });

  it('does not leave empty message values in either locale', () => {
    const emptyEntries = Object.entries(messages).flatMap(([locale, localeMessages]) =>
      Object.entries(localeMessages)
        .filter(([, value]) => value.trim().length === 0)
        .map(([key]) => `${locale}.${key}`),
    );

    expect(emptyEntries).toEqual([]);
  });

  it('keeps migrated Sprint 7 admin surfaces free of hardcoded Chinese copy', () => {
    const filesWithHardcodedChinese = sprint7I18nSourceFiles.filter((file) => /[\u4e00-\u9fff]/.test(readSource(file)));

    expect(filesWithHardcodedChinese).toEqual([]);
  });
});
