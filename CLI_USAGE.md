# gh-oscal CLI Tool - Installation & Usage Guide

This guide covers the installation and usage of the `gh-oscal` GitHub CLI extension.

## 🚀 Quick Start

### Installation

```bash
cd /path/to/OSCAL-GRC-SKILLS
npm install
npm run build
chmod +x bin/gh-oscal
gh extension install .
```

### Verify

```bash
gh oscal --version
gh oscal --help
```

## 📖 Commands

### Generate SSP Skeleton

Create a valid OSCAL System Security Plan with NIST 800-53 baseline controls:

```bash
gh oscal generate --baseline moderate --system "My API"
```

**Options:**
- `-b, --baseline <level>`: `low`, `moderate`, or `high` (default: moderate)
- `-s, --system <name>`: System name (default: Unnamed System)
- `-o, --output <file>`: Output file (default: ssp-draft.json)
- `-q, --quiet`: Reduce console output (CI-friendly)

### Scan Repository

Auto-detect compliance implementations:

```bash
gh oscal scan . --update ssp-draft.json
```

**Arguments:**
- `[path]`: Repository path (default: `.`)

**Options:**
- `-u, --update <file>`: SSP file to update
- `-o, --output <file>`: Save scan results
- `--enable <detectors>`: Enable only selected detectors (comma-separated)
- `--disable <detectors>`: Disable selected detectors (comma-separated)
- `-q, --quiet`: Reduce console output (CI-friendly)
- `--no-tips`: Suppress tips/guidance text
- `--pager`: Show findings in pager (`less`)

### Explain Controls

Translate NIST controls to developer language:

```bash
gh oscal explain AC-2 --for-devs
```

**Arguments:**
- `<control-id>`: NIST control ID (e.g., AC-2, IA-5, SC-8)

**Options:**
- `--for-devs`: Developer-friendly output (default: true)
- `--json`: Output as JSON
- `--pager`: Show output in pager (`less`)
- `--no-tips`: Suppress tips/guidance text

### Doctor Diagnostics

Run environment and repository checks before scanning/generating:

```bash
gh oscal doctor .
```

**Checks include:**
- Node.js and tool availability (`gh`, `git`)
- repository and `.git` write access
- optional `.oscalflow.json` discovery
- required NIST baseline data files

## ⚙️ Repository Config (`.oscalflow.json`)

You can set per-repository defaults:

```json
{
  "baseline": "moderate",
  "systemName": "Payment API",
  "defaultOutput": "ssp-draft.json",
  "scanOutput": "scan-results.json",
  "quiet": false,
  "suppressTips": true,
  "pager": false,
  "enabledDetectors": ["containers", "cicd", "dependencies"],
  "disabledDetectors": ["sbom"]
}
```

Available detector names:
- `containers`, `cicd`, `dependencies`, `iac`, `secrets`, `security-tools`, `git-security`, `api`, `database`, `sbom`, `cloud`

## 🎯 Example Workflow

```bash
# 1. Generate SSP skeleton
gh oscal generate --baseline moderate --system "Payment API"

# 2. Scan your repository
gh oscal scan . --update ssp-draft.json

# 3. Review the generated SSP
cat ssp-draft.json | jq '.["system-security-plan"]["control-implementation"]["implemented-requirements"] | length'

# 4. Understand specific controls
gh oscal explain SC-8 --for-devs
```

## 🔍 What Gets Detected (150+ Patterns)

The scanner recognizes compliance signals across 8 programming languages and cloud platforms:

### Languages Supported
| Language | Package Manager | Security Libraries Detected |
|----------|----------------|-----------------------------|
| JavaScript/TypeScript | package.json | bcrypt, argon2, jsonwebtoken, winston, pino, helmet |
| Python | requirements.txt | cryptography, passlib, bcrypt, pyjwt, django, flask |
| Java | pom.xml, build.gradle | spring-security, bcrypt, logback, slf4j, jjwt |
| Ruby | Gemfile | devise, bcrypt, omniauth |
| Go | go.mod | bcrypt, jwt-go, logrus, zap |
| .NET | packages.config, .csproj | BCrypt.Net, IdentityServer, Serilog |
| PHP | composer.json | laravel, symfony, jwt, monolog |
| Rust | Cargo.toml | argon2, bcrypt, jsonwebtoken, log, tracing |

