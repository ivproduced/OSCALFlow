import { Command } from 'commander';
import fs from 'node:fs';
import path from 'node:path';
import chalk from 'chalk';
import ora from 'ora';
import { scanRepository, formatSignalsSummary } from '../lib/scanner.js';
import { updateSSPWithSignals } from '../lib/mapper.js';

export const scanCommand = new Command('scan')
  .description('Scan repository for compliance signals and update SSP')
  .argument('[path]', 'Repository path to scan', '.')
  .option('-u, --update <file>', 'SSP file to update with findings')
  .option('-o, --output <file>', 'Output file for scan results')
  .action(async (repoPath, options) => {
    const spinner = ora('Scanning repository for compliance signals...').start();
    
    try {
      // Resolve path
      const absolutePath = path.resolve(repoPath);
      
      if (!fs.existsSync(absolutePath)) {
        spinner.fail(chalk.red(`Path not found: ${absolutePath}`));
        process.exit(1);
      }
      
      // Scan repository
      const signals = await scanRepository(absolutePath);
      
      if (signals.length === 0) {
        spinner.warn(chalk.yellow('No compliance signals detected'));
        console.log(chalk.gray('\nTip: Add Dockerfile, CI/CD workflows, or security libraries to improve detection'));
        return;
      }
      
      spinner.succeed(chalk.green(`Found ${signals.length} compliance signal${signals.length !== 1 ? 's' : ''}`));
      
      // Calculate statistics
      const uniqueControls = new Set(signals.map(s => s.control));
      const controlFamilies = Array.from(uniqueControls).reduce((acc, control) => {
        const family = control.split('-')[0];
        acc[family] = (acc[family] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      
      const totalControls = 243; // MODERATE baseline
      const detectedCount = uniqueControls.size;
      const coveragePercent = ((detectedCount / totalControls) * 100).toFixed(1);
      const timeSaved = (detectedCount * 0.5).toFixed(1); // 30 min per control
      
      // Display summary dashboard
      console.log(chalk.cyan('\n📊 Coverage Summary:'));
      console.log(chalk.white(`   ├─ Total Controls (MODERATE): ${totalControls}`));
      console.log(chalk.green(`   ├─ Auto-Detected: ${detectedCount} (${coveragePercent}%)`));
      console.log(chalk.yellow(`   ├─ Needs Documentation: ${totalControls - detectedCount} (${(100 - parseFloat(coveragePercent)).toFixed(1)}%)`));
      console.log(chalk.magenta(`   └─ Time Saved: ~${timeSaved} hours\n`));
      
      // Display control families
      const sortedFamilies = Object.entries(controlFamilies)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
      
      if (sortedFamilies.length > 0) {
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
      
      // Display findings
      console.log(chalk.cyan('Compliance Signals Detected:\n'));
      console.log(formatSignalsSummary(signals));
      
      // Update SSP if requested
      if (options.update) {
        const updateSpinner = ora(`Updating ${options.update}...`).start();
        
        if (!fs.existsSync(options.update)) {
          updateSpinner.fail(chalk.red(`SSP file not found: ${options.update}`));
          console.log(chalk.yellow('\nTip: Run \'gh oscal generate\' first to create an SSP skeleton'));
          process.exit(1);
        }
        
        const ssp = JSON.parse(fs.readFileSync(options.update, 'utf-8'));
        const updatedSSP = updateSSPWithSignals(ssp, signals);
        
        fs.writeFileSync(options.update, JSON.stringify(updatedSSP, null, 2));
        
        // Count updated controls
        const uniqueControlsUpdated = new Set(signals.map(s => s.control));
        updateSpinner.succeed(chalk.green(`Updated ${uniqueControlsUpdated.size} control implementation${uniqueControlsUpdated.size !== 1 ? 's' : ''} in ${options.update}`));
      }
      
      // Save scan results if output specified
      if (options.output) {
        fs.writeFileSync(options.output, JSON.stringify(signals, null, 2));
        console.log(chalk.cyan(`\n✓ Scan results saved to: ${options.output}`));
      }
      
    } catch (error) {
      spinner.fail(chalk.red('Scan failed'));
      console.error(error);
      process.exit(1);
    }
  });
