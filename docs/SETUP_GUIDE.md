# Setup Guide: Claude Code Development Environment

This guide explains how to set up any Windows, Linux, or macOS machine with Josh's Claude configuration, rules, and scripts.

---

## What Gets Installed

When you run the setup script:
1. **Claude Instructions (`~/.claude/CLAUDE.md`)**
   - Directives enforcing terse replies, no unprompted documentation, zero legacy backward-compatibility shims, and mandatory linter runs after changes.
   - Setup dynamically adapts file paths to the current machine's home directory.
   - If an existing `CLAUDE.md` is detected, you will be prompted to **Overwrite**, **Append**, or **Skip**.

2. **Linter & Grep Tooling (`scripts/`)**
   - `scripts/claudemd_linter.py`: The 35-rule AST and prose validation script (single source of truth).
   - `scripts/grep_keywords.py`: Fast directory-aware search utility.

3. **Claude Code Configuration (`~/.claude/settings.json`)**
   - Sourced from `templates/claude_settings.json`: automatically sets `defaultMode: "bypassPermissions"`, enables the dark theme, selects `opus[1m]`, and whitelists scripts so tools run without repetitive permission prompts.

---

## Installation by Operating System

### 1. Windows (Command Prompt or PowerShell)

1. Clone or copy this repository to your target machine:
   ```cmd
   git clone <repo-url> josh-ai-tools
   cd josh-ai-tools
   ```
2. Run the automated installer:
   ```cmd
   setup.bat
   ```
3. Follow the on-screen prompts:
   - If `CLAUDE.md` already exists, press `O` to overwrite, `A` to append, or `S` to skip.
   - Confirm script installation.
   - Choose whether to install the recommended `settings.json`.
   - Optionally install `vulture` via `pip install vulture` for unused code analysis.

### 2. Linux & macOS (Bash / Terminal)

1. Clone or copy this repository:
   ```bash
   git clone <repo-url> josh-ai-tools
   cd josh-ai-tools
   ```
2. Make `setup.sh` executable and run it:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
3. Follow the interactive prompts (Overwrite, Append, or Skip if `CLAUDE.md` already exists).

---

## Verifying the Setup

After installation, verify that the scripts and configuration are in place:

### On Windows
```cmd
python %USERPROFILE%\.claude\scripts\claudemd_linter.py --help
type %USERPROFILE%\.claude\CLAUDE.md
```

### On Linux / macOS
```bash
python3 ~/.claude/scripts/claudemd_linter.py --help
cat ~/.claude/CLAUDE.md
```

---

## How Claude Enforces This Workflow

Whenever Claude starts a coding session in a project workspace, it reads your global `CLAUDE.md`.

According to Josh's rules:
1. Claude responds tersely without preamble or unsolicited reasoning.
2. After making any code changes, Claude automatically runs:
   ```bash
   python <scripts_dir>/claudemd_linter.py <project_root>
   ```
3. Claude inspects `lint_report.txt` and continues iterating until the report reads:
   ```
   None. Lint clean.
   ```
4. Claude reports only what changed and confirmation that testing succeeded.

