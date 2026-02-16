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
- 🤖 **AI-powered suggestions** using GitHub Copilot CLI - get context-aware implementation guidance
- ✅ **AI-powered validation** - verify implementations against OSCAL catalog requirements (not just pattern matching)
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

# Get AI-powered suggestions for missing controls
gh oscal suggest AC-2 .

# Understand a control
gh oscal explain AC-2 --for-devs
```

## 🎬 Full Workflow Demo

Here's how OSCALFLOW + GitHub Copilot CLI accelerates compliance from weeks to hours:

```bash
# 1. Generate baseline SSP (moderate = 243 NIST controls)
$ gh oscal generate --baseline moderate --system "FedChat API"
✓ Created ssp-draft.json with 243 controls

# 2. Scan your codebase for implemented controls
$ gh oscal scan . --update ssp-draft.json
🔍 Scanning ./backend...

✓ Found 48 control implementations:
  AC-17  Docker, Kubernetes configs detected
  AU-2   Winston logging in 12 files
  CM-3   GitHub Actions workflows
  IA-5   bcrypt password hashing
  SC-8   TLS/HTTPS configurations
  ... (43 more)

✗ Missing 195 controls

# 3. AI validate implementations (optional - higher confidence)
$ gh oscal scan . --ai-validate --ai-limit 10
✔ AI Validation: 7/10 controls verified

✅ AU-3 [AI: VERIFIED ✓]: Audit records properly implemented
✅ SC-5 [AI: VERIFIED ✓]: Rate limiting functional
❌ SC-2 [AI: NOT VERIFIED ✗]: Partial implementation detected
... (7 more)

# 4. Get AI suggestions for missing controls (save to file for reference)
$ gh oscal suggest AC-2 . --output compliance-docs/AC-2-plan.md
🤖 Analyzing codebase...
   Detected: Python, FastAPI, SQLAlchemy, PostgreSQL
💾 Saving session to: compliance-docs/AC-2-plan.md

💡 GitHub Copilot suggests for AC-2 (Account Management):

   1. Enhance User model with lifecycle fields
      File: models/__init__.py
      
   2. Create AccountManagementService 
      File: services/account_management.py
      
   3. Add admin endpoints for account operations
      File: api/v1/admin.py

[Full implementation details with YOUR code style...]

✓ Recommendations saved to: compliance-docs/AC-2-plan.md

# 5. Implement the suggestions
$ # ... add the code Copilot suggested ...
$ # (refer to saved file for complete implementation plan)

# 6. Rescan to verify implementation  
$ gh oscal scan . --update ssp-draft.json
✓ Found 49 control implementations (+1: AC-2)

# 7. Export final documentation
$ gh oscal export ssp-draft.json --output report.html
✓ Generated report.html (ATO-ready documentation)
```

**Result:** 20% auto-detected + AI-guided implementation = Weeks of work → Days

---

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

Auto-detect compliance implementations from your repository. Optionally validate implementations with AI using GitHub Copilot CLI + OSCAL catalog requirements.

```bash
gh oscal scan . --update ssp-draft.json

# AI-powered validation: verify implementations against NIST 800-53 requirements
gh oscal scan . --ai-validate --ai-limit 10
```

**Options:**
- `-u, --update <file>` - SSP file to update with findings
- `-o, --output <file>` - Save scan results to file
- `--enable <detectors>` - Enable only selected detectors (comma-separated)
- `--disable <detectors>` - Disable selected detectors (comma-separated)
- `-q, --quiet` - Reduce console output (CI-friendly)
- `--no-tips` - Suppress tips and guidance text
- `--pager` - Show findings with pager (`less`)
- `--ai-validate` 🤖 - Use AI (Copilot CLI) to validate control implementations against OSCAL requirements
- `--ai-limit <number>` - Limit number of controls to validate (useful for testing)

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

**🤖 AI Validation (--ai-validate):**

Beyond pattern detection, OSCALFlow can validate implementations using GitHub Copilot CLI + NIST 800-53 Rev 5 OSCAL catalog:

```bash
# Quick test with 5 controls
gh oscal scan . --ai-validate --ai-limit 5

# Full validation (may take 5-10 min for 50 controls)
gh oscal scan . --ai-validate
```

> ⚠️ **COST WARNING**: OSCALFlow uses `gpt-5-mini` by default to avoid consuming premium request quotas. With 50 controls, validation makes ~50 AI calls. Using premium models (claude-sonnet-4.5, gpt-5.2) could exhaust your GitHub Copilot request limits quickly. **Always test with `--ai-limit 5` first** before running full validation.

**How it works:**
1. Pattern scanner detects controls (fast - seconds)
2. For each control, extracts authoritative requirements from NIST OSCAL catalog
3. Sends file content + requirements to Copilot CLI with structured prompt (using `gpt-5-mini` by default)
4. AI analyzes if code actually implements the requirement (not just pattern matching)
5. Returns validation status with confidence level

**Output:**
- ✅ **VERIFIED ✓** - AI confirmed proper implementation  
- ⚠️ **LIKELY ≈** - Partial implementation or medium confidence
- ❌ **NOT VERIFIED ✗** - Pattern detected but incomplete/incorrect implementation

**Example:**
```bash
$ gh oscal scan Test_Case/FedChat --ai-validate --ai-limit 5

