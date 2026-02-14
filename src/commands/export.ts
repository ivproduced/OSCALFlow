import { Command } from 'commander';
import fs from 'node:fs';
import path from 'node:path';
import chalk from 'chalk';
import ora from 'ora';
import { generateHTMLReport } from '../lib/html-export.js';

export const exportCommand = new Command('export')
  .description('Export SSP to HTML report')
  .argument('<ssp-file>', 'OSCAL SSP JSON file to export')
  .option('-o, --output <file>', 'Output HTML file', 'ssp-report.html')
  .action(async (sspFile, options) => {
    const spinner = ora('Generating HTML report...').start();
    
    try {
      // Validate input file
      if (!fs.existsSync(sspFile)) {
        spinner.fail(chalk.red(`SSP file not found: ${sspFile}`));
        process.exit(1);
      }
      
      // Generate HTML report
      const outputPath = path.resolve(options.output);
      generateHTMLReport(sspFile, outputPath);
      
      spinner.succeed(chalk.green('HTML report generated'));
      
      console.log(chalk.cyan('\n✓ Report saved to:'), chalk.white(outputPath));
      console.log(chalk.gray('\nOpen in browser:'), chalk.blue(`file://${outputPath}`));
      
    } catch (error) {
      spinner.fail(chalk.red('Export failed'));
      console.error(error);
      process.exit(1);
    }
  });
