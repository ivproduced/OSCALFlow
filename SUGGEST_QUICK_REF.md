# Quick Reference: gh oscal suggest

## Syntax
```bash
gh oscal suggest <control-id> [path] [options]
```

## Arguments
- `<control-id>` - NIST 800-53 control ID (e.g., AC-2, SC-8)
- `[path]` - Repository path to analyze (default: current directory)

## Options
- `-o, --output <file>` - Save Copilot session to markdown file
- `--no-context` - Skip displaying control information before suggestions
- `-h, --help` - Display help

## Quick Examples

```bash
# Get suggestions for Account Management control
gh oscal suggest AC-2

# Analyze a specific directory
gh oscal suggest SC-8 ./backend

# Skip control info display
gh oscal suggest IA-5 --no-context

# Save recommendations to file
gh oscal suggest AC-2 . --output AC-2-recommendations.md

# Build a recommendations library
mkdir compliance-docs
gh oscal suggest AC-2 . -o compliance-docs/AC-2.md
```

## Supported Controls

| Family | Controls |
|--------|----------|
| **Access Control** | AC-1, AC-2, AC-3 |
| **Audit & Accountability** | AU-2 |
| **Configuration Management** | CM-2, CM-3 |
| **Identification & Authentication** | IA-2, IA-5 |
| **Risk Assessment** | RA-5 |
| **System & Services Acquisition** | SA-11 |
| **System & Communications Protection** | SC-2, SC-7, SC-8, SC-12, SC-13, SC-39 |
| **System & Information Integrity** | SI-2 |

## What Gets Detected

### Languages
- JavaScript/TypeScript/Node.js (package.json)
- Python (requirements.txt, setup.py)
- Go (go.mod)
- Rust (Cargo.toml)
- Java (pom.xml, build.gradle)
- Ruby (Gemfile)

### Frameworks
- Express.js, Fastify, NestJS
- React, Vue, Angular, Next.js
- And more from package.json

### Infrastructure
- Docker (Dockerfile, docker-compose.yml)
- Kubernetes (kubernetes/ or k8s/ directory)
- Terraform (terraform/ directory)
- GitHub Actions (.github/workflows/)

## Integration Workflow

```bash
# 1. Scan current state
gh oscal scan .

# 2. Get suggestions for missing controls
gh oscal suggest AC-2

# 3. Implement the suggestions
# (manually edit code based on AI suggestions)

# 4. Verify implementation
gh oscal scan . --update ssp.json

# 5. Repeat for other controls
gh oscal suggest SC-8
```

## Prerequisites

Before using this command, ensure you have:

1. **GitHub CLI** installed
   ```bash
   brew install gh  # macOS
   ```
   Or visit: https://cli.github.com/

2. **Copilot extension** installed
   ```bash
   gh extension install github/gh-copilot
   ```

3. **Authenticated** with GitHub
   ```bash
   gh auth login
   ```

## What Copilot Provides

When you run the suggest command, GitHub Copilot will analyze your codebase and provide:

1. **Specific files** to create or modify
2. **Code snippets** ready to use
3. **Commands to run** (e.g., npm install packages)
4. **Dependencies to add** with installation instructions
5. **Architecture recommendations** for compliance
6. **Configuration changes** needed

## Example Output Flow

```
$ gh oscal suggest AC-2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AC-2: Account Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Manage system accounts including creation, enablement,
modification, disabling, and removal.

💡 Implement proper user lifecycle management with audit
   logging for all account operations.

🤖 Getting implementation suggestions from GitHub Copilot CLI...

[Copilot provides interactive, codebase-specific suggestions]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Next steps:
  • Run 'gh oscal explain AC-2' for more control details
  • Run 'gh oscal scan .' to verify implementation
  • Run 'gh oscal generate' to update your SSP
```

## Tips

- **Start with high-impact controls**: AC (Access), IA (Auth), SC (Security)
- **Review before implementing**: Always review AI suggestions carefully
- **Iterate**: Scan → Suggest → Implement → Verify → Repeat
- **Combine with explain**: Use `gh oscal explain <control>` first to understand requirements

## Troubleshooting

### "GitHub CLI with Copilot extension is not installed"
Install gh CLI and the Copilot extension (see Prerequisites above)

### "Control XYZ not found in database"  
The demo includes 17 commonly-used controls. Check available controls with:
```bash
gh oscal suggest --help
```

### "Path not found"
Verify the path exists and is accessible:
```bash
ls /path/to/repo
```

## Related Commands

- `gh oscal scan [path]` - Detect current compliance signals
- `gh oscal explain <control>` - Learn about control requirements
- `gh oscal generate` - Create SSP skeleton
- `gh oscal doctor` - Check environment setup

## Learn More

- [Full Documentation](./SUGGEST_COMMAND.md)
- [NIST 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli)
