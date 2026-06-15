import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

export interface ComplianceSignal {
  file: string;
  control: string;
  evidence: string;
  confidence: 'high' | 'medium' | 'low';
}

const MAX_FILE_BYTES = 1024 * 1024; // 1 MB — prevents OOM on large files in repo

/**
 * Safe file read: skips symlinks, caps at MAX_FILE_BYTES.
 * Returns null if the file should be skipped.
 */
function safeReadFile(filePath: string): string | null {
  try {
    const stat = fs.lstatSync(filePath);
    if (stat.isSymbolicLink() || stat.isDirectory()) return null;
    if (stat.size === 0 || stat.size > MAX_FILE_BYTES) return null;
    return fs.readFileSync(filePath, 'utf-8');
  } catch {
    return null;
  }
}

/**
 * Validates that a file exists and has meaningful content
 * @param filePath - Absolute path to the file
 * @param minLines - Minimum number of non-empty lines (default: 1)
 * @returns true if file exists with valid content
 */
function hasValidContent(filePath: string, minLines: number = 1): boolean {
  const content = safeReadFile(filePath);
  if (content === null) return false;
  const nonEmptyLines = content.split('\n').filter(line => line.trim().length > 0);
  return nonEmptyLines.length >= minLines;
}

/**
 * Validates that a directory exists and contains files
 * @param dirPath - Absolute path to the directory
 * @returns true if directory exists and has files
 */
function hasValidDirectory(dirPath: string): boolean {
  if (!fs.existsSync(dirPath)) {
    return false;
  }
  
  try {
    const stats = fs.statSync(dirPath);
    if (!stats.isDirectory()) {
      return false;
    }
    
    // Check if directory has any files
    const entries = fs.readdirSync(dirPath);
    return entries.length > 0;
  } catch (err) {
    return false;
  }
}

export const DETECTOR_NAMES = [
  'containers',
  'cicd',
  'dependencies',
  'iac',
  'secrets',
  'security-tools',
  'git-security',
  'api',
  'database',
  'sbom',
  'cloud'
] as const;

export type DetectorName = (typeof DETECTOR_NAMES)[number];

export function classifySignal(signal: ComplianceSignal): DetectorName {
  const file = signal.file.toLowerCase();
  const evidence = signal.evidence.toLowerCase();

  if (
    file.includes('docker') ||
    file.includes('kubernetes') ||
    file.includes('openshift') ||
    file.includes('helm')
  ) {
    return 'containers';
  }

  if (
    file.includes('.github/workflows') ||
    file.endsWith('.gitlab-ci.yml') ||
    file.includes('.circleci') ||
    file.endsWith('jenkinsfile') ||
    file.endsWith('azure-pipelines.yml') ||
    file.endsWith('.travis.yml') ||
    file.endsWith('bitbucket-pipelines.yml') ||
    file.includes('dependabot')
  ) {
    return 'cicd';
  }

  if (
    file.endsWith('terraform.tf') ||
    file.endsWith('.tf') ||
    file.endsWith('.tfvars') ||
    file.includes('cloudformation') ||
    file.includes('ansible') ||
    file.includes('arm-template') ||
    file.endsWith('bicep')
  ) {
    return 'iac';
  }

  if (
    file.includes('vault') ||
    file.includes('secrets') ||
    file.includes('keyvault') ||
    file.includes('sealed-secrets') ||
    evidence.includes('secret') ||
    evidence.includes('key management')
  ) {
    return 'secrets';
  }

  if (
    evidence.includes('snyk') ||
    evidence.includes('trivy') ||
    evidence.includes('sonarqube') ||
    evidence.includes('fortify') ||
    evidence.includes('checkmarx') ||
    evidence.includes('owasp zap') ||
    evidence.includes('gitleaks') ||
    evidence.includes('gitguardian')
  ) {
    return 'security-tools';
  }

  if (
    file.endsWith('codeowners') ||
    evidence.includes('branch protection') ||
    evidence.includes('gpg') ||
    evidence.includes('signed commit')
  ) {
    return 'git-security';
  }

  if (
    file.includes('openapi') ||
    file.includes('swagger') ||
    evidence.includes('api gateway') ||
    evidence.includes('api security')
  ) {
    return 'api';
  }

  if (
    file.includes('migration') ||
    file.includes('database') ||
    evidence.includes('database') ||
    evidence.includes('backup')
  ) {
    return 'database';
  }

  if (
    file.includes('cyclonedx') ||
    file.includes('spdx') ||
    file.endsWith('package-lock.json') ||
    file.endsWith('yarn.lock') ||
    file.endsWith('pnpm-lock.yaml') ||
    file.endsWith('gemfile.lock') ||
    file.endsWith('poetry.lock') ||
    file.endsWith('cargo.lock') ||
    evidence.includes('sbom')
  ) {
    return 'sbom';
  }

  if (
    evidence.includes('aws') ||
    evidence.includes('azure') ||
    evidence.includes('gcp') ||
    evidence.includes('cloudformation') ||
    evidence.includes('resource manager')
  ) {
    return 'cloud';
  }

  return 'dependencies';
}

export function filterSignalsByDetectors(
  signals: ComplianceSignal[],
  enabled: DetectorName[],
  disabled: DetectorName[]
): ComplianceSignal[] {
  const disabledSet = new Set<DetectorName>(disabled);
  const enabledSet = new Set<DetectorName>(enabled);
  const useEnabledSet = enabledSet.size > 0;

  return signals.filter((signal) => {
    const detector = classifySignal(signal);

    if (disabledSet.has(detector)) {
      return false;
    }

    if (useEnabledSet) {
      return enabledSet.has(detector);
    }

    return true;
  });
}

// Helper function to recursively get all files in a directory
function getAllFiles(dirPath: string, arrayOfFiles: string[] = []): string[] {
  try {
    const files = fs.readdirSync(dirPath);
    
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      
      if (fs.statSync(filePath).isDirectory()) {
        arrayOfFiles = getAllFiles(filePath, arrayOfFiles);
      } else {
        arrayOfFiles.push(filePath);
      }
    }
  } catch (err) {
    // Ignore errors
  }
  
  return arrayOfFiles;
}

// Helper function to find files by name pattern
function findFilesByName(dirPath: string, fileName: string): string[] {
  const allFiles = getAllFiles(dirPath);
  return allFiles.filter(file => path.basename(file) === fileName);
}

/**
 * Assign confidence to a signal based on detection method.
 * High: dedicated security tooling files
 * Low:  directory/doc presence only or keyword-in-filename
 * Medium: content pattern match, dependency file, CI config
 */
function assignConfidence(signal: Omit<ComplianceSignal, 'confidence'>): ComplianceSignal {
  const f = signal.file.toLowerCase();

  const highFiles = ['.snyk', '.gitleaks.toml', '.trivyignore', 'dependabot.yml', 'dockerfile.ironbank', 'dockerfile.distroless', 'dockerfile.ubi', 'sbom'];
  if (highFiles.some((h) => f.includes(h))) {
    return { ...signal, confidence: 'high' };
  }

  const lowPatterns = ['/tests/', '/test/', '/docs/', '/spec/', 'readme', '.md', '.example', '.template', 'poam', 'risk_assessment', 'fisma'];
  if (lowPatterns.some((p) => f.includes(p)) || f.endsWith('/')) {
    return { ...signal, confidence: 'low' };
  }

  return { ...signal, confidence: 'medium' };
}

