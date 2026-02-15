# Changelog

All notable changes to this project are documented in this file.

## [1.1.0] - 2026-02-14

### Added
- New `gh oscal doctor` command for environment and repository diagnostics.
- Repository-level configuration support via `.oscalflow.json`.
- Detector filtering controls for scan: `--enable` and `--disable`.
- Optional pager support for long output in `scan` and `explain`.
- New test suite using Node built-in test runner:
  - Config parsing/discovery tests
  - Detector classification/filtering tests

### Changed
- `generate` now supports `-q, --quiet` for CI-friendly output.
- `scan` now supports `-q, --quiet` and `--no-tips`.
- `explain` now supports `--no-tips`.
- Documentation updated in `README.md`, `CLI_USAGE.md`, and `INSTALLATION.md`.

### Quality
- Added `npm test` script (`npm run build && node --test test/*.test.mjs`).
- Verified build and command help output after feature additions.

## [1.0.0] - 2026-01-27

### Added
- Initial release of OSCALFLOW GitHub CLI extension.
- Core commands: `generate`, `scan`, `explain`, `export`.
- OSCAL SSP generation with baseline support.
- Repository compliance signal scanning and SSP update workflow.
- Developer-friendly NIST control explanations.
