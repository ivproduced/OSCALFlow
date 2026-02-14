# 🚀 gh-oscal Setup & Installation Guide

Complete guide to installing and using the `gh-oscal` CLI tool.

## Prerequisites

Before installing, ensure you have:

- ✅ **Node.js 18+** - [Download](https://nodejs.org/)
- ✅ **GitHub CLI** - [Install](https://cli.github.com/)
- ✅ **npm** (comes with Node.js)

### Verify Prerequisites

```bash
node --version    # Should be 18.0.0 or higher
npm --version     # Should be 8.0.0 or higher
gh --version      # Should be 2.0.0 or higher
```

## Installation Steps

### Step 1: Clone the Repository

```bash
cd ~/projects  # or your preferred directory
git clone https://github.com/euCann/gh-oscal.git
cd gh-oscal/OSCAL-GRC-SKILLS
```

### Step 2: Install Dependencies

```bash
npm install
```

This will automatically:
- Install all required packages
- Build the TypeScript code
- Copy templates to the dist folder

### Step 3: Make Binary Executable

```bash
chmod +x bin/gh-oscal
```

### Step 4: Install as GitHub CLI Extension

```bash
gh extension install .
```

### Step 5: Verify Installation

```bash
gh oscal --version
gh oscal --help
```

You should see:
```
Usage: gh-oscal [options] [command]

GitHub CLI extension for OSCAL compliance automation
...
```

## 🎯 Quick Test

Run these commands to verify everything works:

```bash
# 1. Generate an SSP
gh oscal generate --baseline low --system "Test" -o test.json

# 2. Scan this repository
gh oscal scan . --update test.json

# 3. Explain a control
gh oscal explain SC-8
```

## 📦 Project Structure After Build

```
OSCAL-GRC-SKILLS/
├── bin/
│   └── gh-oscal              # Executable ✓
├── dist/                     # Compiled JavaScript ✓
│   ├── commands/
│   ├── lib/
│   ├── templates/            # JSON templates ✓
│   └── index.js
├── src/                      # TypeScript source
├── node_modules/             # Dependencies ✓
└── package.json
```

## 🔧 Troubleshooting

### Issue: "command not found: gh oscal"

**Solution:**
```bash
# Check if gh is installed
gh --version

# Reinstall extension
gh extension remove oscal
cd /path/to/OSCAL-GRC-SKILLS
gh extension install .
```

### Issue: "Cannot find module 'node:fs'"

**Solution:**
```bash
# Update Node.js to version 18+
node --version

# If < 18, download from nodejs.org
# Then rebuild:
npm install
npm run build
```

### Issue: Build errors or TypeScript errors

**Solution:**
```bash
# Clean reinstall
rm -rf node_modules package-lock.json dist
npm install
npm run build
```

### Issue: "ENOENT: no such file or directory, open '...ssp-skeleton.json'"

**Solution:**
```bash
# Templates not copied, rebuild:
npm run build

# Verify templates exist:
ls dist/templates/
```

### Issue: Permission denied when running gh oscal

**Solution:**
```bash
chmod +x bin/gh-oscal
```

## 🔄 Updating

To update to the latest version:

```bash
cd /path/to/OSCAL-GRC-SKILLS
git pull origin main
npm install
npm run build
```

## 🗑️ Uninstalling

```bash
gh extension remove oscal
```

## 📚 Next Steps

Once installed, check out:
- [CLI_USAGE.md](./CLI_USAGE.md) - Detailed usage guide
- [examples/demo-api/](./examples/demo-api/) - Sample project
- `./demo.sh` - Interactive demo script

## 🎥 Run the Demo

```bash
./demo.sh
```

This will walk you through:
1. Generating an SSP
2. Scanning a repository
3. Understanding controls
4. Viewing the output

## 💡 Development Mode

If you want to contribute or modify the tool:

```bash
# Run in development mode (auto-reload)
npm run dev

# Or test directly without installing as gh extension
node dist/index.js generate --help
node dist/index.js scan examples/demo-api
```

## 🌐 Alternative: Run Without GitHub CLI

You can use the tool directly with Node.js:

```bash
node dist/index.js generate --baseline moderate --system "My System"
node dist/index.js scan . --output results.json
node dist/index.js explain AC-2
```

## 📊 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Node.js | 18.0.0 | 20.x LTS |
| npm | 8.0.0 | 10.x |
| RAM | 512 MB | 1 GB |
| Disk Space | 100 MB | 500 MB |
| OS | macOS, Linux, Windows | Any |

## ✅ Installation Checklist

- [ ] Node.js 18+ installed
- [ ] GitHub CLI installed
- [ ] Repository cloned
- [ ] `npm install` completed
- [ ] `npm run build` successful
- [ ] `chmod +x bin/gh-oscal` executed
- [ ] `gh extension install .` completed
- [ ] `gh oscal --version` works
- [ ] Test commands successful

## 🆘 Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Review [CLI_USAGE.md](./CLI_USAGE.md)
3. Run `gh oscal <command> --help`
4. Check [GitHub Issues](https://github.com/euCann/gh-oscal/issues)

## 📝 Quick Reference Card

```bash
# Installation
gh extension install .

# Generate SSP
gh oscal generate -b moderate -s "System Name" -o ssp.json

# Scan repository
gh oscal scan . -u ssp.json

# Explain control
gh oscal explain AC-2

# Get help
gh oscal --help
gh oscal <command> --help
```

---

**Ready to automate compliance!** 🎉

Start with: `gh oscal generate --help`
