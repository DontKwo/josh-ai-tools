# josh-ai-tools

Portable environment configuration and automated tooling to set up any machine (Windows, Linux, or macOS) across popular AI developer tools (Claude Code, Cursor, Cline / Roo Code, Google Antigravity, OpenAI Codex / ChatGPT, Windsurf, GitHub Copilot, Aider) with Josh's developer workflow, style rules, AST-driven linter, safe auto-fixer, context optimizers, and native MCP server.

---

## Supported AI Tools

`josh-ai-tools` automatically detects and configures the exact rule and instruction files required for each AI tool, pointing every one of them to the canonical linter script located inside this cloned repository:

| AI Tool | Global Target | Workspace / Project Target | Notes |
|:---|:---|:---|:---|
| **Claude Code** | `~/.claude/CLAUDE.md` | `CLAUDE.md` | Configures CLAUDE.md rules |
| **Cursor IDE** | `~/.cursorrules` | `.cursorrules` & `.cursor/rules/josh-rules.mdc` | Includes Cursor MDC frontmatter |
| **Cline & Roo Code** | `~/.clinerules` | `.clinerules` | Full compatibility with both extensions |
| **Google Antigravity (AGY)** | `~/.gemini/config/AGENTS.md` | `AGENTS.md` & `.agent/rules/josh_rules.md` | Native Antigravity rules format |
| **OpenAI Codex & ChatGPT** | `~/.codex/instructions.md` | `AGENTS.md` & `OPENAI.md` | Universal agent markdown convention |
| **Windsurf IDE** | `~/.windsurfrules` | `.windsurfrules` | Codeium / Windsurf configuration |
| **GitHub Copilot** | N/A | `.github/copilot-instructions.md` | Copilot workspace rules |
| **Aider CLI** | `~/.aider.conventions.md` | `.aider.conventions.md` | Aider conventions file |

---

## Quickstart

Clone this repository onto your machine and run the installer:

### Windows
```cmd
setup.bat
```

### Linux & macOS
```bash
chmod +x setup.sh
./setup.sh
```

### Direct Invocation (`uv` or Python)
```bash
# Configure all tools globally
uv run --no-project python scripts/configure.py --tools all --scope global

# Configure a specific tool for the current project
uv run --no-project python scripts/configure.py --tools cursor,cline --scope workspace

# Interactive setup wizard
uv run --no-project python scripts/configure.py
```

---

## Global Terminal Shortcuts

Once installed via `setup.bat` or `setup.sh`, you can run these 21 commands from any terminal in any project folder:

```bash
ailint            # Run the 45-rule linter (diff default, pass --full for whole repo)
aifix             # Apply safe, guaranteed formulaic fixes (== None, quotes, unicode)
airepo            # Dump a compact AST symbol tree of the current codebase
aiprune           # Detect and prune unused/zombie imports and dead code
aiboost           # Infer and apply type annotations to unannotated functions
aideps            # Detect hallucinated imports and undeclared dependencies
aimd              # Convert PDF, DOCX, PPTX, XLSX, CSV, IPYNB to structured Markdown
aitree            # Token-efficient directory tree with line counts and file sizes
aisearch          # Fast regex and symbol search across codebases with context lines
aislice           # View targeted line ranges of any file with line numbers
aidiff            # AST-aware token-compressed git diff for LLM prompts
airollback        # Snapshot checkpoints and one-key rollback manager
aicontext         # Pack workspace context into token-budgeted prompt files
aitokens          # Calculate token budgets and file token counts
aisec             # Scan repository for exposed secrets and credentials
aitest            # Run smart targeted test runner for modified files
aispell           # Scan code and comments for common typos
aivars            # Check variable names for single-letter and uninformative identifiers
aihook            # Install Antigravity and git safety hooks
aisync            # Synchronize instructions across all configured AI tools
aigrill           # Grill the user relentlessly about a plan or decision
```

---

## Repository Structure (Single Source of Truth)

