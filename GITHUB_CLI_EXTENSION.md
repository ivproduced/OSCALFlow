# Using gh-oscal as a GitHub CLI Extension

This guide covers installing and using `gh-oscal` as a proper GitHub CLI extension.

## Prerequisites

- GitHub CLI installed: `gh --version`
- Node.js 18+: `node --version`

## Installation as GitHub CLI Extension

### Option 1: Install from Local Directory (Development)

```bash
cd /path/to/OSCAL-GRC-SKILLS
npm install
npm run build
gh extension install .
```

### Option 2: Install from GitHub (Once Published)

```bash
gh extension install euCann/gh-oscal
```

## Verify Installation

```bash
gh oscal --version
gh oscal --help
```

You should see:
```
Usage: gh-oscal [options] [command]

GitHub CLI extension for OSCAL compliance automation
```

## Using the Extension

Once installed, use `gh oscal` instead of `node dist/index.js`:

### Generate SSP

```bash
gh oscal generate --baseline moderate --system "My API"
```

### Scan Repository

```bash
gh oscal scan . --update ssp-draft.json
```

### Explain Controls

```bash
gh oscal explain AC-2 --for-devs
```

## Extension Management

### List Installed Extensions

```bash
gh extension list
```

### Upgrade Extension

```bash
gh extension upgrade oscal
```

### Uninstall Extension

```bash
gh extension remove oscal
```

## Troubleshooting

### Extension Not Found

If `gh oscal` says "command not found":

1. Check GitHub CLI is installed:
   ```bash
   gh --version
   ```

2. Reinstall the extension:
   ```bash
   cd /path/to/OSCAL-GRC-SKILLS
   gh extension remove oscal
   gh extension install .
   ```

### Permission Errors

```bash
chmod +x bin/gh-oscal
```

### Update After Code Changes

```bash
cd /path/to/OSCAL-GRC-SKILLS
npm run build
gh extension remove oscal
gh extension install .
```

## Publishing to GitHub (Optional)

To make this installable by others:

1. Create a GitHub repository named `gh-oscal`
2. Push your code:
   ```bash
   git remote add origin https://github.com/euCann/gh-oscal.git
   git push -u origin main
   ```

3. Others can then install:
   ```bash
   gh extension install euCann/gh-oscal
   ```

## Integration with GitHub Workflows

Use in GitHub Actions:

```yaml
name: Generate SSP
on: [push]

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install gh-oscal
        run: |
          gh extension install euCann/gh-oscal
      
      - name: Generate SSP
        run: |
          gh oscal generate --baseline moderate --system "${{ github.repository }}"
          gh oscal scan . --update ssp-draft.json
      
      - name: Upload SSP
        uses: actions/upload-artifact@v3
        with:
          name: ssp
          path: ssp-draft.json
```

## Command Aliases (Optional)

Add to your shell profile (~/.bashrc or ~/.zshrc):

```bash
alias oscal='gh oscal'
alias oscal-gen='gh oscal generate'
alias oscal-scan='gh oscal scan'
alias oscal-explain='gh oscal explain'
```

Then use:
```bash
oscal-gen -b moderate -s "My System"
oscal-scan . -u ssp-draft.json
oscal-explain AC-2
```

## Tips

1. **Tab Completion**: GitHub CLI supports tab completion for extensions
2. **Help Text**: Use `--help` on any command for details
3. **Output Format**: All commands support standard output redirection
4. **Error Handling**: Commands exit with proper codes for scripting

## Example Workflows

### Daily Compliance Check

```bash
#!/bin/bash
# compliance-check.sh

gh oscal generate -b moderate -s "Production API" -o ssp.json
gh oscal scan . -u ssp.json
echo "SSP updated: $(date)" >> compliance.log
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

gh oscal scan . --output scan-results.json
if [ $(jq '.length' scan-results.json) -lt 5 ]; then
    echo "Warning: Low compliance signal count"
fi
```

### CI/CD Integration

```bash
# In your CI/CD pipeline
gh oscal generate --baseline high --system "$CI_PROJECT_NAME"
gh oscal scan . --update ssp-draft.json

# Validate output
if [ -f ssp-draft.json ]; then
    echo "SSP generated successfully"
else
    exit 1
fi
```

## Advanced Usage

### Custom Templates

Modify the template:
```bash
cd /path/to/OSCAL-GRC-SKILLS/src/templates
# Edit ssp-skeleton.json
npm run build
gh extension remove oscal
gh extension install .
```

### Adding Controls

Edit `src/commands/explain.ts` to add more controls to the database.

### Extending Scanner

Add detection patterns in `src/lib/scanner.ts`:
```typescript
// Add your pattern
if (fs.existsSync(path.join(repoPath, 'your-file'))) {
  signals.push({
    file: 'your-file',
    control: 'XX-##',
    evidence: 'Your evidence description'
  });
}
```

---

## Quick Reference

| Command | Shorthand | Description |
|---------|-----------|-------------|
| `gh oscal generate` | | Create SSP skeleton |
| `-b, --baseline` | | low/moderate/high |
| `-s, --system` | | System name |
| `-o, --output` | | Output file |
| `gh oscal scan` | | Scan repository |
| `-u, --update` | | Update SSP file |
| `gh oscal explain` | | Explain control |
| `--for-devs` | | Developer mode |
| `--json` | | JSON output |

---

**Ready to use!** Run `gh oscal --help` to get started.
