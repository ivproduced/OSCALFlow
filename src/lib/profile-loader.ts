import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export type Baseline = 'low' | 'moderate' | 'high' | 'privacy';

const cache = new Map<string, string[]>();

/**
 * Load control IDs from the bundled NIST 800-53 Rev 5 baseline profile.
 * Returns uppercase control IDs in parenthesis notation (e.g. 'AC-2', 'AC-2(1)').
 */
export function loadBaselineControlIds(baseline: Baseline): string[] {
  const cached = cache.get(baseline);
  if (cached) return cached;

  const fileName = `NIST_SP-800-53_rev5_${baseline.toUpperCase()}-baseline_profile.json`;
  const filePath = path.join(__dirname, '../../data/nist', fileName);

  let raw: string;
  try {
    raw = fs.readFileSync(filePath, 'utf-8');
  } catch {
    throw new Error(`NIST baseline profile not found: ${fileName}. Ensure the data/nist/ directory is intact.`);
  }

  const profile = JSON.parse(raw);
  const withIds: string[] = profile?.profile?.imports?.[0]?.['include-controls']?.[0]?.['with-ids'] ?? [];

  if (withIds.length === 0) {
    throw new Error(`No controls found in baseline profile: ${fileName}`);
  }

  const controls = withIds.map((id) => {
    const upper = id.toUpperCase();
    return upper.replace(/\.(\d+)$/, '($1)');
  });

  cache.set(baseline, controls);
  return controls;
}

/** Return count of controls in a baseline (useful for scan coverage %). */
export function getBaselineCount(baseline: Baseline): number {
  return loadBaselineControlIds(baseline).length;
}
