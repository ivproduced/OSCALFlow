# Suggest Command - AI-Powered NIST Control Implementation

## Overview

The `suggest` command provides AI-powered implementation suggestions for NIST 800-53 controls based on your specific codebase. It analyzes your project structure, detects languages and frameworks, then uses GitHub Copilot CLI to provide tailored, actionable implementation steps.

## Features

- **Codebase-Aware**: Automatically detects your tech stack (languages, frameworks, infrastructure)
- **Context-Rich Prompts**: Builds detailed prompts with control requirements and your project context
- **AI-Powered**: Leverages GitHub Copilot CLI for intelligent, project-specific suggestions
- **Actionable Output**: Get specific files to modify, code snippets, and commands to run

## Usage

```bash
# Get suggestions for a specific control
gh oscal suggest <control-id> [path]

# Examples:
gh oscal suggest AC-2              # Account Management for current directory
gh oscal suggest SC-8 ./my-app     # Transmission Security for specific path
gh oscal suggest IA-5 --no-context # Authenticator Management without control info
```

## How It Works

1. **Control Lookup**: Retrieves NIST 800-53 control details from the built-in database
2. **Codebase Analysis**: Scans your project to detect:
   - Programming languages (Node.js, Python, Go, Rust, Java, Ruby)
   - Frameworks (Express, React, Vue, Angular, NestJS, etc.)
   - Infrastructure (Docker, Kubernetes, Terraform, GitHub Actions)
3. **Prompt Building**: Creates a comprehensive prompt including:
   - Control description and guidance
   - Your project's tech stack
   - Example implementations
   - Request for specific, actionable steps
4. **AI Suggestions**: Shells out to `gh copilot` with the prompt
5. **Actionable Results**: Copilot provides tailored suggestions for your codebase

## Example Output

When you run `gh oscal suggest AC-2`, you might see:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AC-2: Account Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Manage system accounts including creation, enablement, modification, disabling, and removal.
💡 Implement proper user lifecycle management with audit logging for all account operations.

🤖 Getting implementation suggestions from GitHub Copilot CLI...

[GitHub Copilot provides interactive suggestions specific to your codebase]
```

## Options

- `-o, --output <file>`: Save the GitHub Copilot session to a markdown file for future reference
- `--no-context`: Skip showing control information before getting suggestions
- `[path]`: Specify a repository path to analyze (defaults to current directory)

### Saving Recommendations to a File

Use the `--output` flag to save the complete Copilot analysis and recommendations to a markdown file:

```bash
# Save recommendations for future reference
gh oscal suggest AC-2 . --output AC-2-recommendations.md

# Build a recommendations library
mkdir compliance-docs
gh oscal suggest AC-2 . -o compliance-docs/AC-2.md
gh oscal suggest IA-5 . -o compliance-docs/IA-5.md
gh oscal suggest SC-8 . -o compliance-docs/SC-8.md
```

The saved file includes:
- Complete codebase analysis steps
- Tech stack detection results
- Full implementation plan with code snippets
- NIST control mappings
- Testing and verification instructions

## Prerequisites

You need GitHub Copilot CLI installed:

```bash
# 1. Install GitHub CLI
brew install gh  # macOS
# or download from https://cli.github.com/

# 2. Install Copilot extension
gh extension install github/gh-copilot

# 3. Authenticate
gh auth login
```

## Supported Controls

The demo includes commonly-used NIST 800-53 controls:

- **AC-1**: Policy and Procedures
- **AC-2**: Account Management
- **AC-3**: Access Enforcement
- **AU-2**: Event Logging
- **CM-2**: Baseline Configuration
- **CM-3**: Configuration Change Control
- **IA-2**: Identification and Authentication
- **IA-5**: Authenticator Management
- **RA-5**: Vulnerability Monitoring and Scanning
- **SA-11**: Developer Testing and Evaluation
- **SC-2**: Separation of System and User Functionality
- **SC-7**: Boundary Protection
- **SC-8**: Transmission Confidentiality and Integrity
- **SC-12**: Cryptographic Key Establishment and Management
- **SC-13**: Cryptographic Protection
- **SC-39**: Process Isolation
- **SI-2**: Flaw Remediation

## Integration with Other Commands

The `suggest` command integrates seamlessly with other OSCALFlow commands:

```bash
# 1. Scan your codebase for compliance signals
gh oscal scan .

