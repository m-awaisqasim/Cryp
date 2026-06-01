import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();

test('package metadata exposes runnable checks', () => {
  const pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));

  expect(pkg.name).toBe('cryp');
  expect(pkg.scripts.test).toBe('playwright test');
  expect(pkg.scripts['python:check']).toContain('py_compile');
  expect(pkg.repository.url).toContain('m-awaisqasim/Cryp');
});

test('python dependency manifest covers imported optional modules', () => {
  const requirements = readFileSync(join(root, 'requirements.txt'), 'utf8').toLowerCase();

  for (const dependency of [
    'websockets',
    'pdfplumber',
    'pypdf2',
    'python-docx',
    'pandas',
    'openpyxl',
    'pydub',
    'audioop-lts',
    'plyer',
  ]) {
    expect(requirements).toContain(dependency);
  }
});
