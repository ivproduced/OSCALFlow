import { Command } from 'commander';
import fs from 'node:fs';
import chalk from 'chalk';
import ora from 'ora';
import { generateSSP, SSPOptions } from '../lib/oscal-writer.js';

export const generateCommand = new Command('generate')
  .description('Generate OSCAL SSP skeleton with baseline controls')
  .option('-b, --baseline <level>', 'Impact baseline (low|moderate|high)', 'moderate')
  .option('-s, --system <name>', 'System name', 'Unnamed System')
  .option('-o, --output <file>', 'Output file path', 'ssp-draft.json')
  .option('--fetch-controls', 'Fetch control details from NIST catalog', false)
  .action(async (options) => {
    const spinner = ora('Generating SSP skeleton...').start();
    
    try {
      // Validate baseline
      const baseline = options.baseline.toLowerCase();
      if (!['low', 'moderate', 'high'].includes(baseline)) {
        spinner.fail(chalk.red('Invalid baseline. Must be: low, moderate, or high'));
        process.exit(1);
      }
      
      if (options.fetchControls) {
        spinner.text = 'Fetching control details from NIST catalog...';
      }
      
      const sspOptions: SSPOptions = {
        baseline: baseline as 'low' | 'moderate' | 'high',
        systemName: options.system,
        includeControlDetails: options.fetchControls
      };
      
      const ssp = generateSSP(sspOptions);
      
      // Write to file
      fs.writeFileSync(options.output, JSON.stringify(ssp, null, 2));
      
      const controlCount = ssp['system-security-plan']['control-implementation']['implemented-requirements'].length;
      
      spinner.succeed(chalk.green('SSP skeleton created successfully'));
      console.log(chalk.cyan(`\n✓ System: ${options.system}`));
      console.log(chalk.cyan(`✓ Baseline: ${baseline.toUpperCase()}`));
      console.log(chalk.cyan(`✓ Controls: ${controlCount}`));
      if (options.fetchControls) {
        console.log(chalk.cyan(`✓ Control Details: Fetched from NIST catalog`));
      }
      console.log(chalk.cyan(`✓ UUID: ${ssp['system-security-plan'].uuid}`));
      console.log(chalk.cyan(`✓ Output: ${options.output}\n`));
      console.log(chalk.yellow('Next step: Run \'gh oscal scan .\' to populate implementation details'));
      
    } catch (error) {
      spinner.fail(chalk.red('Failed to generate SSP'));
      console.error(error);
      process.exit(1);
    }
  });
