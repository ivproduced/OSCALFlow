import { Command } from 'commander';
import fs from 'node:fs';
import path from 'node:path';
import chalk from 'chalk';
import ora from 'ora';

interface ValidationError {
  path: string;
  message: string;
}

function validateOscalSSP(ssp: any): ValidationError[] {
  const errors: ValidationError[] = [];

  function check(condition: boolean, errorPath: string, message: string) {
    if (!condition) {
      errors.push({ path: errorPath, message });
    }
  }

  const root = ssp?.['system-security-plan'];
  check(Boolean(root), 'system-security-plan', 'Root element "system-security-plan" is missing');
  if (!root) {
    return errors;
  }

  const metadata = root.metadata;
  check(Boolean(metadata), 'system-security-plan.metadata', 'metadata is required');
  if (metadata) {
    check(typeof metadata.title === 'string' && metadata.title.length > 0, 'metadata.title', 'title must be a non-empty string');
    check(typeof metadata['last-modified'] === 'string', 'metadata.last-modified', 'last-modified must be an ISO 8601 string');
    check(typeof metadata['oscal-version'] === 'string', 'metadata.oscal-version', 'oscal-version is required');
    check(Array.isArray(metadata.parties), 'metadata.parties', 'parties must be an array');
    if (Array.isArray(metadata.parties)) {
      metadata.parties.forEach((party: any, index: number) => {
        check(typeof party.uuid === 'string', `metadata.parties[${index}].uuid`, 'party uuid is required');
        check(party.type === 'organization' || party.type === 'person', `metadata.parties[${index}].type`, 'party type must be "organization" or "person"');
      });
    }
  }

  const systemCharacteristics = root['system-characteristics'];
  check(Boolean(systemCharacteristics), 'system-security-plan.system-characteristics', 'system-characteristics is required');
  if (systemCharacteristics) {
    check(
      typeof systemCharacteristics['system-name'] === 'string' && systemCharacteristics['system-name'].length > 0,
      'system-characteristics.system-name',
      'system-name is required'
    );
    const validLevels = ['LOW', 'MODERATE', 'HIGH'];
    check(
      validLevels.includes(systemCharacteristics['security-sensitivity-level']),
      'system-characteristics.security-sensitivity-level',
      `security-sensitivity-level must be one of: ${validLevels.join(', ')}`
    );
    const securityImpactLevel = systemCharacteristics['security-impact-level'];
    check(Boolean(securityImpactLevel), 'system-characteristics.security-impact-level', 'security-impact-level is required');
    if (securityImpactLevel) {
      const validImpacts = ['low', 'moderate', 'high'];
      ['security-objective-confidentiality', 'security-objective-integrity', 'security-objective-availability'].forEach((field) => {
        check(
          validImpacts.includes(securityImpactLevel[field]),
          `security-impact-level.${field}`,
          `${field} must be one of: ${validImpacts.join(', ')}`
        );
      });
    }
    check(Boolean(systemCharacteristics['authorization-boundary']), 'system-characteristics.authorization-boundary', 'authorization-boundary is required');
  }

  const systemImplementation = root['system-implementation'];
  check(Boolean(systemImplementation), 'system-security-plan.system-implementation', 'system-implementation is required');
  if (systemImplementation) {
    check(Array.isArray(systemImplementation.users), 'system-implementation.users', 'users must be an array');
    check(Array.isArray(systemImplementation.components), 'system-implementation.components', 'components must be an array');
    if (Array.isArray(systemImplementation.components)) {
      systemImplementation.components.forEach((component: any, index: number) => {
        check(typeof component.uuid === 'string', `system-implementation.components[${index}].uuid`, 'component uuid is required');
        check(typeof component.type === 'string', `system-implementation.components[${index}].type`, 'component type is required');
        check(typeof component.title === 'string', `system-implementation.components[${index}].title`, 'component title is required');
        check(Boolean(component.status?.state), `system-implementation.components[${index}].status.state`, 'component status.state is required');
      });
    }
  }

  const controlImplementation = root['control-implementation'];
  check(Boolean(controlImplementation), 'system-security-plan.control-implementation', 'control-implementation is required');
  if (controlImplementation) {
    check(
      Array.isArray(controlImplementation['implemented-requirements']),
      'control-implementation.implemented-requirements',
      'implemented-requirements must be an array'
    );
    if (Array.isArray(controlImplementation['implemented-requirements'])) {
      const requirements = controlImplementation['implemented-requirements'];
      check(requirements.length > 0, 'control-implementation.implemented-requirements', 'at least one implemented-requirement is required');
      requirements.forEach((requirement: any, index: number) => {
        check(typeof requirement.uuid === 'string', `implemented-requirements[${index}].uuid`, 'requirement uuid is required');
        check(typeof requirement['control-id'] === 'string', `implemented-requirements[${index}].control-id`, 'control-id is required');
        check(typeof requirement.description === 'string', `implemented-requirements[${index}].description`, 'description is required');
      });
    }
  }

  return errors;
}

