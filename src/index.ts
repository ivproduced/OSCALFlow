#!/usr/bin/env node

import { program } from 'commander';
import { generateCommand } from './commands/generate.js';
import { scanCommand } from './commands/scan.js';
import { explainCommand } from './commands/explain.js';
import { exportCommand } from './commands/export.js';
import { doctorCommand } from './commands/doctor.js';

program
  .name('gh-oscal')
  .description('GitHub CLI extension for OSCAL compliance automation')
  .version('1.1.0');

program.addCommand(generateCommand);
program.addCommand(scanCommand);
program.addCommand(explainCommand);
program.addCommand(exportCommand);
program.addCommand(doctorCommand);

program.parse();
