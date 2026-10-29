# Setup Guide: AI Tools Development Environment

This guide explains how to configure any Windows, Linux, or macOS machine with unified rules, developer tooling, and automated AST linting across AI assistants (Claude Code, Cursor, Cline, Antigravity, Codex, Windsurf, Copilot, Aider).

---

## What Gets Configured

When you run the setup script:
1. **AI Assistant Instructions**
   - Directives enforcing terse replies, explicit types, git diff-scoped linting, and uv execution.
   - Dynamic path expansion pointing to this repository.
   - If a target instruction file already exists, choose overwrite, idempotent append, or skip.

2. **Automated Linter and MCP Server**
   - `scripts/claudemd_linter.py`: 45-rule AST and prose validation script.
   - `mcp/server.py`: Standard Model Context Protocol server exposing repository tools.

3. **Global Terminal Shortcuts**
   - Command wrappers in `bin/` (`ailint`, `aifix`, `airepo`, `aimd`, `aitree`, `aisearch`, `airollback`, etc.) utilizing `uv` when available.

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
   - Select configuration mode (Claude only, all tools, or custom interactive wizard).
   - Choose whether to add `josh-ai-tools\bin` to your User PATH.

### 2. Linux and macOS (Bash / Terminal)

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
3. Follow the interactive prompts.

---

## Direct Python and UV Invocation

```bash
# Configure all supported tools globally
uv run --no-project python scripts/configure.py --tools all --scope global

# Preview configuration changes without writing
uv run --no-project python scripts/configure.py --tools all --dry-run

# Run linter against current project
uv run --no-project python scripts/claudemd_linter.py . --level strict
```

---

## Verifying Setup

```bash
# Run the automated doctor health check
uv run --no-project python scripts/doctor.py

# Verify global shortcut
ailint --help
```