### CI/CD Platforms (8 Supported)
| Platform | File | Controls Detected |
|----------|------|------------------|
| GitHub Actions | .github/workflows/ | CM-3, SA-11 |
| GitLab CI | .gitlab-ci.yml | CM-3, SA-11 |
| CircleCI | .circleci/config.yml | CM-3, SA-11 |
| Jenkins | Jenkinsfile | CM-3, SA-11 |
| Azure Pipelines | azure-pipelines.yml | CM-3, SA-11 |
| Travis CI | .travis.yml | CM-3, SA-11 |
| Bitbucket | bitbucket-pipelines.yml | CM-3, SA-11 |
| Dependabot | .github/dependabot.yml | SI-2 |

### Infrastructure & Cloud
| Technology | Controls | Evidence |
|------------|----------|----------|
| Docker/Kubernetes | SC-39, SC-2, SC-7, SC-6, AC-3 | Container isolation, RBAC, NetworkPolicy, resource limits |
| Terraform | CM-2, CM-6 | Infrastructure as Code |
| AWS CloudFormation | CM-2, SC-7, AC-3, SC-28 | IaC, security groups, IAM, encryption |
| Azure ARM | CM-2 | Azure Resource Manager templates |
| GCP Deployment Manager | CM-2 | Google Cloud IaC |
| Ansible | CM-2 | Configuration management |
| Helm | CM-2 | Kubernetes package management |

### Security Tools
| Tool | Controls | Purpose |
|------|----------|----------|
| Snyk | RA-5 | Vulnerability scanning |
| Trivy | RA-5 | Container scanning |
| SonarQube | SA-11, RA-5 | SAST |
| Fortify | SA-11 | Static analysis |
| Checkmarx | SA-11 | SAST |
| OWASP ZAP | SA-11 | DAST |
| GitLeaks/GitGuardian | RA-5, SC-12 | Secret detection |

### Secret Management
| System | Controls | Description |
|--------|----------|-------------|
| HashiCorp Vault | SC-12, SC-28 | Enterprise secret management |
| AWS Secrets Manager | SC-12 | AWS secret storage |
| Azure Key Vault | SC-12 | Azure secret management |
| Kubernetes Sealed Secrets | SC-12, SC-28 | K8s encrypted secrets |

### SBOM & Supply Chain
| Format | Controls | Evidence |
|--------|----------|----------|
| CycloneDX | SR-4, SA-4 | Software bill of materials |
| SPDX | SR-4 | Open source SBOM |
| Lock files | SA-15, SR-3 | Dependency pinning (package-lock.json, yarn.lock, Gemfile.lock, etc.) |

### API Security
| Technology | Controls | Description |
|------------|----------|-------------|
| OpenAPI/Swagger | SA-5, AC-3 | API documentation and security specs |
| API Gateway | SC-7, SC-5 | Boundary protection and rate limiting |

### Database Security
| Pattern | Controls | Evidence |
|---------|----------|----------|
| Migrations | CM-3 | Schema version control |
| TLS/SSL configs | SC-8 | Encrypted connections |
| Backup scripts | CP-9 | Data protection |

### Git Security
| Feature | Controls | Description |
|---------|----------|-------------|
| GPG-signed commits | SI-7, AU-10 | Software integrity and non-repudiation |
| CODEOWNERS | AC-3, CM-3 | Access control for code changes |
| Branch protection | CM-3 | Change approval process |

## 📊 Baseline Control Counts

- **Low**: 125 controls
- **Moderate**: 248 controls
- **High**: 421 controls

## 🛠️ Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Development mode
npm run dev

# Test locally (without gh extension)
node dist/index.js generate --help
```

## 📄 Output Format

Generated SSPs conform to OSCAL 1.2.0:

```json
{
  "system-security-plan": {
    "uuid": "a1b2c3d4...",
    "metadata": {
      "title": "System Security Plan Template",
      "oscal-version": "1.0.4"
    },
    "system-characteristics": {
      "system-name": "Your System",
      "security-sensitivity-level": "MODERATE"
    },
    "control-implementation": {
      "implemented-requirements": [
        {
          "control-id": "AC-2",
          "description": "Implementation evidence"
        }
      ]
    }
  }
}
```

## 🔗 Resources

- [Main README](./README.md) - Full project documentation
- [OSCAL Specification](https://pages.nist.gov/OSCAL/)
- [NIST 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [GitHub CLI Manual](https://cli.github.com/manual/)

## 🐛 Troubleshooting

### Command not found

```bash
# Verify GitHub CLI is installed
gh --version

# Reinstall extension
gh extension remove oscal
gh extension install .
```

### Type errors during build

```bash
# Make sure @types/node is installed
npm install --save-dev @types/node
```

### Module not found errors

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

**Part of the GitHub + MCP Hackathon submission**
