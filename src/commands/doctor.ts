import { Command } from 'commander';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import chalk from 'chalk';
import { findConfigPath } from '../lib/config.js';

interface CheckResult {
  name: string;
  ok: boolean;
  details: string;
}

function checkCommandVersion(command: string): string | null {
  try {
    return execSync(`${command} --version`, { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return null;
  }
}

function hasWriteAccess(targetPath: string): boolean {
  try {
    fs.accessSync(targetPath, fs.constants.W_OK);
    return true;
  } catch {
    return false;
  }
}

export const doctorCommand = new Command('doctor')
  .description('Run diagnostics for OSCALFLOW environment and repository setup')
  .argument('[path]', 'Repository path to inspect', '.')
  .action((repoPath: string) => {
    const absolutePath = path.resolve(repoPath);
    const checks: CheckResult[] = [];

    const nodeMajor = Number(process.versions.node.split('.')[0]);
    checks.push({
      name: 'Node.js version',
      ok: nodeMajor >= 18,
      details: `Detected ${process.versions.node} (requires >= 18)`
    });

    const ghVersion = checkCommandVersion('gh');
    checks.push({
      name: 'GitHub CLI installed',
      ok: ghVersion !== null,
      details: ghVersion ?? 'gh not found on PATH'
    });

    const gitVersion = checkCommandVersion('git');
    checks.push({
      name: 'Git installed',
      ok: gitVersion !== null,
      details: gitVersion ?? 'git not found on PATH'
    });

    checks.push({
      name: 'Repository path exists',
      ok: fs.existsSync(absolutePath),
      details: absolutePath
    });

    checks.push({
      name: 'Repository path writable',
      ok: hasWriteAccess(absolutePath),
      details: hasWriteAccess(absolutePath) ? 'Writable' : 'Not writable'
    });

    const gitDir = path.join(absolutePath, '.git');
    checks.push({
      name: 'Git metadata present',
      ok: fs.existsSync(gitDir),
      details: fs.existsSync(gitDir) ? '.git directory found' : '.git directory missing'
    });

    if (fs.existsSync(gitDir)) {
      checks.push({
        name: '.git writable',
        ok: hasWriteAccess(gitDir),
        details: hasWriteAccess(gitDir) ? 'Writable' : 'Not writable (sync tools can block this)'
      });
    }

    const configPath = findConfigPath(absolutePath);
    checks.push({
      name: 'Repo config',
      ok: true,
      details: configPath ? `Using ${configPath}` : 'No .oscalflow.json found (optional)'
    });

    const requiredCatalogFiles = [
      'data/nist/NIST_SP-800-53_rev5_catalog.json',
      'data/nist/NIST_SP-800-53_rev5_LOW-baseline_profile.json',
      'data/nist/NIST_SP-800-53_rev5_MODERATE-baseline_profile.json',
      'data/nist/NIST_SP-800-53_rev5_HIGH-baseline_profile.json'
    ];

    const missingCatalogs = requiredCatalogFiles.filter((file) => !fs.existsSync(path.join(absolutePath, file)));
    checks.push({
      name: 'NIST baseline data',
      ok: missingCatalogs.length === 0,
      details: missingCatalogs.length === 0 ? 'All required files present' : `Missing: ${missingCatalogs.join(', ')}`
    });

    console.log(chalk.cyan('\nOSCALFLOW Doctor\n'));

    for (const check of checks) {
      const icon = check.ok ? chalk.green('✓') : chalk.red('✗');
      console.log(`${icon} ${chalk.white(check.name)}: ${chalk.gray(check.details)}`);
    }

    const failed = checks.filter((check) => !check.ok);
    if (failed.length === 0) {
      console.log(chalk.green('\nAll checks passed.\n'));
      return;
    }

    console.log(chalk.yellow(`\n${failed.length} check(s) need attention.`));
    console.log(chalk.gray('Tip: if commits fail in cloud-synced folders, move repo to a local non-synced path.\n'));
    process.exit(1);
  });