export async function scanRepository(repoPath: string): Promise<ComplianceSignal[]> {
  const signals: Omit<ComplianceSignal, 'confidence'>[] = [];
  
  // Signal 1: Containerization
  const dockerfilePath = path.join(repoPath, 'Dockerfile');
  if (hasValidContent(dockerfilePath, 3)) { // Minimum 3 lines for valid Dockerfile
    signals.push({
      file: 'Dockerfile',
      control: 'SC-39',
      evidence: 'Application uses container isolation via Docker for process separation'
    });
  }
  
  // Hardened Container Images - NEW
  const hardenedDockerfiles = [
    { file: 'Dockerfile.ironbank', control: 'SA-22', evidence: 'Platform One Iron Bank hardened container image from DoD-approved registry (registry1.dso.mil)' },
    { file: 'Dockerfile.distroless', control: 'CM-7', evidence: 'Distroless container image with minimal attack surface (no shell, no package manager)' },
    { file: 'Dockerfile.ubi', control: 'SA-22', evidence: 'Universal Base Image (UBI) from Red Hat with enterprise security updates' }
  ];
  
  for (const hardened of hardenedDockerfiles) {
    const hardenedPath = path.join(repoPath, hardened.file);
    if (hasValidContent(hardenedPath, 3)) { // Minimum 3 lines
      signals.push({
        file: hardened.file,
        control: hardened.control,
        evidence: hardened.evidence
      });
      
      // Additional controls for hardened images
      signals.push({
        file: hardened.file,
        control: 'SI-7',
        evidence: 'Software integrity verification via hardened base image with cryptographic signatures'
      });
    }
  }
  
  // Check for multi-stage distroless pattern in regular Dockerfile
  if (hasValidContent(dockerfilePath, 3)) {
    try {
      const dockerContent = safeReadFile(dockerfilePath) ?? '';
      
      if (dockerContent.match(/FROM.*distroless|gcr\.io\/distroless/i)) {
        signals.push({
          file: 'Dockerfile',
          control: 'CM-7',
          evidence: 'Least functionality via distroless base image (minimal attack surface)'
        });
      }
      
      if (dockerContent.match(/FROM.*alpine/i)) {
        signals.push({
          file: 'Dockerfile',
          control: 'CM-7',
          evidence: 'Minimal container footprint via Alpine Linux base image'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  const dockerComposeYml = path.join(repoPath, 'docker-compose.yml');
  const dockerComposeYaml = path.join(repoPath, 'docker-compose.yaml');
  if (hasValidContent(dockerComposeYml, 5) || hasValidContent(dockerComposeYaml, 5)) { // Minimum 5 lines for valid compose file
    signals.push({
      file: 'docker-compose.yml',
      control: 'SC-2',
      evidence: 'Application partitions system components via Docker Compose orchestration'
    });
  }
  
  // Signal 2: CI/CD - ENHANCED
  if (hasValidDirectory(path.join(repoPath, '.github/workflows'))) {
    signals.push({
      file: '.github/workflows/',
      control: 'CM-3',
      evidence: 'Automated configuration change control via GitHub Actions workflows'
    });
    
    signals.push({
      file: '.github/workflows/',
      control: 'SA-11',
      evidence: 'Developer testing and evaluation via automated CI/CD pipeline'
    });
  }
  
  // GitLab CI
  const gitlabCiPath = path.join(repoPath, '.gitlab-ci.yml');
  if (hasValidContent(gitlabCiPath, 3)) {
    signals.push({
      file: '.gitlab-ci.yml',
      control: 'CM-3',
      evidence: 'Automated configuration change control via GitLab CI/CD'
    });
    signals.push({
      file: '.gitlab-ci.yml',
      control: 'SA-11',
      evidence: 'Developer testing via GitLab CI pipeline'
    });
  }

  // CircleCI
  const circleCiPath = path.join(repoPath, '.circleci/config.yml');
  if (hasValidContent(circleCiPath, 3)) {
    signals.push({
      file: '.circleci/config.yml',
      control: 'CM-3',
      evidence: 'Configuration change control via CircleCI automation'
    });
    signals.push({
      file: '.circleci/config.yml',
      control: 'SA-11',
      evidence: 'Automated testing via CircleCI pipeline'
    });
  }

  // Jenkins
  const jenkinsfilePath = path.join(repoPath, 'Jenkinsfile');
  if (hasValidContent(jenkinsfilePath, 3)) {
    signals.push({
      file: 'Jenkinsfile',
      control: 'CM-3',
      evidence: 'Configuration change control via Jenkins pipeline'
    });
    signals.push({
      file: 'Jenkinsfile',
      control: 'SA-11',
      evidence: 'Continuous integration and testing via Jenkins'
    });
  }

  // Azure Pipelines
  const azurePipelinesPath = path.join(repoPath, 'azure-pipelines.yml');
  if (hasValidContent(azurePipelinesPath, 3)) {
    signals.push({
      file: 'azure-pipelines.yml',
      control: 'CM-3',
      evidence: 'Change management via Azure DevOps Pipelines'
    });
    signals.push({
      file: 'azure-pipelines.yml',
      control: 'SA-11',
      evidence: 'Automated testing via Azure Pipelines'
    });
  }

  // Travis CI
  const travisPath = path.join(repoPath, '.travis.yml');
  if (hasValidContent(travisPath, 3)) {
    signals.push({
      file: '.travis.yml',
      control: 'CM-3',
      evidence: 'Configuration change control via Travis CI'
    });
    signals.push({
      file: '.travis.yml',
      control: 'SA-11',
      evidence: 'Continuous testing via Travis CI'
    });
  }

  // Bitbucket Pipelines
  const bitbucketPipelinesPath = path.join(repoPath, 'bitbucket-pipelines.yml');
  if (hasValidContent(bitbucketPipelinesPath, 3)) {
    signals.push({
      file: 'bitbucket-pipelines.yml',
      control: 'CM-3',
      evidence: 'Automated change control via Bitbucket Pipelines'
    });
    signals.push({
      file: 'bitbucket-pipelines.yml',
      control: 'SA-11',
      evidence: 'CI/CD testing via Bitbucket Pipelines'
    });
  }
  
  // Signal 3: Package Management
  const packageJsonPath = path.join(repoPath, 'package.json');
  if (fs.existsSync(packageJsonPath)) {
    try {
      const packageJson = JSON.parse(safeReadFile(packageJsonPath) ?? '');
      
      // Authentication libraries
      if (packageJson.dependencies?.['bcrypt'] || packageJson.dependencies?.['argon2'] || packageJson.dependencies?.['bcryptjs']) {
        signals.push({
          file: 'package.json',
          control: 'IA-5',
          evidence: 'Password hashing implemented with industry-standard cryptographic library'
        });
      }
      
      // JWT/Session management
      if (packageJson.dependencies?.['jsonwebtoken'] || packageJson.dependencies?.['express-session']) {
        signals.push({
          file: 'package.json',
          control: 'IA-2',
          evidence: 'User identification and authentication via token-based authentication'
        });
      }
      
      // Logging
      if (packageJson.dependencies?.['winston'] || packageJson.dependencies?.['pino'] || packageJson.dependencies?.['bunyan']) {
        signals.push({
          file: 'package.json',
          control: 'AU-2',
          evidence: 'Audit logging implemented via structured logging library'
        });
      }
      
      // Security headers
      if (packageJson.dependencies?.['helmet']) {
        signals.push({
          file: 'package.json',
          control: 'SC-8',
          evidence: 'Transmission confidentiality via HTTP security headers (Helmet.js)'
        });
      }
      
      // HTTPS
      if (packageJson.dependencies?.['https']) {
        signals.push({
          file: 'package.json',
          control: 'SC-8',
          evidence: 'Transmission confidentiality and integrity via HTTPS/TLS'
        });
      }
    } catch (err) {
      // Invalid package.json, skip
    }
  }
  
  // Python requirements - ENHANCED
  const requirementsPath = path.join(repoPath, 'requirements.txt');
  if (fs.existsSync(requirementsPath)) {
    const requirements = safeReadFile(requirementsPath) ?? '';
    
    // Cryptographic libraries
    if (requirements.match(/cryptography|passlib|bcrypt/i)) {
      signals.push({
        file: 'requirements.txt',
        control: 'IA-5',
        evidence: 'Authenticator management via cryptographic password hashing (cryptography/passlib)'
      });
      
      signals.push({
        file: 'requirements.txt',
        control: 'SC-13',
        evidence: 'Cryptographic protection via industry-standard encryption libraries'
      });
    }
    
    // JWT/Auth libraries
    if (requirements.match(/python-jose|pyjwt|jwt/i)) {
      signals.push({
        file: 'requirements.txt',
        control: 'IA-2',
        evidence: 'User identification and authentication via JSON Web Token implementation'
      });
    }
    
    // Django/Flask security
    if (requirements.match(/django|flask-login|flask-security/i)) {
      signals.push({
        file: 'requirements.txt',
        control: 'IA-2',
        evidence: 'User authentication framework with session management'
      });
    }
  }

  // Java - Maven (pom.xml)
  const pomPath = path.join(repoPath, 'pom.xml');
  if (fs.existsSync(pomPath)) {
    try {
      const pomContent = safeReadFile(pomPath) ?? '';
      
      // Spring Security
      if (pomContent.includes('spring-security')) {
        signals.push({
          file: 'pom.xml',
          control: 'AC-3',
          evidence: 'Access enforcement via Spring Security framework'
        });
        signals.push({
          file: 'pom.xml',
          control: 'IA-2',
          evidence: 'User authentication via Spring Security'
        });
      }
      
      // BCrypt
      if (pomContent.includes('bcrypt')) {
        signals.push({
          file: 'pom.xml',
          control: 'IA-5',
          evidence: 'Password hashing via BCrypt cryptographic library'
        });
      }
      
      // Logging frameworks
      if (pomContent.match(/logback|slf4j|log4j2/i)) {
        signals.push({
          file: 'pom.xml',
          control: 'AU-2',
          evidence: 'Audit logging via Java logging framework'
        });
      }
      
      // JWT libraries
      if (pomContent.match(/jjwt|java-jwt/i)) {
        signals.push({
          file: 'pom.xml',
          control: 'IA-2',
          evidence: 'Token-based authentication via JWT library'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }

  // Java - Gradle (build.gradle)
  const gradlePath = path.join(repoPath, 'build.gradle');
  if (fs.existsSync(gradlePath)) {
    try {
      const gradleContent = safeReadFile(gradlePath) ?? '';
      
      if (gradleContent.includes('spring-security')) {
        signals.push({
          file: 'build.gradle',
          control: 'AC-3',
          evidence: 'Access enforcement via Spring Security framework'
        });
      }
      
      if (gradleContent.match(/bcrypt|jbcrypt/i)) {
        signals.push({
          file: 'build.gradle',
          control: 'IA-5',
          evidence: 'Password hashing via BCrypt'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }

  // Ruby - Gemfile
  const gemfilePath = path.join(repoPath, 'Gemfile');
  if (fs.existsSync(gemfilePath)) {
    try {
      const gemfileContent = safeReadFile(gemfilePath) ?? '';
      
      // Devise (authentication)
      if (/\bdevise\b/i.test(gemfileContent)) {
        signals.push({
          file: 'Gemfile',
          control: 'IA-2',
          evidence: 'User authentication via Devise Ruby gem'
        });
        signals.push({
          file: 'Gemfile',
          control: 'IA-5',
          evidence: 'Password management via Devise with BCrypt'
        });
      }
      
      // BCrypt
      if (/\bbcrypt\b/i.test(gemfileContent)) {
        signals.push({
          file: 'Gemfile',
          control: 'IA-5',
          evidence: 'Password hashing via BCrypt gem'
        });
      }
      
      // OmniAuth (OAuth)
      if (/\bomniauth\b/i.test(gemfileContent)) {
        signals.push({
          file: 'Gemfile',
          control: 'IA-2',
          evidence: 'OAuth authentication via OmniAuth'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }

  // Go - go.mod
  const goModPath = path.join(repoPath, 'go.mod');
  if (fs.existsSync(goModPath)) {
    try {
      const goModContent = safeReadFile(goModPath) ?? '';
      
      // BCrypt
      if (/golang\.org\/x\/crypto\/bcrypt/.test(goModContent)) {
        signals.push({
          file: 'go.mod',
          control: 'IA-5',
          evidence: 'Password hashing via Go crypto/bcrypt'
        });
      }
      
      // JWT
      if (/\bjwt-go\b/.test(goModContent) || /\bgolang-jwt\b/.test(goModContent)) {
        signals.push({
          file: 'go.mod',
          control: 'IA-2',
          evidence: 'Token authentication via JWT library'
        });
      }
      
      // Logging
      if (goModContent.match(/logrus|zap/)) {
        signals.push({
          file: 'go.mod',
          control: 'AU-2',
          evidence: 'Audit logging via structured logging library'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }

  // .NET - packages.config or .csproj
  const packagesConfigPath = path.join(repoPath, 'packages.config');
  const csprojFiles = getAllFiles(repoPath).filter(f => f.endsWith('.csproj'));
  
  if (fs.existsSync(packagesConfigPath) || csprojFiles.length > 0) {
    try {
      let dotnetContent = '';
      if (fs.existsSync(packagesConfigPath)) {
        dotnetContent = safeReadFile(packagesConfigPath) ?? '';
      } else if (csprojFiles.length > 0) {
        dotnetContent = safeReadFile(csprojFiles[0]) ?? '';
      }
      
      // BCrypt.Net
      if (/BCrypt\.Net/.test(dotnetContent)) {
        signals.push({
          file: fs.existsSync(packagesConfigPath) ? 'packages.config' : path.basename(csprojFiles[0]),
          control: 'IA-5',
          evidence: 'Password hashing via BCrypt.Net'
        });
      }
      
      // IdentityServer
      if (/IdentityServer/.test(dotnetContent)) {
        signals.push({
          file: fs.existsSync(packagesConfigPath) ? 'packages.config' : path.basename(csprojFiles[0]),
          control: 'IA-2',
          evidence: 'Authentication and authorization via IdentityServer'
        });
      }
      
      // Serilog
      if (/\bSerilog\b/.test(dotnetContent)) {
        signals.push({
          file: fs.existsSync(packagesConfigPath) ? 'packages.config' : path.basename(csprojFiles[0]),
          control: 'AU-2',
          evidence: 'Audit logging via Serilog structured logging'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }

  // PHP - composer.json
  const composerPath = path.join(repoPath, 'composer.json');
  if (fs.existsSync(composerPath)) {
    try {
      const composerJson = JSON.parse(safeReadFile(composerPath) ?? '');
      const deps = { ...composerJson.require, ...composerJson['require-dev'] };
      
      // Laravel/Symfony security
      if (deps['laravel/framework'] || deps['symfony/security']) {
        signals.push({
          file: 'composer.json',
          control: 'IA-2',
          evidence: 'Authentication via PHP framework security components'
        });
      }
      
      // JWT
      if (deps['firebase/php-jwt'] || deps['lcobucci/jwt']) {
        signals.push({
          file: 'composer.json',
          control: 'IA-2',
          evidence: 'Token authentication via JWT library'
        });
      }
      
      // Monolog (logging)
      if (deps['monolog/monolog']) {
        signals.push({
          file: 'composer.json',
          control: 'AU-2',
          evidence: 'Audit logging via Monolog'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }

  // Rust - Cargo.toml
  const cargoPath = path.join(repoPath, 'Cargo.toml');
  if (fs.existsSync(cargoPath)) {
    try {
      const cargoContent = safeReadFile(cargoPath) ?? '';
      
      // Argon2/BCrypt
      if (cargoContent.match(/argon2|bcrypt/)) {
        signals.push({
          file: 'Cargo.toml',
          control: 'IA-5',
          evidence: 'Password hashing via Rust cryptographic crate'
        });
      }
      
      // JWT
      if (/\bjsonwebtoken\b/.test(cargoContent)) {
        signals.push({
          file: 'Cargo.toml',
          control: 'IA-2',
          evidence: 'Token authentication via JWT crate'
        });
      }
      
      // Logging
      if (cargoContent.match(/log|tracing|env_logger/)) {
        signals.push({
          file: 'Cargo.toml',
          control: 'AU-2',
          evidence: 'Audit logging via Rust logging framework'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Backend/Middleware Detection - NEW
  const middlewarePath = path.join(repoPath, 'backend/middleware');
  if (fs.existsSync(middlewarePath)) {
    const middlewareFiles = fs.readdirSync(middlewarePath);
    
    // Audit middleware
    if (middlewareFiles.some(f => f.includes('audit'))) {
      signals.push({
        file: 'backend/middleware/audit.py',
        control: 'AU-2',
        evidence: 'Audit event determination via centralized audit middleware'
      });
      
      signals.push({
        file: 'backend/middleware/audit.py',
        control: 'AU-3',
        evidence: 'Audit record content generation with timestamp, user, and event details'
      });
      
      signals.push({
        file: 'backend/middleware/audit.py',
        control: 'AU-12',
        evidence: 'Audit record generation via application-level logging middleware'
      });
    }
    
    // Rate limiting
    if (middlewareFiles.some(f => f.includes('rate'))) {
      signals.push({
        file: 'backend/middleware/rate_limit.py',
        control: 'SC-5',
        evidence: 'Denial-of-service protection via rate limiting middleware'
      });
    }
    
    // Security headers/context
    if (middlewareFiles.some(f => f.includes('security'))) {
      signals.push({
        file: 'backend/middleware/security.py',
        control: 'AC-6',
        evidence: 'Least privilege enforcement via security middleware'
      });
    }
    
    // System use notification
    if (middlewareFiles.some(f => f.includes('banner') || f.includes('notification'))) {
      signals.push({
        file: 'backend/middleware/system_use_banner.py',
        control: 'AC-8',
        evidence: 'System use notification displayed via middleware banner'
      });
    }
  }
  
  // Signal 5: Testing
  const hasTests = fs.existsSync(path.join(repoPath, 'test')) || 
                   fs.existsSync(path.join(repoPath, 'tests')) ||
                   fs.existsSync(path.join(repoPath, '__tests__')) ||
                   fs.existsSync(path.join(repoPath, 'spec'));
  
  if (hasTests) {
    signals.push({
      file: 'tests/',
      control: 'SA-11',
      evidence: 'Security testing and evaluation via automated test suite'
    });
  }
  
  // Signal 6: Infrastructure as Code - ENHANCED
  if (fs.existsSync(path.join(repoPath, 'terraform')) || fs.existsSync(path.join(repoPath, 'main.tf'))) {
    signals.push({
      file: 'terraform/',
      control: 'CM-2',
      evidence: 'Baseline configuration via Infrastructure as Code (Terraform)'
    });
  }
  
  if (fs.existsSync(path.join(repoPath, 'ansible')) || fs.existsSync(path.join(repoPath, 'playbook.yml'))) {
    signals.push({
      file: 'ansible/',
      control: 'CM-2',
      evidence: 'Configuration management via Ansible automation'
    });
  }

  // AWS CloudFormation
  if (fs.existsSync(path.join(repoPath, 'cloudformation')) || getAllFiles(repoPath).some(f => f.endsWith('.template') || f.endsWith('.template.json'))) {
    signals.push({
      file: 'cloudformation/',
      control: 'CM-2',
      evidence: 'Configuration baseline via AWS CloudFormation templates'
    });
    signals.push({
      file: 'cloudformation/',
      control: 'SC-7',
      evidence: 'Boundary protection via CloudFormation security group definitions'
    });
  }

  // Azure Resource Manager (ARM)
  if (getAllFiles(repoPath).some(f => f.includes('azuredeploy.json') || f.includes('.bicep'))) {
    signals.push({
      file: 'Azure ARM templates',
      control: 'CM-2',
      evidence: 'Infrastructure baseline via Azure Resource Manager templates'
    });
  }

  // Google Cloud Deployment Manager
  if (getAllFiles(repoPath).some(f => f.includes('.jinja') && f.includes('deployment'))) {
    signals.push({
      file: 'GCP Deployment Manager',
      control: 'CM-2',
      evidence: 'Configuration management via GCP Deployment Manager'
    });
  }

  // Pulumi
  if (fs.existsSync(path.join(repoPath, 'Pulumi.yaml'))) {
    signals.push({
      file: 'Pulumi.yaml',
      control: 'CM-2',
      evidence: 'Infrastructure as Code via Pulumi'
    });
  }

  // Helm charts
  if (fs.existsSync(path.join(repoPath, 'charts')) || fs.existsSync(path.join(repoPath, 'Chart.yaml'))) {
    signals.push({
      file: 'helm charts/',
      control: 'CM-2',
      evidence: 'Kubernetes application configuration via Helm charts'
    });
  }
  
  // Kubernetes - ENHANCED with YAML parsing
  const k8sPaths = [
    path.join(repoPath, 'k8s'),
    path.join(repoPath, 'kubernetes'),
    path.join(repoPath, 'openshift')
  ];
  
  for (const k8sPath of k8sPaths) {
    if (fs.existsSync(k8sPath)) {
      signals.push({
        file: path.basename(k8sPath) + '/',
        control: 'SC-2',
        evidence: 'Application partitioning via Kubernetes namespace isolation'
      });
      
      // Parse YAML files for specific patterns
      try {
        const yamlFiles = fs.readdirSync(k8sPath).filter(f => f.endsWith('.yaml') || f.endsWith('.yml'));
        
        for (const yamlFile of yamlFiles) {
          const content = fs.readFileSync(path.join(k8sPath, yamlFile), 'utf-8');
          
          // Network policies
          if (content.includes('kind: NetworkPolicy') || content.includes('networkPolicy')) {
            signals.push({
              file: `${path.basename(k8sPath)}/${yamlFile}`,
              control: 'SC-7',
              evidence: 'Boundary protection via Kubernetes NetworkPolicy configuration'
            });
          }
          
          // RBAC
          if (content.match(/kind:\s*(Role|ClusterRole|RoleBinding)/)) {
            signals.push({
              file: `${path.basename(k8sPath)}/${yamlFile}`,
              control: 'AC-3',
              evidence: 'Access enforcement via Kubernetes Role-Based Access Control (RBAC)'
            });
          }
          
          // Security contexts
          if (content.includes('securityContext')) {
            signals.push({
              file: `${path.basename(k8sPath)}/${yamlFile}`,
              control: 'SC-39',
              evidence: 'Process isolation via Kubernetes security context constraints'
            });
          }
          
          // Resource limits
          if (content.includes('resources:') && content.includes('limits:')) {
            signals.push({
              file: `${path.basename(k8sPath)}/${yamlFile}`,
              control: 'SC-6',
              evidence: 'Resource availability via Kubernetes resource quotas and limits'
            });
          }
        }
      } catch (err) {
        // Ignore parsing errors
      }
      
      break; // Only process first found k8s directory
    }
  }
  
  // Signal 7: Security Scanning - ENHANCED
  if (fs.existsSync(path.join(repoPath, '.snyk'))) {
    signals.push({
      file: '.snyk',
      control: 'RA-5',
      evidence: 'Vulnerability scanning via Snyk security monitoring'
    });
  }
  
  // Dependabot
  if (fs.existsSync(path.join(repoPath, '.github/dependabot.yml'))) {
    signals.push({
      file: '.github/dependabot.yml',
      control: 'SI-2',
      evidence: 'Flaw remediation via automated dependency updates'
    });
  }

  // Trivy
  if (fs.existsSync(path.join(repoPath, '.trivyignore')) || getAllFiles(repoPath).some(f => f.includes('trivy'))) {
    signals.push({
      file: 'trivy configuration',
      control: 'RA-5',
      evidence: 'Container vulnerability scanning via Trivy'
    });
  }

  // SonarQube
  if (fs.existsSync(path.join(repoPath, 'sonar-project.properties'))) {
    signals.push({
      file: 'sonar-project.properties',
      control: 'SA-11',
      evidence: 'Code quality and security analysis via SonarQube'
    });
    signals.push({
      file: 'sonar-project.properties',
      control: 'RA-5',
      evidence: 'Static application security testing (SAST) via SonarQube'
    });
  }

  // Fortify
  if (getAllFiles(repoPath).some(f => f.includes('fortify'))) {
    signals.push({
      file: 'fortify configuration',
      control: 'SA-11',
      evidence: 'Static code analysis via Fortify'
    });
  }

  // Checkmarx
  if (getAllFiles(repoPath).some(f => f.includes('checkmarx') || f.includes('.cxxml'))) {
    signals.push({
      file: 'checkmarx configuration',
      control: 'SA-11',
      evidence: 'Security testing via Checkmarx SAST'
    });
  }

  // OWASP ZAP
  if (getAllFiles(repoPath).some(f => f.includes('zap') && (f.endsWith('.yaml') || f.endsWith('.conf')))) {
    signals.push({
      file: 'OWASP ZAP configuration',
      control: 'SA-11',
      evidence: 'Dynamic application security testing (DAST) via OWASP ZAP'
    });
  }

  // Secret Detection (.gitguardian, .gitleaks, etc.)
  if (fs.existsSync(path.join(repoPath, '.gitleaks.toml')) || fs.existsSync(path.join(repoPath, '.gitguardian.yaml'))) {
    signals.push({
      file: 'secret scanning configuration',
      control: 'RA-5',
      evidence: 'Secret detection via automated scanning tools'
    });
    signals.push({
      file: 'secret scanning configuration',
      control: 'SC-12',
      evidence: 'Cryptographic key management via secret detection'
    });
  }
  
  // Signal 8: Documentation - ENHANCED
  if (fs.existsSync(path.join(repoPath, 'README.md'))) {
    signals.push({
      file: 'README.md',
      control: 'SA-5',
      evidence: 'System documentation maintained in repository'
    });
  }
  
  // Compliance documentation - NEW
  const docsPath = path.join(repoPath, 'docs');
  if (fs.existsSync(docsPath)) {
    try {
      const docFiles = getAllFiles(docsPath);
      
      for (const docFile of docFiles) {
        const fileName = path.basename(docFile).toLowerCase();
        
        // Risk assessment
        if (fileName.includes('risk') && fileName.includes('assessment')) {
          signals.push({
            file: `docs/${path.relative(docsPath, docFile)}`,
            control: 'RA-3',
            evidence: 'Risk assessment documentation maintained for security authorization'
          });
        }
        
        // Privacy impact
        if (fileName.includes('privacy') && (fileName.includes('impact') || fileName.includes('assessment'))) {
          signals.push({
            file: `docs/${path.relative(docsPath, docFile)}`,
            control: 'AP-2',
            evidence: 'Privacy impact assessment documented for PII handling'
          });
        }
        
        // FISMA/Compliance
        if (fileName.includes('fisma') || fileName.includes('compliance')) {
          signals.push({
            file: `docs/${path.relative(docsPath, docFile)}`,
            control: 'CA-2',
            evidence: 'Security assessment documentation per FISMA requirements'
          });
        }
        
        // System Security Plan
        if (fileName.includes('ssp') || fileName.includes('security_plan') || fileName.includes('system_security')) {
          signals.push({
            file: `docs/${path.relative(docsPath, docFile)}`,
            control: 'PL-2',
            evidence: 'System security plan documentation maintained'
          });
        }
        
        // Deployment/operations
        if (fileName.includes('deployment') || fileName.includes('operations')) {
          signals.push({
            file: `docs/${path.relative(docsPath, docFile)}`,
            control: 'SA-5',
            evidence: 'System deployment and operational documentation'
          });
        }
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Authentication Service Detection - Search recursively for auth_service.py
  const authServiceFiles = findFilesByName(repoPath, 'auth_service.py');
  for (const authServicePath of authServiceFiles) {
    try {
      const authContent = safeReadFile(authServicePath) ?? '';
      const relPath = path.relative(repoPath, authServicePath);
      
      // IA-2: Identification and Authentication
      if (authContent.includes('jwt') || authContent.includes('JWT') || authContent.includes('token')) {
        signals.push({
          file: relPath,
          control: 'IA-2',
          evidence: 'User identification and authentication via JWT token-based system'
        });
      }
      
      // IA-5: Authenticator Management
      if (authContent.includes('hash_password') || authContent.includes('bcrypt') || authContent.includes('CryptContext')) {
        signals.push({
          file: relPath,
          control: 'IA-5',
          evidence: 'Authenticator management via password hashing (bcrypt)'
        });
      }
      
      // AC-2: Account Management
      if (authContent.includes('create_user') || authContent.includes('User') || authContent.includes('register')) {
        signals.push({
          file: relPath,
          control: 'AC-2',
          evidence: 'Account management implementation for user creation and administration'
        });
      }
      
      // AC-11: Session Lock / AC-12: Session Termination
      if (authContent.includes('expires_delta') || authContent.includes('JWT_EXPIRATION') || authContent.includes('expire')) {
        signals.push({
          file: relPath,
          control: 'AC-11',
          evidence: 'Device lock via session timeout configured through JWT expiration'
        });
        
        signals.push({
          file: relPath,
          control: 'AC-12',
          evidence: 'Session termination via JWT token expiration mechanism'
        });
      }
      
      // AC-7: Unsuccessful Login Attempts (if rate limiting on auth)
      if (authContent.includes('login') && authContent.includes('attempt')) {
        signals.push({
          file: 'backend/services/auth_service.py',
          control: 'AC-7',
          evidence: 'Unsuccessful login attempt handling and account lockout mechanism'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Guardrails Service Detection - NEW
  const guardrailsPath = path.join(repoPath, 'backend/services/guardrails_service.py');
  if (fs.existsSync(guardrailsPath)) {
    try {
      const guardrailsContent = safeReadFile(guardrailsPath) ?? '';
      
      // SI-10: Information Input Validation
      if (guardrailsContent.includes('validate_input') || guardrailsContent.includes('sanitize')) {
        signals.push({
          file: 'backend/services/guardrails_service.py',
          control: 'SI-10',
          evidence: 'Information input validation via guardrails service sanitization'
        });
      }
      
      // SI-12: Information Handling and Retention (PII detection/redaction)
      if (guardrailsContent.includes('pii') || guardrailsContent.includes('PII') || guardrailsContent.includes('redaction')) {
        signals.push({
          file: 'backend/services/guardrails_service.py',
          control: 'SI-12',
          evidence: 'Information handling via PII detection and redaction mechanisms'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Logging and Monitoring Detection - NEW
  const servicesPath = path.join(repoPath, 'backend/services');
  if (fs.existsSync(servicesPath)) {
    try {
      const serviceFiles = getAllFiles(servicesPath).filter(f => f.endsWith('.py'));
      
      for (const serviceFile of serviceFiles) {
        try {
          const content = safeReadFile(serviceFile) ?? '';
          
          // SI-4: System Monitoring (structured logging)
          if (content.includes('structlog') || content.includes('logger.info') || content.includes('logger.error')) {
            signals.push({
              file: `backend/services/${path.basename(serviceFile)}`,
              control: 'SI-4',
              evidence: 'System monitoring via structured logging implementation'
            });
            break; // Only add once
          }
        } catch (err) {
          // Ignore individual file errors
        }
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Configuration Management Detection - NEW
  const configPath = path.join(repoPath, 'backend/core/config.py');
  if (fs.existsSync(configPath)) {
    signals.push({
      file: 'backend/core/config.py',
      control: 'CM-6',
      evidence: 'Configuration settings management via centralized configuration module'
    });
  }
  
  // Environment Configuration
  const envExamplePath = path.join(repoPath, '.env.example');
  if (fs.existsSync(envExamplePath)) {
    // CM-2: an .env.example is a documented baseline configuration template
    signals.push({
      file: '.env.example',
      control: 'CM-2',
      evidence: 'Baseline configuration documented via environment variable template'
    });
    // Note: presence of HTTPS/TLS/SSL variable names in a template file does NOT
    // confirm SC-8 (Transmission Confidentiality) — removed to avoid false positive.
  }
  
  // Error Handling Detection - NEW
  const apiPath = path.join(repoPath, 'backend/api');
  if (fs.existsSync(apiPath)) {
    try {
      const apiFiles = getAllFiles(apiPath).filter(f => f.endsWith('.py'));
      
      for (const apiFile of apiFiles) {
        try {
          const content = safeReadFile(apiFile) ?? '';
          
          // SI-11: Error Handling
          if ((content.includes('try:') && content.includes('except')) || content.includes('HTTPException')) {
            signals.push({
              file: `backend/api/${path.basename(apiFile)}`,
              control: 'SI-11',
              evidence: 'Error handling and information disclosure prevention via exception handling'
            });
            break; // Only add once
          }
        } catch (err) {
          // Ignore individual file errors
        }
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Database Security Detection - NEW
  const dbPath = path.join(repoPath, 'backend/core/database.py');
  if (fs.existsSync(dbPath)) {
    try {
      const dbContent = safeReadFile(dbPath) ?? '';
      
      // SC-28: Protection of Information at Rest
      if (dbContent.includes('encrypt') || dbContent.includes('ssl_mode') || dbContent.includes('AsyncSession')) {
        signals.push({
          file: 'backend/core/database.py',
          control: 'SC-28',
          evidence: 'Protection of information at rest via database encryption and secure connections'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // API Security - Dependencies Detection - NEW
  const dependenciesPath = path.join(repoPath, 'backend/api/dependencies.py');
  if (fs.existsSync(dependenciesPath)) {
    try {
      const depContent = safeReadFile(dependenciesPath) ?? '';
      
      // AC-3: Access Enforcement
      if (depContent.includes('get_current_user') || depContent.includes('require_auth') || depContent.includes('Permission')) {
        signals.push({
          file: 'backend/api/dependencies.py',
          control: 'AC-3',
          evidence: 'Access enforcement via authentication and authorization dependencies'
        });
      }
      
      // IA-4: Identifier Management
      if (depContent.includes('user_id') || depContent.includes('api_key')) {
        signals.push({
          file: 'backend/api/dependencies.py',
          control: 'IA-4',
          evidence: 'Identifier management via user and API key authentication'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Security Automation Scripts - NEW
  const securityScriptsPath = path.join(repoPath, 'scripts/security');
  if (fs.existsSync(securityScriptsPath)) {
    try {
      const securityFiles = fs.readdirSync(securityScriptsPath);
      
      // SBOM Generation
      if (securityFiles.some(f => f.includes('sbom') || f.includes('SBOM'))) {
        signals.push({
          file: 'scripts/security/generate_sbom.sh',
          control: 'SR-4',
          evidence: 'Software supply chain provenance via automated SBOM generation'
        });
        
        signals.push({
          file: 'scripts/security/generate_sbom.sh',
          control: 'SA-4',
          evidence: 'Acquisition process controls via software bill of materials'
        });
      }
      
      // Vulnerability Scanning
      if (securityFiles.some(f => f.includes('vulnerabilit') || f.includes('scan'))) {
        signals.push({
          file: 'scripts/security/scan_vulnerabilities.sh',
          control: 'RA-5',
          evidence: 'Vulnerability monitoring and scanning via automated security tooling'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Health Check & Monitoring - NEW
  const healthCheckPath = path.join(repoPath, 'scripts/health_check.py');
  if (fs.existsSync(healthCheckPath)) {
    signals.push({
      file: 'scripts/health_check.py',
      control: 'SI-4',
      evidence: 'System monitoring via automated health check endpoints'
    });
    
    signals.push({
      file: 'scripts/health_check.py',
      control: 'CP-2',
      evidence: 'Contingency plan implementation via system health monitoring'
    });
  }
  
  // SAML/SSO Configuration - NEW
  const coreConfigPath = path.join(repoPath, 'backend/core/config.py');
  if (fs.existsSync(coreConfigPath)) {
    try {
      const configContent = safeReadFile(coreConfigPath) ?? '';
      
      // IA-8: Non-organizational users
      if (configContent.match(/SAML|SSO|ENABLE_SAML/i)) {
        signals.push({
          file: 'backend/core/config.py',
          control: 'IA-8',
          evidence: 'Identification and authentication for non-organizational users via SAML/SSO'
        });
      }
      
      // CP-9: System Backup
      if (configContent.match(/BACKUP|backup_path/i)) {
        signals.push({
          file: 'backend/core/config.py',
          control: 'CP-9',
          evidence: 'System backup configuration for data protection'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Backup Endpoints - NEW
  const adminApiPath = path.join(repoPath, 'backend/api/v1/admin.py');
  if (fs.existsSync(adminApiPath)) {
    try {
      const adminContent = safeReadFile(adminApiPath) ?? '';
      
      if (adminContent.includes('backup')) {
        signals.push({
          file: 'backend/api/v1/admin.py',
          control: 'CP-9',
          evidence: 'System backup capability via administrative API endpoints'
        });
        
        signals.push({
          file: 'backend/api/v1/admin.py',
          control: 'CP-10',
          evidence: 'System recovery via backup and restore API functionality'
        });
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Additional Documentation - NEW
  if (fs.existsSync(docsPath)) {
    try {
      const docFiles = getAllFiles(docsPath);
      
      for (const docFile of docFiles) {
        const fileName = path.basename(docFile).toLowerCase();
        const relativePath = `docs/${path.relative(docsPath, docFile)}`;
        
        // POA&M Template
        if (fileName.includes('poam')) {
          signals.push({
            file: relativePath,
            control: 'CA-5',
            evidence: 'Plan of Action and Milestones template for tracking security deficiencies'
          });
        }
        
        // Data Flow Diagram
        if (fileName.includes('data_flow') || fileName.includes('dataflow')) {
          signals.push({
            file: relativePath,
            control: 'AC-4',
            evidence: 'Information flow enforcement documented via data flow diagrams'
          });
        }
        
        // Controls Traceability Matrix
        if (fileName.includes('traceability') || fileName.includes('matrix')) {
          signals.push({
            file: relativePath,
            control: 'CA-2',
            evidence: 'Security control assessment via controls traceability matrix'
          });
        }
        
        // Production Readiness
        if (fileName.includes('production') && fileName.includes('readiness')) {
          signals.push({
            file: relativePath,
            control: 'SA-11',
            evidence: 'Developer security testing via production readiness checklist'
          });
        }
        
        // Hardened Images Documentation
        if (fileName.includes('hardened') && fileName.includes('image')) {
          signals.push({
            file: relativePath,
            control: 'SA-22',
            evidence: 'Unsupported system functions documented via hardened container images'
          });
        }
        
        // ServiceNow/Splunk Integration
        if (fileName.includes('servicenow') || fileName.includes('splunk')) {
          signals.push({
            file: relativePath,
            control: 'AU-6',
            evidence: 'Audit record review and analysis via SIEM integration (ServiceNow/Splunk)'
          });
          
          signals.push({
            file: relativePath,
            control: 'SI-4',
            evidence: 'System monitoring via security information and event management integration'
          });
        }
        
        // FISMA Compliance Doc - Additional Controls
        if (fileName.includes('fisma')) {
          // Read content for specific control evidence
          try {
            const fismaContent = safeReadFile(docFile) ?? '';
            
            // IR-4: Incident Handling
            if (fismaContent.match(/incident.*response|response.*procedure/i)) {
              signals.push({
                file: relativePath,
                control: 'IR-4',
                evidence: 'Incident handling procedures documented for security event response'
              });
            }
            
            // AC-7: Unsuccessful Login Attempts
            if (fismaContent.match(/failed.*login|login.*attempt|lockout/i)) {
              signals.push({
                file: relativePath,
                control: 'AC-7',
                evidence: 'Unsuccessful logon attempts enforcement via account lockout policy'
              });
            }
            
            // AU-9: Protection of Audit Information
            if (fismaContent.match(/audit.*protect|append.*only|log.*protect/i)) {
              signals.push({
                file: relativePath,
                control: 'AU-9',
                evidence: 'Protection of audit information via append-only logs and access controls'
              });
            }
          } catch (err) {
            // Ignore read errors
          }
        }
      }
    } catch (err) {
      // Ignore errors
    }
  }
  
  // Dependency Management Files - SA-15
  const requirementsTxt = path.join(repoPath, 'backend/requirements.txt');
  const packageJson = path.join(repoPath, 'package.json');
  const frontendPackageJson = path.join(repoPath, 'frontend/package.json');
  const librechatPackageJson = path.join(repoPath, 'librechat/package.json');
  
  if (fs.existsSync(requirementsTxt) || fs.existsSync(packageJson) || 
      fs.existsSync(frontendPackageJson) || fs.existsSync(librechatPackageJson)) {
    const depFiles = [];
    if (fs.existsSync(requirementsTxt)) depFiles.push('backend/requirements.txt');
    if (fs.existsSync(packageJson)) depFiles.push('package.json');
    if (fs.existsSync(frontendPackageJson)) depFiles.push('frontend/package.json');
    if (fs.existsSync(librechatPackageJson)) depFiles.push('librechat/package.json');
    
    signals.push({
      file: depFiles.join(', '),
      control: 'SA-15',
      evidence: 'Development process and standards via documented dependencies and version management'
    });
  }
  
  // Flaw Remediation via Vulnerability Scanning - SI-2
  if (fs.existsSync(path.join(repoPath, 'scripts/security/scan_vulnerabilities.sh'))) {
    signals.push({
      file: 'scripts/security/scan_vulnerabilities.sh',
      control: 'SI-2',
      evidence: 'Flaw remediation via automated vulnerability scanning and patching workflow'
    });
  }
  
  // Signal 9: License
  if (fs.existsSync(path.join(repoPath, 'LICENSE'))) {
    signals.push({
      file: 'LICENSE',
      control: 'SA-1',
      evidence: 'System and services acquisition policy via open source license'
    });
  }

  // Secret Management Systems
  // HashiCorp Vault
  if (getAllFiles(repoPath).some(f => f.includes('vault') && (f.endsWith('.hcl') || f.endsWith('.json')))) {
    signals.push({
      file: 'vault configuration',
      control: 'SC-12',
      evidence: 'Cryptographic key establishment via HashiCorp Vault'
    });
    signals.push({
      file: 'vault configuration',
      control: 'SC-28',
      evidence: 'Protection of information at rest via Vault encryption'
    });
  }

  // AWS Secrets Manager / Parameter Store
  if (getAllFiles(repoPath).some(f => f.includes('secrets') && f.includes('aws'))) {
    signals.push({
      file: 'AWS secrets configuration',
      control: 'SC-12',
      evidence: 'Cryptographic key management via AWS Secrets Manager'
    });
  }

  // Azure Key Vault
  if (getAllFiles(repoPath).some(f => f.includes('keyvault') || f.includes('key-vault'))) {
    signals.push({
      file: 'Azure Key Vault configuration',
      control: 'SC-12',
      evidence: 'Cryptographic key management via Azure Key Vault'
    });
  }

  // Kubernetes Sealed Secrets
  if (getAllFiles(repoPath).some(f => f.includes('sealed-secret') || f.includes('sealedsecret'))) {
    signals.push({
      file: 'sealed secrets',
      control: 'SC-12',
      evidence: 'Secret management via Kubernetes Sealed Secrets'
    });
    signals.push({
      file: 'sealed secrets',
      control: 'SC-28',
      evidence: 'Encryption of secrets at rest in Kubernetes'
    });
  }

  // API Security - OpenAPI/Swagger Specifications
  if (getAllFiles(repoPath).some(f => f.includes('swagger') || f.includes('openapi'))) {
    const apiSpecFile = getAllFiles(repoPath).find(f => f.includes('swagger') || f.includes('openapi'));
    signals.push({
      file: path.basename(apiSpecFile || 'API specification'),
      control: 'SA-5',
      evidence: 'System documentation via OpenAPI/Swagger API specifications'
    });
    signals.push({
      file: path.basename(apiSpecFile || 'API specification'),
      control: 'AC-3',
      evidence: 'Access enforcement documented via API security definitions'
    });
  }

  // API Gateway configurations
  if (getAllFiles(repoPath).some(f => f.includes('api-gateway') || f.includes('apigateway'))) {
    signals.push({
      file: 'API Gateway configuration',
      control: 'SC-7',
      evidence: 'Boundary protection via API Gateway'
    });
    signals.push({
      file: 'API Gateway configuration',
      control: 'SC-5',
      evidence: 'Denial of service protection via API rate limiting'
    });
  }

  // Database Security
  // Database migrations (schema changes tracked)
  const migrationDirs = ['migrations', 'db/migrations', 'database/migrations', 'alembic'];
  for (const migDir of migrationDirs) {
    if (fs.existsSync(path.join(repoPath, migDir))) {
      signals.push({
        file: `${migDir}/`,
        control: 'CM-3',
        evidence: 'Configuration change control via database migration versioning'
      });
      break;
    }
  }

  // Database connection configs with TLS/SSL
  const dbConfigFiles = getAllFiles(repoPath).filter(f => 
    f.includes('database') && (f.endsWith('.yml') || f.endsWith('.yaml') || f.endsWith('.conf'))
  );
  for (const dbConfig of dbConfigFiles) {
    try {
      const content = safeReadFile(dbConfig) ?? '';
      if (content.match(/ssl.*true|tls.*enabled|sslmode.*require/i)) {
        signals.push({
          file: path.basename(dbConfig),
          control: 'SC-8',
          evidence: 'Transmission confidentiality via database TLS/SSL connections'
        });
        break;
      }
    } catch (err) {
      // Ignore read errors
    }
  }

  // Database backup scripts
  if (getAllFiles(repoPath).some(f => f.includes('backup') && (f.endsWith('.sh') || f.endsWith('.py')))) {
    signals.push({
      file: 'backup scripts',
      control: 'CP-9',
      evidence: 'System backup via automated database backup scripts'
    });
  }

  // SBOM (Software Bill of Materials) Detection
  // CycloneDX
  if (getAllFiles(repoPath).some(f => f.includes('cyclonedx') || f.includes('bom.json') || f.includes('bom.xml'))) {
    signals.push({
      file: 'CycloneDX SBOM',
      control: 'SR-4',
      evidence: 'Supply chain provenance via CycloneDX Software Bill of Materials'
    });
    signals.push({
      file: 'CycloneDX SBOM',
      control: 'SA-4',
      evidence: 'Acquisition process with software composition transparency'
    });
  }

  // SPDX
  if (getAllFiles(repoPath).some(f => f.includes('spdx') || f.endsWith('.spdx'))) {
    signals.push({
      file: 'SPDX SBOM',
      control: 'SR-4',
      evidence: 'Supply chain security via SPDX Software Bill of Materials'
    });
  }

  // Dependency graphs or lock files (enhanced detection)
  const lockFiles = ['package-lock.json', 'yarn.lock', 'Gemfilelock', 'Cargo.lock', 'poetry.lock', 'Pipfile.lock', 'go.sum'];
  for (const lockFile of lockFiles) {
    if (fs.existsSync(path.join(repoPath, lockFile))) {
      signals.push({
        file: lockFile,
        control: 'SA-15',
        evidence: 'Development process controls via dependency lock file'
      });
      signals.push({
        file: lockFile,
        control: 'SR-3',
        evidence: 'Supply chain controls via pinned dependency versions'
      });
      break;
    }
  }

  // Git Security - Signed Commits
  try {
    const gitConfigPath = path.join(repoPath, '.git/config');
    if (fs.existsSync(gitConfigPath)) {
      const gitConfig = safeReadFile(gitConfigPath) ?? '';
      if (gitConfig.includes('gpgsign') || gitConfig.includes('signingkey')) {
        signals.push({
          file: '.git/config',
          control: 'SI-7',
          evidence: 'Software integrity via GPG-signed Git commits'
        });
        signals.push({
          file: '.git/config',
          control: 'AU-10',
          evidence: 'Non-repudiation via cryptographic commit signing'
        });
      }
    }
  } catch (err) {
    // Ignore errors
  }

  // .gitattributes (file handling rules)
  if (fs.existsSync(path.join(repoPath, '.gitattributes'))) {
    signals.push({
      file: '.gitattributes',
      control: 'CM-3',
      evidence: 'Configuration management via Git attribute rules'
    });
  }

  // CODEOWNERS (access control for code changes)
  if (fs.existsSync(path.join(repoPath, 'CODEOWNERS')) || fs.existsSync(path.join(repoPath, '.github/CODEOWNERS'))) {
    signals.push({
      file: 'CODEOWNERS',
      control: 'AC-3',
      evidence: 'Access enforcement via code ownership requirements'
    });
    signals.push({
      file: 'CODEOWNERS',
      control: 'CM-3',
      evidence: 'Change approval process via required code owner reviews'
    });
  }

  // Branch protection (via .github/settings.yml or similar)
  if (getAllFiles(repoPath).some(f => f.includes('.github') && f.includes('settings'))) {
    signals.push({
      file: '.github/settings.yml',
      control: 'CM-3',
      evidence: 'Configuration change control via branch protection rules'
    });
  }

  // Enhanced YAML/JSON Parsing for CloudFormation
  const cfTemplates = getAllFiles(repoPath).filter(f => 
    f.includes('cloudformation') && (f.endsWith('.yaml') || f.endsWith('.json') || f.endsWith('.template'))
  );
  for (const cfTemplate of cfTemplates) {
    try {
      const content = safeReadFile(cfTemplate) ?? '';
      
      // Security Groups
      if (content.includes('AWS::EC2::SecurityGroup')) {
        signals.push({
          file: path.basename(cfTemplate),
          control: 'SC-7',
          evidence: 'Boundary protection via CloudFormation security groups'
        });
      }
      
      // IAM Policies
      if (content.includes('AWS::IAM::') || content.includes('PolicyDocument')) {
        signals.push({
          file: path.basename(cfTemplate),
          control: 'AC-3',
          evidence: 'Access enforcement via AWS IAM policies in CloudFormation'
        });
      }
      
      // Encryption
      if (content.match(/Encrypted.*true|KmsKeyId/i)) {
        signals.push({
          file: path.basename(cfTemplate),
          control: 'SC-28',
          evidence: 'Protection of information at rest via CloudFormation encryption'
        });
      }
    } catch (err) {
      // Ignore parsing errors
    }
  }
  
  return signals.map(assignConfidence);
}

function formatConfidenceBadge(signal: Partial<ComplianceSignal>): string {
  return signal.confidence ? ` [${signal.confidence.toUpperCase()}]` : '';
}

export function formatSignalsSummary(signals: ComplianceSignal[]): string {
  if (signals.length === 0) {
    return 'No compliance signals detected';
  }
  
  const grouped = signals.reduce((acc, signal) => {
    if (!acc[signal.control]) {
      acc[signal.control] = [];
    }
    acc[signal.control].push(signal);
    return acc;
  }, {} as Record<string, ComplianceSignal[]>);
  
  const lines: string[] = [];
  for (const [control, items] of Object.entries(grouped)) {
    lines.push(`✓ ${control}${formatConfidenceBadge(items[0])}: ${items[0].evidence} (${items.map(i => i.file).join(', ')})`);
  }
  
  return lines.join('\n');
}

/**
 * Format signals with AI validation results
 */
export function formatSignalsSummaryWithValidation(
  signals: ComplianceSignal[],
  validationResults: Map<string, any>
): string {
  if (signals.length === 0) {
    return 'No compliance signals detected';
  }
  
  const grouped = signals.reduce((acc, signal) => {
    if (!acc[signal.control]) {
      acc[signal.control] = [];
    }
    acc[signal.control].push(signal);
    return acc;
  }, {} as Record<string, ComplianceSignal[]>);
  
  const lines: string[] = [];
  for (const [control, items] of Object.entries(grouped)) {
    const key = `${control}:${items[0].file}`;
    const validation = validationResults.get(key);
    
    let statusIcon = '✓';
    let statusText = '';
    
    if (validation) {
      if (validation.validated && validation.confidence === 'high') {
        statusIcon = '✅';
        statusText = ' [AI: VERIFIED ✓]';
      } else if (validation.validated && validation.confidence === 'medium') {
        statusIcon = '⚠️ ';
        statusText = ' [AI: LIKELY ≈]';
      } else if (!validation.validated) {
        statusIcon = '❌';
        statusText = ' [AI: NOT VERIFIED ✗]';
      }
    }
    
    lines.push(`${statusIcon} ${control}${formatConfidenceBadge(items[0])}${statusText}: ${items[0].evidence} (${items.map(i => i.file).join(', ')})`);
  }
  
  return lines.join('\n');
}
