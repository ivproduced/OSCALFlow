import { Command } from 'commander';
import fs from 'node:fs';
import path from 'node:path';
import chalk from 'chalk';
import ora from 'ora';
import { updateSSPWithSignals } from '../lib/mapper.js';
import type { ComplianceSignal } from '../lib/scanner.js';
import { getBaselineCount } from '../lib/profile-loader.js';

const CWE_TO_NIST: Record<string, string[]> = {
  'CWE-20': ['SI-10'],
  'CWE-22': ['AC-3', 'AC-6'],
  'CWE-78': ['SI-10', 'SI-16'],
  'CWE-79': ['SI-10'],
  'CWE-89': ['SI-10'],
  'CWE-94': ['SI-10', 'SI-16'],
  'CWE-200': ['AC-3', 'AC-6'],
  'CWE-256': ['IA-5', 'SC-28'],
  'CWE-259': ['IA-5', 'SC-12'],
  'CWE-269': ['AC-6'],
  'CWE-276': ['AC-3', 'AC-6'],
  'CWE-284': ['AC-3'],
  'CWE-285': ['AC-3', 'AC-6'],
  'CWE-295': ['SC-8', 'IA-5'],
  'CWE-306': ['IA-2', 'IA-3'],
  'CWE-312': ['SC-28', 'IA-5'],
  'CWE-319': ['SC-8'],
  'CWE-326': ['SC-13', 'IA-7'],
  'CWE-327': ['SC-13', 'IA-7'],
  'CWE-328': ['IA-5', 'SC-13'],
  'CWE-330': ['SC-13'],
  'CWE-400': ['SC-5'],
  'CWE-502': ['SI-10', 'SI-16'],
  'CWE-521': ['IA-5'],
  'CWE-522': ['IA-5', 'SC-28'],
  'CWE-611': ['SI-10'],
  'CWE-693': ['SI-16'],
  'CWE-732': ['AC-3', 'AC-6'],
  'CWE-798': ['IA-5', 'SC-12'],
  'CWE-862': ['AC-3'],
  'CWE-863': ['AC-3', 'AC-6'],
  'CWE-916': ['IA-5', 'SC-13']
};

const VULN_SCANNER_CONTROLS = ['RA-5', 'SI-2'];

function extractCwes(tags: string[]): string[] {
  return tags
    .filter((tag) => /^CWE-\d+$/i.test(tag))
    .map((tag) => tag.toUpperCase());
}

function mapRuleToControls(ruleId: string, tags: string[], level: string, toolName: string): string[] {
  const controls = new Set<string>();
  const toolLower = toolName.toLowerCase();

  if (toolLower.includes('trivy') || toolLower.includes('grype') || toolLower.includes('snyk')) {
    VULN_SCANNER_CONTROLS.forEach((control) => controls.add(control));
  }

  if (toolLower.includes('gitleaks') || toolLower.includes('trufflehog') || ruleId.toLowerCase().includes('secret')) {
    controls.add('IA-5');
    controls.add('SC-12');
  }

  for (const cwe of extractCwes(tags)) {
    for (const control of CWE_TO_NIST[cwe] ?? []) {
      controls.add(control);
    }
  }

  if (/^CVE-/i.test(ruleId)) {
    controls.add('RA-5');
    controls.add('SI-2');
  }

  if (controls.size === 0) {
    if (level === 'error') {
      controls.add('RA-5');
    } else if (level === 'warning') {
      controls.add('RA-3');
    } else {
      controls.add('CM-7');
    }
  }

  return Array.from(controls);
}

