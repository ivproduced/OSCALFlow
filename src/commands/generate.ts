import { Command } from 'commander';
import fs from 'node:fs';
import path from 'node:path';
import chalk from 'chalk';
import ora from 'ora';
import { generateSSP, SSPOptions } from '../lib/oscal-writer.js';
import { loadOscalFlowConfig } from '../lib/config.js';

export const generateCommand = new Command('generate')
  .description('Generate OSCAL SSP skeleton with baseline controls')
  .option('-b, --baseline <level>', 'Impact baseline (low|moderate|high)', 'moderate')
  .option('-s, --system <name>', 'System name', 'Unnamed System')
  .option('-o, --output <file>', 'Output file path', 'ssp-draft.json')
  .option('--fetch-controls', 'Fetch control details from NIST catalog', false)
  .option('-q, --quiet', 'Reduce console output')
  .action(async (options) => {
    const { config } = loadOscalFlowConfig(process.cwd());
    const quiet = Boolean(options.quiet || config.quiet);
    const baselineOption = options.baseline === 'moderate' && config.baseline ? config.baseline : options.baseline;
    const systemName = options.system === 'Unnamed System' && config.systemName ? config.systemName : options.system;
    const outputFile = options.output === 'ssp-draft.json' && config.defaultOutput ? config.defaultOutput : options.output;

    const spinner = quiet ? null : ora('Generating SSP skeleton...').start();
    
    try {
      const baseline = baselineOption.toLowerCase();
      if (!['low', 'moderate', 'high'].includes(baseline)) {
        if (spinner) {
          spinner.fail(chalk.red('Invalid baseline. Must be: low, moderate, or high'));
        } else {
          console.error(chalk.red('Invalid baseline. Must be: low, moderate, or high'));
        }
        process.exit(1);
      }
      
      if (spinner && options.fetchControls) {
        spinner.text = 'Fetching control details from NIST catalog...';
      }
      
      const sspOptions: SSPOptions = {
        baseline: baseline as 'low' | 'moderate' | 'high',
        systemName,
        includeControlDetails: options.fetchControls
      };
      
      const ssp = generateSSP(sspOptions);
      
      const resolvedOutput = path.resolve(outputFile);
      fs.writeFileSync(resolvedOutput, JSON.stringify(ssp, null, 2));
      
      const controlCount = ssp['system-security-plan']['control-implementation']['implemented-requirements'].length;
      
      if (spinner) {
        spinner.succeed(chalk.green('SSP skeleton created successfully'));
        console.log(chalk.cyan(`\n✓ System: ${systemName}`));
        console.log(chalk.cyan(`✓ Baseline: ${baseline.toUpperCase()}`));
        console.log(chalk.cyan(`✓ Controls: ${controlCount}`));
        if (options.fetchControls) {
          console.log(chalk.cyan('✓ Control Details: Fetched from NIST catalog'));
        }
        console.log(chalk.cyan(`✓ UUID: ${ssp['system-security-plan'].uuid}`));
        console.log(chalk.cyan(`✓ Output: ${resolvedOutput}\n`));
        console.log(chalk.yellow('Next step: Run \'gh oscal scan .\' to populate implementation details'));
      } else {
        console.log(`Generated ${controlCount} controls to ${resolvedOutput}`);
      }
      
    } catch (error) {
      if (spinner) {
        spinner.fail(chalk.red('Failed to generate SSP'));
      } else {
        console.error(chalk.red('Failed to generate SSP'));
      }
      console.error(error);
      process.exit(1);
    }
  });
