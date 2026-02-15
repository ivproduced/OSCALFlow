import fs from 'node:fs';
import path from 'node:path';
import { DETECTOR_NAMES, type DetectorName } from './scanner.js';

export interface OscalFlowConfig {
  baseline?: 'low' | 'moderate' | 'high';
  systemName?: string;
  defaultOutput?: string;
  scanOutput?: string;
  quiet?: boolean;
  suppressTips?: boolean;
  pager?: boolean;
  enabledDetectors?: DetectorName[];
  disabledDetectors?: DetectorName[];
}

const CONFIG_FILE_NAME = '.oscalflow.json';

export function findConfigPath(startDir: string): string | null {
  let currentDir = path.resolve(startDir);

  while (true) {
    const candidate = path.join(currentDir, CONFIG_FILE_NAME);
    if (fs.existsSync(candidate)) {
      return candidate;
    }

    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) {
      return null;
    }

    currentDir = parentDir;
  }
}

function normalizeDetectorList(value: unknown): DetectorName[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const allowed = new Set<string>(DETECTOR_NAMES);
  const normalized = value
    .filter((item): item is string => typeof item === 'string')
    .map((item) => item.trim().toLowerCase())
    .filter((item) => item.length > 0 && allowed.has(item));

  return Array.from(new Set(normalized)) as DetectorName[];
}

function isValidBaseline(value: unknown): value is 'low' | 'moderate' | 'high' {
  return value === 'low' || value === 'moderate' || value === 'high';
}

export function loadOscalFlowConfig(startDir: string): { config: OscalFlowConfig; path: string | null } {
  const configPath = findConfigPath(startDir);

  if (!configPath) {
    return { config: {}, path: null };
  }

  try {
    const raw = JSON.parse(fs.readFileSync(configPath, 'utf-8')) as Record<string, unknown>;

    const config: OscalFlowConfig = {};

    if (isValidBaseline(raw.baseline)) {
      config.baseline = raw.baseline;
    }

    if (typeof raw.systemName === 'string' && raw.systemName.trim().length > 0) {
      config.systemName = raw.systemName.trim();
    }

    if (typeof raw.defaultOutput === 'string' && raw.defaultOutput.trim().length > 0) {
      config.defaultOutput = raw.defaultOutput.trim();
    }

    if (typeof raw.scanOutput === 'string' && raw.scanOutput.trim().length > 0) {
      config.scanOutput = raw.scanOutput.trim();
    }

    if (typeof raw.quiet === 'boolean') {
      config.quiet = raw.quiet;
    }

    if (typeof raw.suppressTips === 'boolean') {
      config.suppressTips = raw.suppressTips;
    }

    if (typeof raw.pager === 'boolean') {
      config.pager = raw.pager;
    }

    config.enabledDetectors = normalizeDetectorList(raw.enabledDetectors);
    config.disabledDetectors = normalizeDetectorList(raw.disabledDetectors);

    return { config, path: configPath };
  } catch {
    return { config: {}, path: configPath };
  }
}

export function parseDetectorList(raw: string | undefined): DetectorName[] {
  if (!raw) {
    return [];
  }

  const allowed = new Set<string>(DETECTOR_NAMES);
  const detectors = raw
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter((item) => item.length > 0 && allowed.has(item));

  return Array.from(new Set(detectors)) as DetectorName[];
}
