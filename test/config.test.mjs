import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { loadOscalFlowConfig, parseDetectorList, findConfigPath } from '../dist/lib/config.js';

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'oscalflow-config-test-'));
}

test('loadOscalFlowConfig returns defaults when config file is missing', () => {
  const tempDir = makeTempDir();
  try {
    const result = loadOscalFlowConfig(tempDir);
    assert.equal(result.path, null);
    assert.deepEqual(result.config, {});
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
});

test('loadOscalFlowConfig loads valid fields and detector arrays', () => {
  const tempDir = makeTempDir();
  const configPath = path.join(tempDir, '.oscalflow.json');

  const config = {
    baseline: 'high',
    systemName: 'Submission API',
    defaultOutput: 'custom-ssp.json',
    scanOutput: 'custom-scan.json',
    quiet: true,
    suppressTips: true,
    pager: true,
    enabledDetectors: ['containers', 'cicd', 'containers'],
    disabledDetectors: ['sbom', 'cloud']
  };

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

  try {
    const result = loadOscalFlowConfig(tempDir);

    assert.equal(result.path, configPath);
    assert.equal(result.config.baseline, 'high');
    assert.equal(result.config.systemName, 'Submission API');
    assert.equal(result.config.defaultOutput, 'custom-ssp.json');
    assert.equal(result.config.scanOutput, 'custom-scan.json');
    assert.equal(result.config.quiet, true);
    assert.equal(result.config.suppressTips, true);
    assert.equal(result.config.pager, true);
    assert.deepEqual(result.config.enabledDetectors, ['containers', 'cicd']);
    assert.deepEqual(result.config.disabledDetectors, ['sbom', 'cloud']);
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
});

test('findConfigPath walks up parent directories', () => {
  const tempDir = makeTempDir();
  const nestedDir = path.join(tempDir, 'a', 'b', 'c');
  fs.mkdirSync(nestedDir, { recursive: true });

  const configPath = path.join(tempDir, '.oscalflow.json');
  fs.writeFileSync(configPath, JSON.stringify({ baseline: 'moderate' }));

  try {
    const found = findConfigPath(nestedDir);
    assert.equal(found, configPath);
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
});

test('parseDetectorList ignores invalid detector names', () => {
  const parsed = parseDetectorList('containers,cloud,not-real,cicd');
  assert.deepEqual(parsed, ['containers', 'cloud', 'cicd']);
});