```
josh-ai-tools/
├── README.md                      # Repository overview and quickstart
├── setup.bat                      # Windows interactive setup script (auto-configures rules & MCP)
├── setup.sh                       # Linux & macOS interactive setup script (auto-configures rules & MCP)
├── .gitignore                     # Git ignores for Python, cache, and checkpoints
├── bin/                           # 21 global terminal shortcuts
│   ├── aiboost / aiboost.cmd      # Type annotation booster
│   ├── aicontext / aicontext.cmd  # Context packing utility
│   ├── aideps / aideps.cmd        # Dependency scanner
│   ├── aidiff / aidiff.cmd        # AST git diff compressor
│   ├── aifix / aifix.cmd          # Safe auto-fixer
│   ├── aigrill / aigrill.cmd      # Grilling skill agent tool
│   ├── aihook / aihook.cmd        # Hook installer
│   ├── ailint / ailint.cmd        # 45-rule linter
│   ├── aimd / aimd.cmd            # Universal document to Markdown converter
│   ├── aiprune / aiprune.cmd      # Dead code and zombie import pruner
│   ├── airepo / airepo.cmd        # Compact symbol tree generator
│   ├── airollback / airollback.cmd# Checkpoint and rollback manager
│   ├── aisearch / aisearch.cmd    # Fast regex search
│   ├── aisec / aisec.cmd          # Secret scanner
│   ├── aislice / aislice.cmd      # Targeted file line slicer
│   ├── aispell / aispell.cmd      # Code typo scanner
│   ├── aisync / aisync.cmd        # Tool rules synchronizer
│   ├── aitest / aitest.cmd        # Smart test runner
│   ├── aitokens / aitokens.cmd    # Token budget calculator
│   ├── aitree / aitree.cmd        # Codebase hierarchy tree
│   └── aivars / aivars.cmd        # Variable naming scanner
├── templates/
│   ├── INSTRUCTIONS_TEMPLATE.md   # Unified AI instruction template
│   ├── ENGINEERING_RULES.md       # Engineering and numerical computation standards
│   ├── PYTHON_RULES.md            # Python execution and environment reuse rules
│   └── mcp_config.json            # Template for registering native MCP server
├── scripts/
│   ├── boost_types.py             # Type annotation booster (safe AST type inference)
│   ├── check_dependencies.py      # Hallucinated dependency and import scanner
│   ├── check_variable_names.py    # Variable name checker for uninformative names
│   ├── claudemd_linter.py         # 45-rule AST, AI writing, and code quality linter
│   ├── clean_encoding.py          # Mojibake and character encoding cleaner
│   ├── configure.py               # Universal multi-AI configurator and MCP setup
│   ├── dir_overview.py            # Token-efficient visual codebase tree
│   ├── doctor.py                  # Health check, MCP verification, and synchronizer
│   ├── fast_search.py             # Fast regex search with context lines
│   ├── grep_keywords.py          # Smart directory-aware regex search utility
│   ├── install_antigravity_hooks.py # Hook installer for Google Antigravity
│   ├── install_hooks.py           # Git pre-commit hook installer
│   ├── lint_fixer.py              # Safe auto-fixer for deterministic mechanical violations
│   ├── minify_instructions.py     # Prompt compressor for rule and instruction files
│   ├── pack_context.py            # Codebase context packager for LLM prompts
│   ├── prune_dead_code.py         # Dead code and zombie import pruner
│   ├── redact_diff.py             # AST git diff redactor (60-80% token savings)
│   ├── repo_map.py                # Token-efficient symbol and dependency map generator
│   ├── rollback.py                # Instant workspace checkpoint and rollback engine
│   ├── secret_sanitizer.py        # Token, API key, and credential scanner
│   ├── slice_file.py              # Targeted line range extractor with line numbers
│   ├── smart_test_runner.py       # Smart test runner detecting affected tests from diffs
│   ├── spell_checker.py           # AST-aware typo scanner for code identifiers
│   ├── sync_rules.py              # Synchronizes instruction templates across installed tools
│   ├── to_markdown.py             # Universal document to Markdown converter
│   └── token_budget.py            # File token counter and context budget analyzer
├── mcp/
│   └── server.py                  # Standard MCP server exposing 23 native tools
├── tests/
│   ├── test_linter.py             # Unit tests for linter rules and companion tools
│   └── test_new_tools.py          # Unit tests for context, budget, test runner, and spell checker
└── docs/
    ├── LINTER_RULES.md            # Reference for all 45 linter codes and suppressions
    └── SETUP_GUIDE.md             # Detailed installation and verification manual
```

