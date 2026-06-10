import { Command } from 'commander';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import chalk from 'chalk';
import ora from 'ora';

interface ControlInfo {
  id: string;
  title: string;
  description: string;
  developerGuidance: string;
  examples: string[];
}

// NIST 800-53 Rev 5 control database (subset for demo)
const CONTROL_DATABASE: Record<string, ControlInfo> = {
  'AC-1': {
    id: 'AC-1',
    title: 'Policy and Procedures',
    description: 'Develop, document, and disseminate access control policy and procedures.',
    developerGuidance: 'Document your access control policies in your README or SECURITY.md file. Include who can access what and how.',
    examples: [
      'Create a SECURITY.md file documenting authentication requirements',
      'Maintain an access control matrix in your documentation',
      'Use GitHub team permissions to enforce role-based access'
    ]
  },
  'AC-2': {
    id: 'AC-2',
    title: 'Account Management',
    description: 'Manage system accounts including creation, enablement, modification, disabling, and removal.',
    developerGuidance: 'Implement proper user lifecycle management with audit logging for all account operations.',
    examples: [
      'Log user creation/deletion events with timestamps',
      'Implement RBAC using OAuth scopes or JWT claims',
      'Auto-disable accounts after 90 days of inactivity',
      'Use GitHub Teams or LDAP for centralized account management'
    ]
  },
  'AC-3': {
    id: 'AC-3',
    title: 'Access Enforcement',
    description: 'Enforce approved authorizations for logical access.',
    developerGuidance: 'Check user permissions before allowing any operation. Use middleware or decorators.',
    examples: [
      'Implement authorization middleware in Express.js',
      'Use decorators like @RequireRole("admin") in your API',
      'Check permissions at both API and database levels',
      'Example: if (!user.hasPermission("delete")) { throw new ForbiddenError(); }'
    ]
  },
  'AU-2': {
    id: 'AU-2',
    title: 'Event Logging',
    description: 'Identify the types of events the system is capable of logging.',
    developerGuidance: 'Use structured logging (JSON) and log security-relevant events.',
    examples: [
      'Use Winston, Pino, or similar structured logging library',
      'Log: authentication attempts, authorization failures, data access, config changes',
      'Include: timestamp, user ID, action, resource, outcome, source IP',
      'Example: logger.info({ event: "login", userId, ip, success: true })'
    ]
  },
  'CM-2': {
    id: 'CM-2',
    title: 'Baseline Configuration',
    description: 'Develop, document, and maintain baseline configurations.',
    developerGuidance: 'Use Infrastructure as Code to define your system\'s baseline configuration.',
    examples: [
      'Define infrastructure in Terraform or CloudFormation',
      'Use Docker for reproducible environments',
      'Store configuration in version control',
      'Document minimum required dependencies and versions'
    ]
  },
  'CM-3': {
    id: 'CM-3',
    title: 'Configuration Change Control',
    description: 'Determine and approve changes to the system.',
    developerGuidance: 'Use CI/CD pipelines and pull request reviews to control changes.',
    examples: [
      'Require pull request reviews before merging',
      'Use GitHub Actions for automated testing',
      'Implement branch protection rules',
      'Run security scans (Snyk, SonarQube) in CI pipeline'
    ]
  },
  'IA-2': {
    id: 'IA-2',
    title: 'Identification and Authentication',
    description: 'Uniquely identify and authenticate users.',
    developerGuidance: 'Implement proper authentication with secure session management.',
    examples: [
      'Use JWT or session tokens',
      'Implement OAuth2/OIDC for third-party authentication',
      'Use Passport.js or similar authentication middleware',
      'Store tokens securely (httpOnly cookies, not localStorage)'
    ]
  },
  'IA-5': {
    id: 'IA-5',
    title: 'Authenticator Management',
    description: 'Manage system authenticators including passwords.',
    developerGuidance: 'Never store passwords in plain text. Use strong hashing algorithms.',
    examples: [
      'Use bcrypt or Argon2 for password hashing',
      'Enforce password complexity requirements',
      'Implement multi-factor authentication',
      'Example: const hash = await bcrypt.hash(password, 12);'
    ]
  },
  'RA-5': {
    id: 'RA-5',
    title: 'Vulnerability Monitoring and Scanning',
    description: 'Monitor and scan for vulnerabilities in the system.',
    developerGuidance: 'Use automated tools to continuously scan for vulnerabilities.',
    examples: [
      'Enable Dependabot for dependency scanning',
      'Use Snyk, WhiteSource, or similar tools',
      'Run npm audit or pip-audit regularly',
      'Set up GitHub security alerts'
    ]
  },
  'SA-11': {
    id: 'SA-11',
    title: 'Developer Testing and Evaluation',
    description: 'Require testing and evaluation during development.',
    developerGuidance: 'Implement comprehensive testing including security tests.',
    examples: [
      'Write unit tests with Jest, Pytest, etc.',
      'Include integration tests in CI pipeline',
      'Use tools like OWASP ZAP for security testing',
      'Achieve >80% code coverage'
    ]
  },
  'SC-2': {
    id: 'SC-2',
    title: 'Separation of System and User Functionality',
    description: 'Separate user functionality from system management functionality.',
    developerGuidance: 'Use separate services/containers for different system components.',
    examples: [
      'Run frontend, backend, and database in separate containers',
      'Use Kubernetes namespaces for separation',
      'Implement microservices architecture',
      'Separate admin interfaces from user interfaces'
    ]
  },
  'SC-7': {
    id: 'SC-7',
    title: 'Boundary Protection',
    description: 'Monitor and control communications at external system boundaries.',
    developerGuidance: 'Use firewalls, API gateways, and network segmentation.',
    examples: [
      'Configure security groups in AWS/Azure',
      'Use API Gateway for external access',
      'Implement rate limiting and DDoS protection',
      'Use VPC/VNET for network isolation'
    ]
  },
  'SC-8': {
    id: 'SC-8',
    title: 'Transmission Confidentiality and Integrity',
    description: 'Protect the confidentiality and integrity of transmitted information.',
    developerGuidance: 'Always use HTTPS/TLS for data in transit.',
    examples: [
      'Enforce HTTPS with HSTS headers',
      'Use Helmet.js for security headers',
      'Configure TLS 1.2+ only',
      'Example: app.use(helmet()); in Express.js'
    ]
  },
  'SC-12': {
    id: 'SC-12',
    title: 'Cryptographic Key Establishment and Management',
    description: 'Establish and manage cryptographic keys.',
    developerGuidance: 'Store secrets securely and rotate them regularly.',
    examples: [
      'Use AWS Secrets Manager or HashiCorp Vault',
      'Store keys in environment variables, never in code',
      'Use .env files locally, secrets management in production',
      'Rotate API keys and tokens regularly'
    ]
  },
  'SC-13': {
    id: 'SC-13',
    title: 'Cryptographic Protection',
    description: 'Implement FIPS-validated cryptography.',
    developerGuidance: 'Use well-established cryptographic libraries.',
    examples: [
      'Use Node.js crypto module for cryptographic operations',
      'Use AES-256 for encryption at rest',
      'Use TLS 1.2+ for transport encryption',
      'Avoid implementing custom crypto algorithms'
    ]
  },
  'SC-39': {
    id: 'SC-39',
    title: 'Process Isolation',
    description: 'Maintain separate execution domains for each executing process.',
    developerGuidance: 'Use containers or virtualization for process isolation.',
    examples: [
      'Use Docker containers for application isolation',
      'Run each service in its own container',
      'Use security contexts in Kubernetes',
      'Example: docker run --security-opt=no-new-privileges'
    ]
  },
  'SI-2': {
    id: 'SI-2',
    title: 'Flaw Remediation',
    description: 'Identify, report, and correct system flaws.',
    developerGuidance: 'Keep dependencies updated and patch vulnerabilities quickly.',
    examples: [
      'Enable automated dependency updates with Dependabot',
      'Review and merge security patches within 30 days',
      'Subscribe to security advisories for your dependencies',
      'Run npm update or pip install --upgrade regularly'
    ]
  }
};

