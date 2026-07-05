import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { describe, expect, it } from 'vitest';

const SRC_ROOT = join(process.cwd(), 'src');
const SOURCE_EXTENSIONS = new Set(['.ts', '.tsx']);

function collectSourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const fullPath = join(dir, entry);
    const stats = statSync(fullPath);

    if (stats.isDirectory()) {
      return collectSourceFiles(fullPath);
    }

    const normalized = relative(SRC_ROOT, fullPath).split(sep).join('/');
    const extension = fullPath.slice(fullPath.lastIndexOf('.'));
    const isRuntimeSource = SOURCE_EXTENSIONS.has(extension) && !normalized.includes('.test.') && !normalized.startsWith('test/');

    return isRuntimeSource ? [fullPath] : [];
  });
}

describe('runtime alert usage', () => {
  it('does not use blocking alert dialogs in app source', () => {
    const offenders = collectSourceFiles(SRC_ROOT).filter((filePath) => {
      const content = readFileSync(filePath, 'utf8');
      return /\b(?:window\.)?alert\s*\(/.test(content);
    });

    expect(offenders.map((filePath) => relative(SRC_ROOT, filePath).split(sep).join('/'))).toEqual([]);
  });
});
