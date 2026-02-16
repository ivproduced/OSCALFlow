import { Command } from 'commander';
import fs from 'node:fs';
import path from 'node:path';
import chalk from 'chalk';
import ora from 'ora';
import type { Ora } from 'ora';
import {
  scanRepository,
  formatSignalsSummary,
  formatSignalsSummaryWithValidation,
  filterSignalsByDetectors,
  DETECTOR_NAMES,
  type DetectorName,
  type ComplianceSignal
} from '../lib/scanner.js';
import { updateSSPWithSignals } from '../lib/mapper.js';
import { loadOscalFlowConfig, parseDetectorList } from '../lib/config.js';
import { printWithOptionalPager } from '../lib/output.js';
import { validateControlImplementation, type ValidationResult } from '../lib/ai-validator.js';

export const scanCommand = new Command('scan')
  .description('Scan repository for compliance signals and update SSP')
  .argument('[path]', 'Repository path to scan', '.')
  .option('-u, --update <file>', 'SSP file to update with findings')
  .option('-o, --output <file>', 'Output file for scan results')
  .option('--enable <detectors>', `Comma-separated detectors to enable (${DETECTOR_NAMES.join(', ')})`)
  .option('--disable <detectors>', `Comma-separated detectors to disable (${DETECTOR_NAMES.join(', ')})`)
  .option('-q, --quiet', 'Reduce console output')
  .option('--no-tips', 'Suppress tips and guidance text')
  .option('--pager', 'Show summary using pager (less)')
  .option('--ai-validate', 'Use AI (Copilot CLI) to validate control implementations against OSCAL requirements')
  .option('--ai-limit <number>', 'Limit the number of controls to AI validate (useful for testing)', parseInt)
  .action(async (repoPath, options) => {
    const absolutePath = path.resolve(repoPath);
    const { config } = loadOscalFlowConfig(absolutePath);
    const quiet = Boolean(options.quiet || config.quiet);
    const showTips = options.tips && !config.suppressTips;
    const usePager = Boolean(options.pager || config.pager);
    const enabledDetectors: DetectorName[] = Array.from(
      new Set<DetectorName>([...(config.enabledDetectors ?? []), ...parseDetectorList(options.enable)])
    );
    const disabledDetectors: DetectorName[] = Array.from(
      new Set<DetectorName>([...(config.disabledDetectors ?? []), ...parseDetectorList(options.disable)])
    );

    const outputPath = options.output ?? config.scanOutput;
    let spinner: Ora | null = null;

    if (!quiet) {
      spinner = ora('Scanning repository for compliance signals...').start();
    }
    
    try {
      if (!fs.existsSync(absolutePath)) {
        if (spinner) {
          spinner.fail(chalk.red(`Path not found: ${absolutePath}`));
        } else {
          console.error(chalk.red(`Path not found: ${absolutePath}`));
        }
        process.exit(1);
      }
      
      let signals = await scanRepository(absolutePath);
      signals = filterSignalsByDetectors(signals, enabledDetectors, disabledDetectors);
      
      if (signals.length === 0) {
        if (spinner) {
          spinner.warn(chalk.yellow('No compliance signals detected'));
        } else {
          console.log(chalk.yellow('No compliance signals detected'));
        }

        if (showTips && !quiet) {
          console.log(chalk.gray('\nTip: Add Dockerfile, CI/CD workflows, or security libraries to improve detection'));
        }
        return;
      }
      
      if (spinner) {
        spinner.succeed(chalk.green(`Found ${signals.length} compliance signal${signals.length !== 1 ? 's' : ''}`));
      }
      
      // AI Validation Phase (if enabled)
      let validationResults: Map<string, ValidationResult> = new Map();
      if (options.aiValidate) {
        const validationSpinner = quiet ? null : ora('AI validating control implementations...').start();
        
        try {
          // Get unique control-file pairs
          const uniqueValidations = new Map<string, ComplianceSignal>();
          for (const signal of signals) {
            const key = `${signal.control}:${signal.file}`;
            if (!uniqueValidations.has(key)) {
              uniqueValidations.set(key, signal);
            }
          }
          
          // Apply limit if specified
          const validationsToProcess = options.aiLimit 
            ? Array.from(uniqueValidations.entries()).slice(0, options.aiLimit)
            : Array.from(uniqueValidations.entries());
          
          if (validationSpinner) {
            validationSpinner.text = `AI validating ${validationsToProcess.length} control implementations...`;
          }
          
          // Validate each control (sequentially to avoid overwhelming Copilot CLI)
          let validated = 0;
          for (const [key, signal] of validationsToProcess) {
            const result = await validateControlImplementation(signal.control, signal.file, absolutePath);
            validationResults.set(key, result);
            validated++;
            
            if (validationSpinner && !quiet) {
              validationSpinner.text = `AI validated ${validated}/${validationsToProcess.length} controls...`;
            }
          }
          
          if (validationSpinner) {
            const verifiedCount = Array.from(validationResults.values()).filter(r => r.validated).length;
            const totalMsg = options.aiLimit ? `${verifiedCount}/${validationsToProcess.length} (limited from ${uniqueValidations.size})` : `${verifiedCount}/${validationsToProcess.length}`;
            validationSpinner.succeed(chalk.green(`AI Validation: ${totalMsg} controls verified`));
          }
        } catch (error) {
          if (validationSpinner) {
            validationSpinner.fail(chalk.red(`AI validation error: ${error instanceof Error ? error.message : String(error)}`));
          }
          if (!quiet) {
            console.log(chalk.yellow('⚠️  Continuing with pattern-based detection only'));
          }
        }
      }
      
      const uniqueControls = new Set(signals.map(s => s.control));
      const controlFamilies = Array.from(uniqueControls).reduce((acc, control) => {
        const family = control.split('-')[0];
        acc[family] = (acc[family] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      
      const totalControls = 243; // MODERATE baseline
      const detectedCount = uniqueControls.size;
      const coveragePercent = ((detectedCount / totalControls) * 100).toFixed(1);
      const timeSaved = (detectedCount * 0.5).toFixed(1);
      
      if (!quiet) {
        console.log(chalk.cyan('\n📊 Coverage Summary:'));
        console.log(chalk.white(`   ├─ Total Controls (MODERATE): ${totalControls}`));
        console.log(chalk.green(`   ├─ Auto-Detected: ${detectedCount} (${coveragePercent}%)`));
        console.log(chalk.yellow(`   ├─ Needs Documentation: ${totalControls - detectedCount} (${(100 - parseFloat(coveragePercent)).toFixed(1)}%)`));
        console.log(chalk.magenta(`   └─ Time Saved: ~${timeSaved} hours\n`));
      }
      
      const sortedFamilies = Object.entries(controlFamilies)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
      
      if (!quiet && sortedFamilies.length > 0) {
        console.log(chalk.cyan('🏆 Top Control Families Detected:'));
        sortedFamilies.forEach(([family, count], idx) => {
          const familyNames: Record<string, string> = {
            'AC': 'Access Control',
            'AU': 'Audit & Accountability',
            'SC': 'System & Communications',
            'IA': 'Identification & Authentication',
            'SI': 'System & Information Integrity',
            'CM': 'Configuration Management',
            'CA': 'Assessment & Authorization',
            'RA': 'Risk Assessment',
            'SA': 'System & Services Acquisition',
            'PL': 'Planning',
            'AP': 'Privacy'
          };
          const isLast = idx === sortedFamilies.length - 1;
          const prefix = isLast ? '   └─' : '   ├─';
          console.log(chalk.white(`${prefix} ${familyNames[family] || family} (${family}): ${count} control${count !== 1 ? 's' : ''}`));
        });
        console.log('');
      }

      if (!quiet) {
        let summaryText: string;
        
        if (options.aiValidate && validationResults.size > 0) {
          summaryText = `${chalk.cyan('Compliance Signals Detected (with AI Validation):\n')}\n${formatSignalsSummaryWithValidation(signals, validationResults)}`;
        } else {
          summaryText = `${chalk.cyan('Compliance Signals Detected:\n')}\n${formatSignalsSummary(signals)}`;
        }
        
        printWithOptionalPager(summaryText, usePager);
      } else {
        console.log(`Detected ${detectedCount} controls (${coveragePercent}% of MODERATE baseline)`);
      }
      
      if (options.update) {
        const updateSpinner = quiet ? null : ora(`Updating ${options.update}...`).start();
        
        if (!fs.existsSync(options.update)) {
          if (updateSpinner) {
            updateSpinner.fail(chalk.red(`SSP file not found: ${options.update}`));
          } else {
            console.error(chalk.red(`SSP file not found: ${options.update}`));
          }

          if (showTips && !quiet) {
            console.log(chalk.yellow('\nTip: Run \'gh oscal generate\' first to create an SSP skeleton'));
          }
          process.exit(1);
        }
        
        const ssp = JSON.parse(fs.readFileSync(options.update, 'utf-8'));
        const updatedSSP = updateSSPWithSignals(ssp, signals);
        
        fs.writeFileSync(options.update, JSON.stringify(updatedSSP, null, 2));
        
        const uniqueControlsUpdated = new Set(signals.map(s => s.control));
        const updateMessage = `Updated ${uniqueControlsUpdated.size} control implementation${uniqueControlsUpdated.size !== 1 ? 's' : ''} in ${options.update}`;
        if (updateSpinner) {
          updateSpinner.succeed(chalk.green(updateMessage));
        } else {
          console.log(chalk.green(updateMessage));
        }
      }
      
      if (outputPath) {
        fs.writeFileSync(outputPath, JSON.stringify(signals, null, 2));
        if (!quiet) {
          console.log(chalk.cyan(`\n✓ Scan results saved to: ${outputPath}`));
        }
      }

      if (!quiet && (enabledDetectors.length > 0 || disabledDetectors.length > 0)) {
        console.log(chalk.gray('\nDetector filters applied:'));
        if (enabledDetectors.length > 0) {
          console.log(chalk.gray(`  enabled: ${enabledDetectors.join(', ')}`));
        }
        if (disabledDetectors.length > 0) {
          console.log(chalk.gray(`  disabled: ${disabledDetectors.join(', ')}`));
        }
      }
      
    } catch (error) {
      if (spinner) {
        spinner.fail(chalk.red('Scan failed'));
      } else {
        console.error(chalk.red('Scan failed'));
      }
      console.error(error);
      process.exit(1);
    }
  });