function getControlInfo(controlId: string): ControlInfo | null {
  const baseControl = controlId.split('(')[0]; // Handle enhancements like AC-2(1)
  return CONTROL_DATABASE[baseControl] || null;
}

function getCodebaseContext(repoPath: string): string {
  const context: string[] = [];
  
  // Detect languages
  const languages: string[] = [];
  if (fs.existsSync(path.join(repoPath, 'package.json'))) languages.push('JavaScript/TypeScript/Node.js');
  if (fs.existsSync(path.join(repoPath, 'requirements.txt')) || fs.existsSync(path.join(repoPath, 'setup.py'))) languages.push('Python');
  if (fs.existsSync(path.join(repoPath, 'go.mod'))) languages.push('Go');
  if (fs.existsSync(path.join(repoPath, 'Cargo.toml'))) languages.push('Rust');
  if (fs.existsSync(path.join(repoPath, 'pom.xml')) || fs.existsSync(path.join(repoPath, 'build.gradle'))) languages.push('Java');
  if (fs.existsSync(path.join(repoPath, 'Gemfile'))) languages.push('Ruby');
  
  if (languages.length > 0) {
    context.push(`Languages: ${languages.join(', ')}`);
  }
  
  // Detect frameworks
  try {
    if (fs.existsSync(path.join(repoPath, 'package.json'))) {
      const pkg = JSON.parse(fs.readFileSync(path.join(repoPath, 'package.json'), 'utf-8'));
      const deps = { ...pkg.dependencies, ...pkg.devDependencies };
      const frameworks: string[] = [];
      
      if (deps.express) frameworks.push('Express.js');
      if (deps.react) frameworks.push('React');
      if (deps.vue) frameworks.push('Vue');
      if (deps.angular || deps['@angular/core']) frameworks.push('Angular');
      if (deps.next) frameworks.push('Next.js');
      if (deps.fastify) frameworks.push('Fastify');
      if (deps.nest || deps['@nestjs/core']) frameworks.push('NestJS');
      
      if (frameworks.length > 0) {
        context.push(`Frameworks: ${frameworks.join(', ')}`);
      }
    }
  } catch (e) {
    // Ignore parsing errors
  }
  
  // Detect infrastructure
  const infra: string[] = [];
  if (fs.existsSync(path.join(repoPath, 'Dockerfile'))) infra.push('Docker');
  if (fs.existsSync(path.join(repoPath, 'docker-compose.yml'))) infra.push('Docker Compose');
  if (fs.existsSync(path.join(repoPath, 'kubernetes')) || fs.existsSync(path.join(repoPath, 'k8s'))) infra.push('Kubernetes');
  if (fs.existsSync(path.join(repoPath, 'terraform'))) infra.push('Terraform');
  if (fs.existsSync(path.join(repoPath, '.github/workflows'))) infra.push('GitHub Actions');
  
  if (infra.length > 0) {
    context.push(`Infrastructure: ${infra.join(', ')}`);
  }
  
  return context.length > 0 ? context.join('\n') : 'General codebase';
}