---

## Tooling Suite & Features

### 1. Advanced 45-Rule Anti-AI Linter (`scripts/claudemd_linter.py`)
- **Git Diff Scoped by Default**: Lints modified and untracked git files by default; pass `--full` for full repository audits.
- **Project-Scoped Reports**: Automatically creates `lint_report_<project>.txt` when violations occur and unlinks the report when clean.
- **Incremental Caching**: `.lint_cache.json` caches hash results for sub-second turnarounds.
- **Safe Parallel Processing**: Multiprocessing safely capped at `min(cpu_count, 4)`.
- **Wikipedia AI Writing Detection**: Detects vocabulary markers, copulative avoidance, negative parallel constructions, and LLM metadata markers.
- **Conversational AI Guard**: Flags chatbot boilerplate, salutations, and conversational residue.

### 2. Guaranteed Safe Auto-Fixer (`scripts/lint_fixer.py`)
- Rule 15: `== None` $\to$ `is None`, `!= None` $\to$ `is not None`
- Rule 2: Normalizes curly quotes, ellipsis, non-breaking spaces, and BOMs to ASCII.
- Rule 3: Safely strips emojis (with `--fix-emojis`).
- **Safety Guarantee**: Rule 1 (em dash) is never automated and requires manual sentence rewriting.

### 3. Universal Document to Markdown Converter (`scripts/to_markdown.py` / `aimd`)
- Converts **PDF, DOCX, PPTX, XLSX, CSV, IPYNB, and HTML** into clean, structured, token-efficient Markdown.
- Standard library Python implementation for DOCX, PPTX, XLSX, CSV, IPYNB, HTML with zero required pip packages.
- Formats tables cleanly into GitHub Flavored Markdown tables.

### 4. AST Git Diff Redactor (`scripts/redact_diff.py` / `aidiff`)
- Compresses `git diff` outputs for LLM prompts by focusing on AST-level changes (modified functions, logic, imports), stripping noisy context lines and whitespace churn for 60-80% token savings.

### 5. Snapshot Checkpoint & Rollback Engine (`scripts/rollback.py` / `airollback`)
- Take instant snapshots before letting AI make edits (`airollback save "before-refactor"`).
- Diff changes against checkpoint (`airollback diff`) or restore workspace in one second (`airollback restore`) if an AI breaks code or tests.

### 6. Fast Search & Codebase Overview (`scripts/fast_search.py`, `scripts/dir_overview.py`)
- `aisearch`: Fast regex search across code with context lines, token caps, and file filters.
- `aitree`: Token-efficient visual hierarchy showing line counts and file sizes.
- `aislice`: Inspect targeted line ranges (e.g. `main.py 100-150`) without full-file context dumps.

### 7. Dead Code & Zombie Import Pruner (`scripts/prune_dead_code.py` / `aiprune`)
- AST-level unused import pruner with syntax verification and Vulture dead code detection.

### 8. Type Annotation Booster (`scripts/boost_types.py` / `aiboost`)
- Infers parameter and return type annotations from default values and return expressions.

### 9. Hallucinated Dependency Scanner (`scripts/check_dependencies.py` / `aideps`)
- Detects non-existent AI-hallucinated packages and undeclared dependencies.

### 10. Native MCP Server with 23 Tools (`mcp/server.py`)
- Directly exposes all 23 tools to Claude, Cursor, Windsurf, Cline, and Antigravity.
- Automatically configured for AI tools via `setup.bat`, `setup.sh`, and `configure.py`.

### 11. Complete Unit Test Suite (`tests/`)
- Run `uv run --no-project python -m unittest discover -s tests` to verify all 51 unit tests across rules and companion tools.

---

## Requirements

- Python 3.9+ or `uv`
- Optional: `vulture` (`uv tool install vulture`) for dead-code and unused function detection (rule 21).

---

## Documentation

- [docs/LINTER_RULES.md](docs/LINTER_RULES.md): Deep dive into all 45 linter codes, legend descriptions, and suppression rules (`# noqa`, `# long-comment-ok`).
- [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md): Step-by-step setup walkthrough for Windows, macOS, and Linux across all AI tools.
