import { Command } from 'commander';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import chalk from 'chalk';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface ControlInfo {
  id: string;
  title: string;
  description: string;
  developerGuidance: string;
  examples: string[];
  relatedControls: string[];
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
    ],
    relatedControls: ['AC-2', 'AC-3', 'PL-1']
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
    ],
    relatedControls: ['AC-3', 'AC-6', 'IA-2', 'AU-2']
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
    ],
    relatedControls: ['AC-2', 'AC-4', 'AC-6']
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
    ],
    relatedControls: ['AU-3', 'AU-6', 'AU-12']
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
    ],
    relatedControls: ['CM-3', 'CM-6', 'CM-8']
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
    ],
    relatedControls: ['CM-2', 'CM-4', 'SA-11']
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
    ],
    relatedControls: ['IA-5', 'IA-8', 'AC-2']
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
    ],
    relatedControls: ['IA-2', 'IA-4', 'IA-6']
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
    ],
    relatedControls: ['SI-2', 'RA-3', 'CA-7']
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
    ],
    relatedControls: ['SA-15', 'CM-3', 'SI-2']
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
    ],
    relatedControls: ['SC-3', 'SC-7', 'AC-6']
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
    ],
    relatedControls: ['SC-5', 'SC-8', 'AC-4']
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
    ],
    relatedControls: ['SC-13', 'SC-23', 'MP-5']
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
    ],
    relatedControls: ['SC-13', 'IA-5', 'MP-2']
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
    ],
    relatedControls: ['SC-8', 'SC-12', 'MP-5']
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
    ],
    relatedControls: ['SC-2', 'SC-3', 'AC-6']
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
    ],
    relatedControls: ['RA-5', 'SI-3', 'CM-3']
  }
};

function getControlInfo(controlId: string): ControlInfo | null {
  const baseControl = controlId.split('(')[0]; // Handle enhancements like AC-2(1)
  return CONTROL_DATABASE[baseControl] || null;
}

export const explainCommand = new Command('explain')
  .description('Explain a NIST 800-53 control in plain English')
  .argument('<control-id>', 'Control ID (e.g., AC-2, SC-8)')
  .option('--for-devs', 'Use developer-friendly language and examples', true)
  .option('--json', 'Output as JSON')
  .action(async (controlId, options) => {
    try {
      const control = getControlInfo(controlId.toUpperCase());
      
      if (!control) {
        console.log(chalk.red(`\n✗ Control ${controlId} not found in database`));
        console.log(chalk.yellow('\nAvailable controls:'));
        console.log(Object.keys(CONTROL_DATABASE).join(', '));
        console.log(chalk.gray('\nNote: This demo includes commonly-used controls. Full NIST 800-53 has 1000+ controls.'));
        process.exit(1);
      }
      
      if (options.json) {
        console.log(JSON.stringify(control, null, 2));
        return;
      }
      
      // Format output for developers
      console.log(chalk.cyan(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`));
      console.log(chalk.bold.white(`\n${control.id}: ${control.title}`));
      console.log(chalk.cyan(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`));
      
      console.log(chalk.bold('Official Description:'));
      console.log(chalk.gray(control.description));
      
      if (options.forDevs) {
        console.log(chalk.bold('\n💡 What This Means for Developers:'));
        console.log(chalk.white(control.developerGuidance));
        
        console.log(chalk.bold('\n📝 Implementation Examples:\n'));
        control.examples.forEach((example, idx) => {
          console.log(chalk.green(`  ${idx + 1}. ${example}`));
        });
      }
      
      console.log(chalk.bold('\n🔗 Related Controls:'));
      console.log(chalk.cyan(`  ${control.relatedControls.join(', ')}`));
      
      console.log(chalk.cyan(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`));
      
      console.log(chalk.yellow(`💡 Tip: Run 'gh oscal scan .' to see if your project implements this control\n`));
      
    } catch (error) {
      console.error(chalk.red('\nError explaining control:'), error);
      process.exit(1);
    }
  });