✔ AI Validation: 2/5 controls verified

✅ AU-3 [AI: VERIFIED ✓]: Audit record content with timestamp/user/event
✅ SC-5 [AI: VERIFIED ✓]: Rate limiting middleware properly implemented  
❌ SC-2 [AI: NOT VERIFIED ✗]: Docker Compose present but no management separation
❌ AU-2 [AI: NOT VERIFIED ✗]: Logging exists but incomplete audit event coverage
```

**Prerequisites:**
- Install GitHub Copilot CLI: `gh extension install github/gh-copilot`
- **Default model: `gpt-5-mini`** (cost-efficient, ~50 requests for full project scan)
- **Avoid premium models** unless needed - they will consume your request quota rapidly
- No hallucination - validates against official NIST 800-53 Rev 5 OSCAL catalog (254,987 lines, authoritative source)

**Use cases:**
- **Pre-ATO audits**: Get higher confidence before assessor review
- **CI/CD gates**: Fail builds if critical controls not properly implemented  
- **Evidence generation**: Show AI analysis alongside pattern detection
- **Testing**: Use `--ai-limit` to validate specific controls quickly

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

### `gh oscal suggest` 🤖 **NEW: AI-Powered with GitHub Copilot CLI**

Get context-aware implementation suggestions for NIST controls by combining your codebase analysis with GitHub Copilot's AI.

```bash
gh oscal suggest AC-2              # Get suggestions for Account Management
gh oscal suggest SC-8 ./my-app     # Analyze specific path  
gh oscal suggest IA-5 --no-context # Skip control info display
```

**✨ What makes this powerful:**

Instead of generic StackOverflow answers, `gh oscal suggest`:
1. **Detects YOUR stack** - Automatically identifies languages (Python, Node.js, Go, Rust, Java, Ruby), frameworks (FastAPI, Express, Django, Spring Boot), and infrastructure (Docker, Kubernetes, Terraform)
2. **Reads YOUR code** - Analyzes actual files to understand your project structure
3. **Asks Copilot specifically** - Builds context-rich prompts combining NIST requirements + your detected stack + your project layout
4. **Provides YOUR-code-style suggestions** - Get implementation steps that match your existing patterns

**Real example output:**
```bash
$ gh oscal suggest AC-2 ./backend

🔍 Analyzing codebase...
   Detected: Python, FastAPI, SQLAlchemy, Docker

🤖 GitHub Copilot Suggestion:

## NIST 800-53 AC-2 Implementation Guide

### 1. ENHANCE USER MODEL
File: backend/models/__init__.py

Add account lifecycle fields:
```python
account_status = Column(String(50), default="active")
disabled_at = Column(DateTime(timezone=True))
# ... with your SQLAlchemy conventions
```

### 2. CREATE ACCOUNT MANAGEMENT SERVICE  
File: backend/services/account_management.py
# ... FastAPI-specific implementation
```

**Prerequisites:**
- Install: `gh extension install github/gh-copilot`
- Authenticate: `gh auth login`
- See [SUGGEST_COMMAND.md](./SUGGEST_COMMAND.md) for detailed usage

**How it works:**
1. Scans your directory for tech stack indicators (package.json, requirements.txt, go.mod, etc.)
2. Detects frameworks by checking imports and config files
3. Builds a compound prompt: `NIST requirement + Developer guidance + Detected stack + Project context`
4. Executes: `gh copilot -- -p "<context-rich-prompt>" --allow-all-tools`
5. Copilot analyzes your actual files and provides specific, actionable steps

**Supported detection:**
- **Languages:** JavaScript/TypeScript, Python, Go, Rust, Java, Ruby
- **Frameworks:** Express, NestJS, Fastify, Django, FastAPI, Flask, Gin, Echo, Spring Boot, Rails
- **Infrastructure:** Docker, Kubernetes, Terraform, Ansible, CloudFormation
- **17 NIST Control Families:** AC, AU, CM, IA, RA, SA, SC, SI with developer-friendly guidance

**Options:**
- `-o, --output <file>` - Save Copilot session to markdown file for future reference
- `--no-context` - Skip showing control information before suggestions
- `[path]` - Repository path to analyze (default: current directory)

**Example with file output:**
```bash
# Save recommendations to file
gh oscal suggest AC-2 . --output AC-2-recommendations.md

# Build a recommendations library
mkdir compliance-docs
gh oscal suggest AC-2 . -o compliance-docs/AC-2.md
gh oscal suggest IA-5 . -o compliance-docs/IA-5.md
gh oscal suggest SC-8 . -o compliance-docs/SC-8.md
```

💡 **Pro tip:** Use after `gh oscal scan .` to get suggestions for missing controls, implement them, then rescan to verify!

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
