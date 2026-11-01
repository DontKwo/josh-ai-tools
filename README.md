# josh-ai-tools

Portable environment configuration and automated tooling to configure any machine (Windows, Linux, or macOS) across AI developer tools (Claude Code, Cursor, Cline, Roo Code, Google Antigravity, OpenAI Codex, Windsurf, GitHub Copilot, Aider) with unified style rules, an AST linter, auto-fixers, context optimizers, and a native MCP server.

---

## Supported AI Tools

`scripts/configure.py` installs rule instructions and registers MCP servers for each supported environment:

| AI Tool | Global Target | Workspace Target | Format Notes |
|:---|:---|:---|:---|
| **Claude Code** | `~/.claude/CLAUDE.md` | `CLAUDE.md` | Standard markdown rules |
| **Cursor IDE** | `~/.cursorrules` | `.cursorrules` & `.cursor/rules/josh-rules.mdc` | Includes Cursor MDC frontmatter |
| **Cline & Roo Code** | `~/.clinerules` | `.clinerules` | Standard markdown rules |
| **Google Antigravity (AGY)** | `~/.gemini/config/AGENTS.md` | `AGENTS.md` & `.agent/rules/josh_rules.md` | Native Antigravity rules and skills |
| **OpenAI Codex & ChatGPT** | `~/.codex/instructions.md` | `AGENTS.md` & `OPENAI.md` | Universal agent markdown convention |
| **Windsurf IDE** | `~/.windsurfrules` | `.windsurfrules` | Codeium / Windsurf configuration |
| **GitHub Copilot** | N/A | `.github/copilot-instructions.md` | Workspace copilot instructions |
| **Aider CLI** | `~/.aider.conventions.md` | `.aider.conventions.md` | Aider conventions format |

---

## Quickstart

Run the installer for your platform:

### Windows
```cmd
setup.bat
```

### Linux & macOS
```bash
chmod +x setup.sh
./setup.sh
```

### Direct CLI Invocation
```bash
# Configure all tools globally
uv run --no-project python scripts/configure.py --tools all --scope global

# Configure specific tools in workspace
uv run --no-project python scripts/configure.py --tools cursor,cline --scope workspace

# Interactive setup menu
uv run --no-project python scripts/configure.py
```

---

## Three Tool Interfaces

The tooling suite exposes 3 complementary access methods:

1. **Agent Skills (`skills/`)**: On-demand workflow runbooks for AI agents (Google Antigravity, Claude Code). Skills use progressive disclosure, loading into prompt context only when triggered.
2. **Native MCP Server (`mcp/server.py`)**: Standard Model Context Protocol server exposing 23 tools for direct tool calling in Claude, Cursor, Windsurf, Cline, and Antigravity.
3. **Terminal Shortcuts (`bin/`)**: 21 shell scripts adding instant commands to your terminal PATH for manual execution.

---

## Tool Reference

| Capability | Script | Skill | CLI | Description |
|:---|:---|:---|:---|:---|
| **45-Rule Linter** | `scripts/claudemd_linter.py` | `lint-and-fix` | `ailint` | AST and style linter (diff default, pass `--full` for whole repo). |
| **Safe Auto-Fixer** | `scripts/lint_fixer.py` | `lint-and-fix` | `aifix` | Applies deterministic fixes (`== None`, smart quotes, emojis). |
| **Plan Griller** | `scripts/grill_user.py` | `grill-user` | `aigrill` | Interrogates plans, architecture, and tradeoffs. |
| **Dead Code Pruner** | `scripts/prune_dead_code.py` | `codebase-health` | `aiprune` | Removes unused imports and unreferenced functions. |
| **Type Booster** | `scripts/boost_types.py` | `codebase-health` | `aiboost` | Infers and writes missing parameter and return type hints. |
| **Variable Auditor** | `scripts/check_variable_names.py` | `codebase-health` | `aivars` | Flags single-letter and uninformative identifiers (Rule 38). |
| **Typo Checker** | `scripts/spell_checker.py` | `codebase-health` | `aispell` | Audits code identifiers and comments for spelling errors. |
| **Symbol Map** | `scripts/repo_map.py` | `codebase-context` | `airepo` | Generates compact AST symbol and dependency trees. |
| **Directory Tree** | `scripts/dir_overview.py` | `codebase-context` | `aitree` | Token-efficient visual hierarchy with line counts and sizes. |
| **File Slicer** | `scripts/slice_file.py` | `codebase-context` | `aislice` | Views targeted line ranges with line numbers. |
| **Context Packer** | `scripts/pack_context.py` | `codebase-context` | `aicontext` | Bundles files into prompt packages with token counts. |
| **Token Counter** | `scripts/token_budget.py` | `codebase-context` | `aitokens` | Calculates token budgets and per-file token usage. |
| **AST Diff Redactor** | `scripts/redact_diff.py` | `codebase-context` | `aidiff` | Compresses git diffs for LLM prompts, saving 60-80% tokens. |
| **Fast Search** | `scripts/fast_search.py` | `codebase-context` | `aisearch` | Regex search with context lines, caps, and file filters. |
| **Dependency Scanner** | `scripts/check_dependencies.py` | `dependency-guard` | `aideps` | Flags undeclared external imports and hallucinated packages. |
| **Rollback Manager** | `scripts/rollback.py` | `workspace-checkpoint` | `airollback` | Saves workspace snapshots and restores state in one step. |
| **Document Converter** | `scripts/to_markdown.py` | `doc-to-markdown` | `aimd` | Converts PDF, DOCX, XLSX, PPTX, CSV, HTML to clean Markdown. |
| **Encoding Cleaner** | `scripts/clean_encoding.py` | `clean-encoding` | N/A | Repairs mojibake sequences and character corruption. |
| **Smart Test Runner** | `scripts/smart_test_runner.py` | `smart-test` | `aitest` | Maps git diffs to impacted test suites and executes them. |
| **Secret Scanner** | `scripts/secret_sanitizer.py` | `secret-sanitizer` | `aisec` | Scans code and git diffs for leaked API keys and tokens. |
| **Rule Synchronizer** | `scripts/sync_rules.py` | N/A | `aisync` | Synchronizes instruction files across all installed tools. |
| **Hook Installer** | `scripts/install_antigravity_hooks.py` | N/A | `aihook` | Installs git pre-commit and Antigravity task hooks. |
| **Environment Doctor** | `scripts/doctor.py` | N/A | N/A | Audits tool configs, MCP registration, and filepaths. |

---

## Repository Structure

```
josh-ai-tools/
├── bin/          # 21 shell shortcuts for manual terminal use
├── docs/         # Setup manual and linter rule specifications
├── mcp/          # Model Context Protocol server exposing 23 native tools
├── scripts/      # Core Python linters, analyzers, and utilities
├── skills/       # 10 modular agent skills with SKILL.md runbooks
├── templates/    # Instruction rules, engineering standards, and MCP templates
└── tests/        # 71 unit tests covering rules and tools
```

---

## Testing & Verification

Run the test suite:
```bash
uv run --no-project python -m unittest discover tests
```

Run the strict linter:
```bash
uv run --no-project python scripts/claudemd_linter.py . --level strict
```

---

## Documentation Links

- [docs/LINTER_RULES.md](docs/LINTER_RULES.md): Specifications for all 45 linter codes, suppression comments, and verification levels.
- [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md): Step-by-step setup walkthrough across Windows, macOS, and Linux.
