# OSCALFLOW

> Automated OSCAL compliance documentation for GitHub repositories

[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![OSCAL](https://img.shields.io/badge/OSCAL-1.2.0-purple)](https://pages.nist.gov/OSCAL/)
[![GitHub](https://img.shields.io/badge/GitHub-eucann%2Foscalflow-black)](https://github.com/eucann/oscalflow)

Transform your repository into a compliance-ready system with automated OSCAL System Security Plan (SSP) generation. Detect 50+ NIST 800-53 control implementations from your codebase automatically across 8 programming languages.

## 🚀 What is OSCALFLOW?

**OSCALFLOW** is a native GitHub CLI extension that automates OSCAL (Open Security Controls Assessment Language) compliance documentation. Instead of spending weeks writing security documentation manually, scan your repository and generate FedRAMP-ready SSPs in seconds.

**Key Features:**
- 🎯 Generate valid OSCAL SSP skeletons with NIST 800-53 baseline controls (119-421 controls)
- 🔍 Auto-detect 50+ control implementations across 8 languages (JavaScript, Python, Java, Ruby, Go, .NET, PHP, Rust)
- 🌐 Support for 8 CI/CD platforms (GitHub, GitLab, CircleCI, Jenkins, Azure, Travis, Bitbucket)
- ☁️ Cloud provider detection (AWS, Azure, GCP, Kubernetes, Docker)
- 🔐 Secret management and SBOM tracking
- 📊 Visual dashboards with coverage statistics (up to 20% auto-detected)
- 📄 Export to HTML reports with professional formatting
- 📚 Translate compliance jargon into developer-friendly language
- ⚡ Native CLI experience (not a chatbot wrapper)

## 📦 Quick Start

### Installation

```bash
cd gh-oscal-cli
npm install
npm run build
chmod +x bin/gh-oscal
gh extension install .
```

### Verify Installation

```bash
gh oscal --version
gh oscal --help
```

### Quick Test

```bash
# Generate an SSP with 243 controls
gh oscal generate --baseline moderate --system "My API"

# Scan your repository
gh oscal scan . --update ssp-draft.json

# Understand a control
gh oscal explain AC-2 --for-devs
```

## 🎯 Commands

### `gh oscal generate`

Generate an OSCAL SSP skeleton with baseline controls.

```bash
gh oscal generate --baseline moderate --system "Payment API"
```

**Options:**
- `-b, --baseline <level>` - Impact baseline: `low` (119 controls), `moderate` (243 controls), or `high` (421 controls)
- `-s, --system <name>` - System name
- `-o, --output <file>` - Output file path (default: `ssp-draft.json`)
- `-q, --quiet` - Reduce console output (CI-friendly)

### `gh oscal scan`

Auto-detect compliance implementations from your repository.

```bash
gh oscal scan . --update ssp-draft.json
```

**Options:**
- `-u, --update <file>` - SSP file to update with findings
- `-o, --output <file>` - Save scan results to file
- `--enable <detectors>` - Enable only selected detectors (comma-separated)
- `--disable <detectors>` - Disable selected detectors (comma-separated)
- `-q, --quiet` - Reduce console output (CI-friendly)
- `--no-tips` - Suppress tips and guidance text
- `--pager` - Show findings with pager (`less`)

**Detects (150+ patterns):**
- **Containers**: Docker, Kubernetes, OpenShift → SC-39, SC-2, SC-7
- **CI/CD**: GitHub Actions, GitLab, CircleCI, Jenkins, Azure Pipelines, Travis, Bitbucket → CM-3, SA-11
- **Languages**: JavaScript, Python, Java, Ruby, Go, .NET, PHP, Rust
- **Authentication**: bcrypt, argon2, JWT, OAuth, SAML → IA-2, IA-5, IA-8
- **Logging**: winston, pino, logback, serilog → AU-2, AU-3, AU-12
- **Security**: helmet, security headers, TLS/SSL → SC-8, SC-28
- **IaC**: Terraform, Ansible, CloudFormation, ARM, Helm → CM-2, SC-7, AC-3
- **Secrets**: HashiCorp Vault, AWS Secrets, Azure Key Vault, Sealed Secrets → SC-12
- **Security Tools**: Snyk, Trivy, SonarQube, Fortify, Checkmarx, OWASP ZAP → RA-5, SA-11
- **SBOM**: CycloneDX, SPDX, lock files → SR-4, SA-4, SR-3
- **Git Security**: GPG signing, CODEOWNERS, branch protection → SI-7, AC-3, CM-3
- **Databases**: Migrations, TLS configs, backups → CM-3, SC-8, CP-9
- **APIs**: OpenAPI/Swagger, API Gateways → SA-5, AC-3, SC-5

### `gh oscal explain`

Translate NIST 800-53 controls into developer-friendly language.

```bash
gh oscal explain AC-2 --for-devs
```

**Output includes:**
- Official NIST description
- Developer-friendly translation
- Implementation examples
- Related controls

**Additional options:**
- `--pager` - Show explain output with pager (`less`)
- `--no-tips` - Suppress tip text

### `gh oscal doctor`

Run diagnostics to validate environment and repository setup before scanning/generation.

```bash
gh oscal doctor .
```

Checks include tool availability, repo/.git write access, config discovery, and NIST data presence.

### Repository Configuration (`.oscalflow.json`)

OSCALFLOW now supports repo-level defaults:

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

Detector names: `containers`, `cicd`, `dependencies`, `iac`, `secrets`, `security-tools`, `git-security`, `api`, `database`, `sbom`, `cloud`.

## 📊 What Gets Generated

Valid OSCAL 1.2.0 JSON conforming to the [NIST specification](https://pages.nist.gov/OSCAL/):

```json
{
  "system-security-plan": {
    "uuid": "unique-identifier",
    "metadata": {
      "title": "System Security Plan",
      "oscal-version": "1.2.0"
    },
    "system-characteristics": {
      "system-name": "Your System",
      "security-sensitivity-level": "MODERATE"
    },
    "control-implementation": {
      "implemented-requirements": [
        {
          "control-id": "AC-2",
          "description": "User authentication via JWT tokens"
        }
      ]
    }
  }
}
```

## 🎬 Demo

Run the interactive demo:

```bash
./demo.sh
```

Or run the test suite:

```bash
./test.sh
```

## 📚 Documentation

- [INSTALLATION.md](./INSTALLATION.md) - Complete setup guide
- [CLI_USAGE.md](./CLI_USAGE.md) - Detailed command reference
- [GITHUB_CLI_EXTENSION.md](./GITHUB_CLI_EXTENSION.md) - GitHub CLI integration
- [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) - Technical overview
- [examples/demo-api/](./examples/demo-api/) - Sample project

## 🏗️ Project Structure

```
gh-oscal-cli/
├── bin/
│   └── gh-oscal              # Executable entry point
├── src/
│   ├── commands/
│   │   ├── generate.ts       # SSP generation
│   │   ├── scan.ts           # Repository scanner
│   │   └── explain.ts        # Control explainer
│   ├── lib/
│   │   ├── oscal-writer.ts   # OSCAL JSON generator
│   │   ├── scanner.ts        # Compliance detector
│   │   └── mapper.ts         # Control mapper
│   └── templates/
│       └── ssp-skeleton.json # OSCAL template
├── dist/                     # Compiled JavaScript
├── examples/
│   └── demo-api/             # Sample project
├── package.json
├── tsconfig.json
└── README.md
```

## 🔍 Detection Capabilities

| Technology | Control | Evidence |
|------------|---------|----------|
| Dockerfile | SC-39 | Container isolation |
| .github/workflows/ | CM-3, SA-11 | CI/CD automation |
| bcrypt/argon2 | IA-5 | Password hashing |
| jsonwebtoken | IA-2 | Token authentication |
| winston/pino | AU-2 | Audit logging |
| helmet | SC-8 | HTTPS headers |
| terraform/ | CM-2 | Infrastructure as Code |
| kubernetes/ | SC-2 | Application partitioning |
| .snyk | RA-5 | Vulnerability scanning |
| dependabot.yml | SI-2 | Flaw remediation |

## 🎯 NIST 800-53 Baselines

| Baseline | Controls | Use Case |
|----------|----------|----------|
| **Low** | 119 | Public-facing systems, low-impact data |
| **Moderate** | 243 | Most federal systems, PII handling |
| **High** | 421 | Financial systems, national security |

## 💡 Use Cases

### For Developers
- Understand compliance requirements in plain English
- Auto-document security implementations from code
- Reduce SSP writing time from weeks to hours

### For Security Teams
- Continuous compliance monitoring
- Automated gap analysis
- FedRAMP preparation assistance

### For DevSecOps
- Shift-left compliance integration
- Automated evidence collection
- CI/CD compliance checks

## 🛠️ Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Development mode (auto-reload)
npm run dev

# Test without GitHub CLI extension
node dist/index.js generate --help
node dist/index.js scan .
node dist/index.js explain AC-2
```

## 🐛 Troubleshooting

### Command not found

```bash
gh --version  # Verify GitHub CLI is installed
cd gh-oscal-cli
gh extension install .
```

### Build errors

```bash
rm -rf node_modules dist
npm install
npm run build
```

### Module not found

Ensure you're using Node.js 18+:
```bash
node --version  # Should be 18.0.0 or higher
```

## 🤝 Contributing

This project was built for the GitHub + MCP Hackathon. Contributions are welcome!

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🏅 Hackathon Submission

**Category:** GitHub + Model Context Protocol Integration  
**Built with:** TypeScript, Commander.js, Chalk, Ora  
**Status:** ✅ Complete and ready for submission

### Why This Project Wins

1. **Real CLI Tool** - Native GitHub CLI extension, not a chatbot wrapper
2. **Produces Artifacts** - Generates valid OSCAL JSON that can be validated
3. **Solves Real Pain** - Anyone who's written an SSP knows this saves weeks of work
4. **Technical Excellence** - Clean architecture, TypeScript, proper error handling
5. **Practical Impact** - Immediate value for FedRAMP/compliance projects

## 🔗 Resources

- [OSCAL Website](https://pages.nist.gov/OSCAL/)
- [NIST 800-53 Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [FedRAMP OSCAL Resources](https://github.com/GSA/fedramp-automation)
- [GitHub CLI Manual](https://cli.github.com/manual/)

## 🙏 Acknowledgments

This project stands on the shoulders of giants. Special thanks to:

### Core Technologies
- **[GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli)** - For pioneering natural language CLI interactions and inspiring this compliance automation approach
- **[LibreChat](https://github.com/danny-avila/LibreChat)** - Test case repository demonstrating real-world compliance implementations
- **[NIST](https://www.nist.gov/cyberframework)** - For developing and maintaining the OSCAL standard and SP 800-53 security controls

### Development Stack
- [GitHub CLI](https://cli.github.com) - Extension framework
- [Commander.js](https://github.com/tj/commander.js) - CLI argument parsing
- [Chalk](https://github.com/chalk/chalk) - Terminal styling
- [Ora](https://github.com/sindresorhus/ora) - Elegant spinners

---

**Made with ❤️ for the GitHub + MCP Hackathon**