function buildPrompt(control: ControlInfo, repoPath: string): string {
  const codebaseContext = getCodebaseContext(repoPath);
  const examples = control.examples.map((ex, idx) => `  ${idx + 1}. ${ex}`).join('\n');
  
  return `Analyze this codebase and suggest specific implementation steps for NIST 800-53 control ${control.id} (${control.title}).

CONTROL DETAILS:
Description: ${control.description}
Guidance: ${control.developerGuidance}

CODEBASE CONTEXT:
${codebaseContext}

EXAMPLE IMPLEMENTATIONS:
${examples}

Please provide:
1. Specific files to create or modify in this codebase
2. Code snippets or commands to run
3. Dependencies to add (with installation commands)
4. Configuration changes needed
5. Any architectural or structural recommendations

Focus on practical, actionable steps that fit this project's tech stack and structure.`;
}

export const suggestCommand = new Command('suggest')
  .description('Get AI-powered implementation suggestions for a NIST control based on your codebase')
  .argument('<control-id>', 'Control ID (e.g., AC-2, SC-8)')
  .argument('[path]', 'Repository path to analyze', '.')
  .option('--no-context', 'Skip showing control info before suggestions')
  .option('-o, --output <file>', 'Save Copilot session to markdown file')
  .action(async (controlId, repoPath, options) => {
    try {
      const absolutePath = path.resolve(repoPath);
      
      if (!fs.existsSync(absolutePath)) {
        console.log(chalk.red(`\n✗ Path not found: ${absolutePath}`));
        process.exit(1);
      }
      
      const control = getControlInfo(controlId.toUpperCase());
      
      if (!control) {
        console.log(chalk.red(`\n✗ Control ${controlId} not found in database`));
        console.log(chalk.yellow('\nAvailable controls:'));
        console.log(Object.keys(CONTROL_DATABASE).join(', '));
        console.log(chalk.gray('\nNote: This demo includes commonly-used controls. Full NIST 800-53 has 1000+ controls.'));
        process.exit(1);
      }

      // Show control context unless --no-context
      if (options.context) {
        console.log(chalk.cyan('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'));
        console.log(chalk.bold.white(`${control.id}: ${control.title}`));
        console.log(chalk.cyan('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'));
        console.log(chalk.gray(control.description));
        console.log(chalk.yellow('💡 ' + control.developerGuidance + '\n'));
      }

      const spinner = ora('Analyzing codebase and preparing prompt...').start();

      // Check if gh copilot is available
      try {
        const check = spawnSync('gh', ['copilot', '--version'], { stdio: 'pipe' });
        if (check.status !== 0) throw new Error();
      } catch (error) {
        spinner.fail(chalk.red('GitHub CLI with Copilot extension is not installed'));
        console.log(chalk.yellow('\nTo install:'));
        console.log(chalk.white('  1. Install GitHub CLI: https://cli.github.com/'));
        console.log(chalk.white('  2. Install Copilot extension: gh extension install github/gh-copilot'));
        console.log(chalk.white('  3. Authenticate: gh auth login'));
        process.exit(1);
      }

      const prompt = buildPrompt(control, absolutePath);
      
      spinner.stop();
      console.log(chalk.cyan('🤖 Getting implementation suggestions from GitHub Copilot CLI...\n'));
      console.log(chalk.gray('───────────────────────────────────────────────────\n'));
      
      // Build args array — no shell string, no escaping needed
      const copilotArgs = ['copilot', '--', '-p', prompt, '--allow-all-tools'];
      if (options.output) {
        const outputPath = path.resolve(options.output);
        copilotArgs.push('--share', outputPath);
        console.log(chalk.gray(`💾 Saving session to: ${outputPath}\n`));
      }
      
      const result = spawnSync('gh', copilotArgs, {
        stdio: 'inherit',
        cwd: absolutePath
      });

      if (result.status !== null && result.status !== 0 && result.status !== 130) {
        console.error(chalk.red('\n✗ Failed to get suggestions from GitHub Copilot'));
        if (result.stderr) console.error(chalk.gray(result.stderr.toString()));
        process.exit(1);
      }
      
      console.log(chalk.gray('\n───────────────────────────────────────────────────'));
      
      if (options.output) {
        const outputPath = path.resolve(options.output);
        if (fs.existsSync(outputPath)) {
          console.log(chalk.green(`\n✓ Recommendations saved to: ${outputPath}`));
        }
      }
      
      console.log(chalk.cyan('\n💡 Next steps:'));
      console.log(chalk.white(`  • Run 'gh oscal explain ${control.id}' for more control details`));
      console.log(chalk.white(`  • Run 'gh oscal scan ${repoPath === '.' ? '.' : repoPath}' to verify implementation`));
      console.log(chalk.white(`  • Run 'gh oscal generate' to update your SSP with new implementations\n`));
      
    } catch (error) {
      console.error(chalk.red('\nError getting suggestions:'), error);
      process.exit(1);
    }
  });
