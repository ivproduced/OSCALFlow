import test from 'node:test';
import assert from 'node:assert/strict';

import { classifySignal, filterSignalsByDetectors } from '../dist/lib/scanner.js';

const sampleSignals = [
  { file: 'Dockerfile', control: 'SC-39', evidence: 'container isolation via Docker' },
  { file: '.github/workflows/ci.yml', control: 'CM-3', evidence: 'Automated configuration change control via GitHub Actions workflows' },
  { file: 'CycloneDX SBOM', control: 'SR-4', evidence: 'Supply chain provenance via CycloneDX Software Bill of Materials' },
  { file: 'backend/requirements.txt', control: 'IA-5', evidence: 'Password hashing implemented with bcrypt' }
];

test('classifySignal maps known categories', () => {
  assert.equal(classifySignal(sampleSignals[0]), 'containers');
  assert.equal(classifySignal(sampleSignals[1]), 'cicd');
  assert.equal(classifySignal(sampleSignals[2]), 'sbom');
  assert.equal(classifySignal(sampleSignals[3]), 'dependencies');
});

test('filterSignalsByDetectors respects disabled detectors', () => {
  const filtered = filterSignalsByDetectors(sampleSignals, [], ['sbom']);
  assert.equal(filtered.length, 3);
  assert.equal(filtered.some((signal) => classifySignal(signal) === 'sbom'), false);
});

test('filterSignalsByDetectors respects enabled detectors allow-list', () => {
  const filtered = filterSignalsByDetectors(sampleSignals, ['containers', 'cicd'], []);
  assert.equal(filtered.length, 2);
  assert.deepEqual(filtered.map((signal) => classifySignal(signal)).sort(), ['cicd', 'containers']);
});

test('disabled detector takes precedence when both enabled and disabled are set', () => {
  const filtered = filterSignalsByDetectors(sampleSignals, ['containers', 'cicd'], ['containers']);
  assert.equal(filtered.length, 1);
  assert.equal(classifySignal(filtered[0]), 'cicd');
});
