import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const COMPONENTS = [
  'SharePanel.tsx',
  'ShareStatusPanel.tsx',
  'DataQueryForm.tsx',
  'DataQueryResult.tsx',
  'ReviewFlow.tsx',
  'LLMEnhancement.tsx',
  'PosterPreview.tsx',
] as const;

describe('Sprint 6 business component dark mode coverage', () => {
  it('keeps dark variants on every extracted business component', () => {
    const missing = COMPONENTS.filter((fileName) => {
      const content = readFileSync(join(process.cwd(), 'src', 'components', fileName), 'utf8');
      return !content.includes('dark:');
    });

    expect(missing).toEqual([]);
  });
});