function parseSarif(sarifPath: string, toolHint: string): ComplianceSignal[] {
  const raw = fs.readFileSync(sarifPath, 'utf-8');
  const sarif = JSON.parse(raw) as {
    runs?: Array<{
      tool?: { driver?: { name?: string; rules?: Array<{ id: string; properties?: { tags?: string[] }; shortDescription?: { text?: string }; fullDescription?: { text?: string } }> } };
      results?: Array<{
        ruleId?: string;
        level?: string;
        message?: { text?: string };
        locations?: Array<{ physicalLocation?: { artifactLocation?: { uri?: string }; region?: { startLine?: number } } }>;
      }>;
    }>;
  };

  if (!Array.isArray(sarif.runs)) {
    throw new Error('Invalid SARIF: missing runs array');
  }

  const signals: ComplianceSignal[] = [];

  for (const run of sarif.runs) {
    const toolName = toolHint !== 'auto' ? toolHint : (run.tool?.driver?.name ?? 'unknown');
    const ruleMap = new Map<string, { tags: string[]; description: string }>();

    for (const rule of run.tool?.driver?.rules ?? []) {
      const tags = rule.properties?.tags ?? [];
      const description = rule.shortDescription?.text ?? rule.fullDescription?.text ?? rule.id ?? '';
      ruleMap.set(rule.id, { tags, description });
    }

    for (const result of run.results ?? []) {
      const ruleId = result.ruleId ?? '';
      const level = result.level ?? 'warning';
      const message = result.message?.text ?? ruleId;
      const location = result.locations?.[0]?.physicalLocation;
      const uri = location?.artifactLocation?.uri ?? 'unknown';
      const line = location?.region?.startLine;
      const ruleInfo = ruleMap.get(ruleId) ?? { tags: [], description: message };
      const controls = mapRuleToControls(ruleId, ruleInfo.tags, level, toolName);
      const file = line ? `${uri}:${line}` : uri;
      const evidence = `${toolName} finding: ${ruleInfo.description || message} [${ruleId}]`;
      const confidence = level === 'error' ? 'high' : level === 'warning' ? 'medium' : 'low';

      for (const control of controls) {
        signals.push({ file, control, evidence, confidence });
      }
    }
  }

  const seen = new Set<string>();
  return signals.filter((signal) => {
    const key = `${signal.control}:${signal.file}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

export const ingestCommand = new Command('ingest')
  .description('Ingest a SARIF report and map findings to NIST 800-53 controls')
  .argument('<sarif-file>', 'Path to SARIF 2.1.0 file (Trivy, Semgrep, CodeQL, Snyk, Grype, etc.)')
  .option('-u, --update <ssp-file>', 'SSP file to update with findings as evidence')
  .option('-o, --output <file>', 'Write signals JSON to this file')
  .option('-t, --tool <name>', 'Tool type hint (trivy|semgrep|codeql|snyk|grype|auto)', 'auto')
  .option('-b, --baseline <level>', 'Baseline for coverage display (low|moderate|high)', 'moderate')
  .option('-q, --quiet', 'Reduce console output')
  .action(async (sarifFile, options) => {
    const quiet = Boolean(options.quiet);
    const sarifPath = path.resolve(sarifFile);

    if (!fs.existsSync(sarifPath)) {
      console.error(chalk.red(`SARIF file not found: ${sarifPath}`));
      process.exit(1);
    }

    const spinner = quiet ? null : ora(`Parsing SARIF: ${path.basename(sarifPath)}`).start();

    try {
      const signals = parseSarif(sarifPath, options.tool);

      if (spinner) {
        spinner.succeed(chalk.green(`Parsed ${signals.length} signals from SARIF`));
      }

      if (!quiet) {
        const uniqueControls = new Set(signals.map((signal) => signal.control));
        const baseline = options.baseline as 'low' | 'moderate' | 'high';
        const totalControls = getBaselineCount(baseline);
        const coverage = ((uniqueControls.size / totalControls) * 100).toFixed(1);

        console.log(chalk.cyan('\n📊 SARIF Ingestion Summary:'));
        console.log(chalk.white(`   ├─ Findings processed: ${signals.length}`));
        console.log(chalk.white(`   ├─ Unique controls mapped: ${uniqueControls.size}`));
        console.log(chalk.white(`   └─ Coverage contribution: ${coverage}% of ${baseline.toUpperCase()} baseline\n`));

        console.log(chalk.cyan('🗺  Controls mapped from findings:'));
        for (const control of Array.from(uniqueControls).sort()) {
          const matchingSignals = signals.filter((signal) => signal.control === control);
          const confidence = matchingSignals[0]?.confidence ?? 'low';
          const badge = confidence === 'high'
            ? chalk.red('[HIGH]')
            : confidence === 'medium'
              ? chalk.yellow('[MED]')
              : chalk.gray('[LOW]');
          console.log(chalk.white(`   • ${control} ${badge} — ${matchingSignals.length} finding${matchingSignals.length !== 1 ? 's' : ''}`));
        }
        console.log('');
      }

      if (options.update) {
        const updatePath = path.resolve(options.update);
        if (!fs.existsSync(updatePath)) {
          console.error(chalk.red(`SSP file not found: ${updatePath}. Run 'gh oscal generate' first.`));
          process.exit(1);
        }
        const ssp = JSON.parse(fs.readFileSync(updatePath, 'utf-8'));
        const updated = updateSSPWithSignals(ssp, signals);
        fs.writeFileSync(updatePath, JSON.stringify(updated, null, 2));
        if (!quiet) {
          console.log(chalk.green(`✓ Updated SSP: ${updatePath}`));
        }
      }

      if (options.output) {
        const outputPath = path.resolve(options.output);
        fs.writeFileSync(outputPath, JSON.stringify(signals, null, 2));
        if (!quiet) {
          console.log(chalk.green(`✓ Signals written to: ${outputPath}`));
        }
      }
    } catch (error) {
      if (spinner) {
        spinner.fail(chalk.red('SARIF ingestion failed'));
      }
      console.error(chalk.red(error instanceof Error ? error.message : String(error)));
      process.exit(1);
    }
  });
