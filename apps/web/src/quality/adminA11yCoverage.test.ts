import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const adminFiles = [
  'layouts/AdminLayout.tsx',
  'pages/admin/LoginPage.tsx',
  'pages/admin/DashboardPage.tsx',
  'pages/admin/ErrorPage.tsx',
  'pages/admin/OrdersPage.tsx',
  'pages/admin/OrderDetailPage.tsx',
  'pages/admin/CasesPage.tsx',
  'pages/admin/CaseDetailPage.tsx',
] as const;

function readSource(path: string): string {
  return readFileSync(join(process.cwd(), 'src', path), 'utf8');
}

describe('Sprint 7 admin accessibility coverage', () => {
  it('keeps semantic landmarks on every admin surface', () => {
    const missing = adminFiles.filter((file) => {
      const source = readSource(file);
      return !/(<main|<nav|<section|<article|aria-label=|role=)/.test(source);
    });

    expect(missing).toEqual([]);
  });

  it('keeps form controls and filters explicitly labelled', () => {
    const filesWithControls = ['pages/admin/LoginPage.tsx', 'pages/admin/OrdersPage.tsx', 'pages/admin/CasesPage.tsx'] as const;
    const missing = filesWithControls.filter((file) => {
      const source = readSource(file);
      return !/(<label|label=)/.test(source);
    });

    expect(missing).toEqual([]);
  });

  it('keeps interactive admin controls keyboard-focus visible', () => {
    const filesWithButtons = ['layouts/AdminLayout.tsx', 'pages/admin/LoginPage.tsx', 'pages/admin/OrderDetailPage.tsx', 'pages/admin/ErrorPage.tsx'] as const;
    const missing = filesWithButtons.filter((file) => {
      const source = readSource(file);
      return !source.includes('focus:ring-2') && !source.includes('focus:outline-none');
    });

    expect(missing).toEqual([]);
  });

  it('keeps dark variants on every admin page and layout', () => {
    const missing = adminFiles.filter((file) => !readSource(file).includes('dark:'));

    expect(missing).toEqual([]);
  });
});