# 2. Get suggestions for missing controls
gh oscal suggest AC-2

# 3. Implement the suggestions (manually or with Copilot)

# 4. Re-scan to verify implementation
gh oscal scan . --update ssp.json

# 5. Generate compliance report
gh oscal export ssp.json -o report.html
```

## Example Workflow

```bash
# Step 1: Scan to find what's missing
$ gh oscal scan .
Found 12 compliance signals
Coverage: 12/243 controls (4.9% of MODERATE baseline)

# Step 2: Pick a missing control and get suggestions
$ gh oscal suggest IA-5
# Copilot suggests: "Add bcrypt for password hashing..."

# Step 3: Implement the suggestions
$ npm install bcrypt
$ # Edit your code based on suggestions

# Step 4: Verify the implementation
$ gh oscal scan . --update ssp.json
Found 13 compliance signals (+1)

# Step 5: Get suggestions for another control
$ gh oscal suggest AU-2
```

## Tips

- **Start with High-Impact Controls**: Focus on AC (Access Control), IA (Authentication), and SC (System/Communications) families first
- **Verify Suggestions**: Always review AI suggestions before implementing
- **Iterate**: Re-scan after each implementation to track progress
- **Combine with Explain**: Use `gh oscal explain <control>` to understand the control before getting implementation suggestions

## Technical Details

### Codebase Detection

The command detects your project structure by checking for:

**Languages:**
- `package.json` → JavaScript/TypeScript/Node.js
- `requirements.txt` or `setup.py` → Python
- `go.mod` → Go
- `Cargo.toml` → Rust
- `pom.xml` or `build.gradle` → Java
- `Gemfile` → Ruby

**Frameworks:**
- Express.js, React, Vue, Angular, Next.js, Fastify, NestJS (from package.json dependencies)

**Infrastructure:**
- Docker (Dockerfile, docker-compose.yml)
- Kubernetes (kubernetes/ or k8s/ directories)
- Terraform (terraform/ directory)
- GitHub Actions (.github/workflows/)

### Prompt Structure

The generated prompt includes:
1. Control ID, title, and description
2. Developer-focused guidance
3. Detected codebase context (languages, frameworks, infrastructure)
4. Example implementations
5. Request for specific, actionable steps

### GitHub Copilot Integration

The command uses `gh copilot -p "<prompt>" --allow-tool 'shell(*)'` to:
- Pass the detailed prompt to Copilot
- Allow Copilot to suggest shell commands
- Run in interactive mode for follow-up questions

## Troubleshooting

**"GitHub CLI with Copilot extension is not installed"**
- Install `gh` CLI: https://cli.github.com/
- Install Copilot: `gh extension install github/gh-copilot`
- Authenticate: `gh auth login`

**"Control XYZ not found in database"**
- Check available controls: `gh oscal suggest --help`
- The demo includes ~17 commonly-used controls
- Full NIST 800-53 Rev 5 has 1000+ controls

**"Path not found"**
- Verify the path exists: `ls /path/to/repo`
- Use absolute or relative paths
- Default is current directory (`.`)

## Future Enhancements

Potential improvements for the suggest command:
- Add more controls to the database
- Support for control enhancements (e.g., AC-2(1), AC-2(2))
- Integration with `scan` results to auto-suggest missing controls
- Save suggestions to markdown files for later reference
- Custom prompt templates
- Support for organization-specific requirements

## Related Commands

- `gh oscal explain <control>` - Get detailed information about a control
- `gh oscal scan [path]` - Scan for existing compliance signals
- `gh oscal generate` - Generate SSP skeleton
- `gh oscal doctor` - Check environment setup

## Learn More

- [NIST 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli)
- [OSCALFlow Documentation](./README.md)