function countWarnings(ssp: any): string[] {
  const warnings: string[] = [];
  const root = ssp?.['system-security-plan'];
  if (!root) {
    return warnings;
  }

  const metadata = root.metadata;
  if (metadata && !metadata.published) {
    warnings.push('metadata.published: not set (recommended for formal SSPs)');
  }
  if (metadata && !metadata['revision-history']) {
    warnings.push('metadata.revision-history: not present (recommended for audit trail)');
  }

  const controlImplementation = root['control-implementation'];
  if (controlImplementation && Array.isArray(controlImplementation['implemented-requirements'])) {
    const requirements = controlImplementation['implemented-requirements'];
    const withoutStatements = requirements.filter((requirement: any) => !requirement.statements || requirement.statements.length === 0).length;
    if (withoutStatements > 0) {
      warnings.push(`${withoutStatements} controls have no implementation statements (run 'gh oscal scan . --update <ssp>' to populate)`);
    }

    const withoutComponents = requirements.filter((requirement: any) =>
      requirement.statements?.some((statement: any) => !statement['by-components'] || statement['by-components'].length === 0)
    ).length;
    if (withoutComponents > 0) {
      warnings.push(`${withoutComponents} controls have statements missing by-components (affects FedRAMP/FISMA traceability)`);
    }

    const withoutOrigination = requirements.filter((requirement: any) =>
      requirement.statements?.some((statement: any) =>
        statement['by-components']?.some((byComponent: any) => !byComponent.props?.some((prop: any) => prop.name === 'control-origination'))
      )
    ).length;
    if (withoutOrigination > 0) {
      warnings.push(`${withoutOrigination} controls are missing control-origination (required for federal authorization)`);
    }
  }

  const systemImplementation = root['system-implementation'];
  if (systemImplementation && Array.isArray(systemImplementation.components) && systemImplementation.components.length === 0) {
    warnings.push('system-implementation.components is empty — add components for federal-grade SSPs');
  }

  if (!root['import-profile']) {
    warnings.push('import-profile not set — link to the NIST baseline profile used for this SSP');
  }

  return warnings;
}

export const validateCommand = new Command('validate')
  .description('Validate an OSCAL SSP file against the OSCAL 1.2.0 schema')
  .argument('<ssp-file>', 'Path to OSCAL SSP JSON file')
  .option('-q, --quiet', 'Only show errors, no summary')
  .action((sspFile, options) => {
    const quiet = Boolean(options.quiet);
    const sspPath = path.resolve(sspFile);

    if (!fs.existsSync(sspPath)) {
      console.error(chalk.red(`File not found: ${sspPath}`));
      process.exit(1);
    }

    const spinner = quiet ? null : ora(`Validating ${path.basename(sspPath)}...`).start();

    let ssp: any;
    try {
      ssp = JSON.parse(fs.readFileSync(sspPath, 'utf-8'));
    } catch (error) {
      if (spinner) {
        spinner.fail(chalk.red('Failed to parse JSON'));
      }
      console.error(chalk.red(`JSON parse error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }

    const errors = validateOscalSSP(ssp);
    const warnings = countWarnings(ssp);

    if (errors.length === 0) {
      if (spinner) {
        spinner.succeed(chalk.green(`Valid OSCAL SSP: ${path.basename(sspPath)}`));
      }
    } else if (spinner) {
      spinner.fail(chalk.red(`Invalid SSP: ${errors.length} error${errors.length !== 1 ? 's' : ''} found`));
    }

    if (!quiet || errors.length > 0) {
      if (errors.length > 0) {
        console.log(chalk.red('\n❌ Validation Errors:'));
        errors.forEach((error) => {
          console.log(chalk.red(`   • [${error.path}] ${error.message}`));
        });
      }

      if (warnings.length > 0 && !quiet) {
        console.log(chalk.yellow('\n⚠  Advisories (not blocking, but address before ATO submission):'));
        warnings.forEach((warning) => {
          console.log(chalk.yellow(`   • ${warning}`));
        });
      }

      if (errors.length === 0 && !quiet) {
        console.log(chalk.green('\n✓ SSP structure is valid.'));
        if (warnings.length === 0) {
          console.log(chalk.green('✓ No advisories. SSP is well-formed for federal use.\n'));
        } else {
          console.log(chalk.gray(`\n  Address ${warnings.length} advisor${warnings.length !== 1 ? 'ies' : 'y'} before ATO submission.\n`));
        }
      }
    }

    process.exit(errors.length > 0 ? 1 : 0);
  });
