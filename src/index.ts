#!/usr/bin/env node

import { program } from 'commander';
import { generateCommand } from './commands/generate.js';
import { scanCommand } from './commands/scan.js';
import { ingestCommand } from './commands/ingest.js';
import { validateCommand } from './commands/validate.js';
import { explainCommand } from './commands/explain.js';
import { exportCommand } from './commands/export.js';
import { doctorCommand } from './commands/doctor.js';
import { suggestCommand } from './commands/suggest.js';

program
  .name('gh-oscal')
  .description('GitHub CLI extension for OSCAL compliance automation')
  .version('1.1.0');

program.addCommand(generateCommand);
program.addCommand(scanCommand);
program.addCommand(ingestCommand);
program.addCommand(validateCommand);
program.addCommand(explainCommand);
program.addCommand(exportCommand);
program.addCommand(doctorCommand);
program.addCommand(suggestCommand);

program.parse();
