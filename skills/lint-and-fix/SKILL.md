---
name: lint-and-fix
description: >-
  Run the 45-rule code quality, AST safety, and anti-AI writing linter or execute guaranteed deterministic auto-fixers. Use when validating code changes, auditing code style, fixing comparison syntax, or stripping non-ASCII artifacts.
---

# Lint and Auto-Fix

Execute static analysis and mechanical repairs on code and documentation.

## Commands

### 1. Run the Linter

Run the 45-rule AST and writing style auditor:

```bash
uv run --no-project python scripts/claudemd_linter.py [target] --level strict
```

Options:
- `--level standard`: Enforces anti-AI writing guards, core AST safety, and math equation formatting.
- `--level strict`: Adds term decomposition, banner removal, unit annotations, and descriptive naming.
- `--level full`: Strict type hints, zero prints, dead code checks, and Qt GUI rules.
- `--diff`: Lints only files with git modifications (default in git repositories).
- `--full`: Forces a whole-repository audit.
- `--skip <codes>`: Comma-separated list of rule numbers to skip.
- `--only <codes>`: Run specific rule numbers only.

### 2. Run the Auto-Fixer

Apply safe, mechanical fixes for deterministic violations:

```bash
uv run --no-project python scripts/lint_fixer.py [target]
```

Options:
- `--dry-run`: Preview suggested replacements without modifying files.
- `--fix-emojis`: Strip emoji characters from code and docstrings.

## Verification

1. Check terminal output for report file paths (`lint_report_<target>.txt`).
2. Fix all reported issues until the terminal outputs `None. Lint clean.`
3. Ensure all unit tests pass after applying auto-fixes.
