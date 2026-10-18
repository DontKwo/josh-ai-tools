# josh-ai-tools

Portable environment configuration and automated tooling to set up any machine (Windows, Linux, or macOS) across **any popular AI developer tool** (Claude Code, Cursor, Cline / Roo Code, Google Antigravity, OpenAI Codex / ChatGPT, Windsurf, GitHub Copilot, Aider) with Josh's exact developer workflow, style rules, AST-driven linter, safe auto-fixer, context optimizers, and native MCP server.

---

## Supported AI Tools

`josh-ai-tools` automatically detects and configures the exact rule/instruction files required for each AI tool, pointing every one of them to the same canonical linter script located inside this cloned repository:

| AI Tool | Global Target | Workspace / Project Target | Notes |
|:---|:---|:---|:---|
| **Claude Code** | `~/.claude/CLAUDE.md` | `CLAUDE.md` | Includes `templates/claude_settings.json` template |
| **Cursor IDE** | `~/.cursorrules` | `.cursorrules` & `.cursor/rules/josh-rules.mdc` | Includes Cursor MDC frontmatter |
| **Cline & Roo Code** | `~/.clinerules` | `.clinerules` | Full compatibility with both extensions |
| **Google Antigravity (AGY)** | `~/.gemini/antigravity/rules/josh_rules.md` | `.agent/rules/josh_rules.md` | Native Antigravity rules format |
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

### Direct Python Invocation (CLI & Automation)
```bash
# Configure ALL tools globally
python scripts/configure.py --tools all --scope global

# Configure a specific tool for the current project
python scripts/configure.py --tools cursor,cline --scope workspace

# Interactive setup wizard
python scripts/configure.py
```

---

## Global Terminal Shortcuts

Once installed via `setup.bat` or `setup.sh`, you can run these commands from **any** terminal in **any** project folder:

```bash
ailint            # Run the 37-rule linter against the current directory
ailint --diff     # Run the linter ONLY against modified/untracked git files
aifix             # Apply safe, guaranteed formulaic fixes (== None, quotes, unicode)
airepo            # Dump a compact AST symbol tree of the current codebase
aiprune           # Detect and prune unused/zombie imports and dead code
aiboost           # Infer and apply type annotations to unannotated functions
aideps            # Detect hallucinated imports and undeclared dependencies
aimd              # Convert PDF, DOCX, PPTX, XLSX, CSV, IPYNB to structured Markdown
aitree            # Token-efficient directory tree with line counts & file sizes
aisearch          # Fast regex & symbol search across codebases with context lines
aislice           # View targeted line ranges of any file with line numbers
aidiff            # AST-aware token-compressed git diff for LLM prompts
airollback        # Snapshot checkpoints and one-key rollback manager
```

---

## Repository Structure (Single Source of Truth)

```
josh-ai-tools/
├── README.md                      # Repository overview and quickstart
├── setup.bat                      # Windows interactive setup script (auto-configures rules & MCP)
├── setup.sh                       # Linux & macOS interactive setup script (auto-configures rules & MCP)
├── .gitignore                     # Git ignores for Python, cache, and checkpoints
├── bin/                           # Global terminal shortcuts
│   ├── ailint.cmd / ailint        # Quick linter command
│   ├── aifix.cmd / aifix          # Quick safe auto-fixer command
│   ├── airepo.cmd / airepo        # Quick symbol map command
│   ├── aiprune.cmd / aiprune      # Quick dead code & zombie import pruner
│   ├── aiboost.cmd / aiboost      # Quick type annotation booster
│   ├── aideps.cmd / aideps        # Quick hallucinated dependency scanner
│   ├── aimd.cmd / aimd            # Universal document to Markdown converter
│   ├── aitree.cmd / aitree        # Visual codebase hierarchy & token estimator
│   ├── aisearch.cmd / aisearch    # Fast codebase regex & symbol searcher
│   ├── aislice.cmd / aislice      # Targeted file line slicer
│   ├── aidiff.cmd / aidiff        # AST git diff compressor
│   └── airollback.cmd / airollback# Workspace checkpoint & rollback manager
├── templates/
│   ├── INSTRUCTIONS_TEMPLATE.md   # [Single Source of Truth] Unified AI instruction template
│   ├── claude_settings.json       # [Single Source of Truth] Claude Code settings template
│   └── mcp_config.json            # Template for registering MCP server
├── scripts/
│   ├── configure.py               # Universal multi-AI configurator & automatic MCP server setup
│   ├── claudemd_linter.py         # 37-rule AST, Wikipedia AI writing & citation bug linter
│   ├── lint_fixer.py              # Safe auto-fixer for deterministic mechanical violations
│   ├── repo_map.py                # Token-efficient symbol & dependency map generator
│   ├── minify_instructions.py     # Prompt minifier for instruction files
│   ├── grep_keywords.py           # Reusable directory-aware grep utility
│   ├── doctor.py                  # Health check, MCP verification & self-healing synchronizer
│   ├── install_hooks.py           # Git pre-commit enforcement hook installer
│   ├── clean_encoding.py          # Mojibake & character encoding cleaner
│   ├── prune_dead_code.py         # Dead code & zombie import pruner (deterministic AST)
│   ├── boost_types.py             # Type annotation booster (safe AST type inference)
│   ├── check_dependencies.py      # Hallucinated dependency & package import scanner
│   ├── to_markdown.py             # Universal PDF, DOCX, PPTX, XLSX, CSV, IPYNB to Markdown parser
│   ├── dir_overview.py            # Token-efficient visual codebase tree
│   ├── fast_search.py             # Directory-aware fast regex search with context lines
│   ├── slice_file.py              # Targeted line range extractor with line numbers
│   ├── redact_diff.py             # AST git diff redactor (60-80% token savings)
│   └── rollback.py                # Instant workspace checkpoint and rollback engine
├── mcp/
│   └── server.py                  # Standard MCP server exposing 14 native tools
├── tests/
│   └── test_linter.py             # Complete unit test suite (32 tests passing)
└── docs/
    ├── LINTER_RULES.md            # Complete reference for all 37 linter codes & suppressions
    └── SETUP_GUIDE.md             # Detailed installation and verification manual
```

---

## Tooling Suite & Features

### 1. Advanced 37-Rule Anti-AI Linter (`scripts/claudemd_linter.py`)
- **Git Diff Scoped Linting**: Pass `--diff` to only lint modified/untracked files or `--staged` for staged changes.
- **Incremental Caching**: `.lint_cache.json` caches hash results for sub-second turnarounds.
- **Safe Parallel Processing**: Multiprocessing safely capped at `min(cpu_count, 4)`.
- **Wikipedia: Signs of AI Writing Coverage**: Covers all 300+ vocabulary markers, copulative avoidance, negative parallel constructions, and Rule 36 internal LLM metadata / citation bugs.
- **Rule 37 Conversational AI Guard**: Flags chatbot boilerplate, salutations, and conversational residue.

### 2. Guaranteed Safe Auto-Fixer (`scripts/lint_fixer.py`)
- Rule 15: `== None` $\to$ `is None`, `!= None` $\to$ `is not None`
- Rule 2: Normalizes curly quotes, ellipsis, non-breaking spaces, and BOMs to ASCII.
- Rule 3: Safely strips emojis (with `--fix-emojis`).
- **Safety Guarantee**: Rule 1 (em dash) is **never** automated and requires manual sentence rewriting.

### 3. Universal Document to Markdown Converter (`scripts/to_markdown.py` / `aimd`)
- Converts **PDF, DOCX, PPTX, XLSX, CSV, IPYNB, and HTML** into clean, structured, token-efficient Markdown.
- 100% standard library Python implementation for DOCX, PPTX, XLSX, CSV, IPYNB, HTML (zero required pip dependencies).
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

### 10. Native MCP Server with 14 Tools (`mcp/server.py`)
- Directly exposes all 14 tools to Claude, Cursor, Windsurf, Cline, and Antigravity.
- Automatically configured for all AI tools via `setup.bat`, `setup.sh`, and `configure.py`.

### 11. Complete Unit Test Suite (`tests/test_linter.py`)
- Run `python -m unittest tests/test_linter.py` to verify all 32 unit tests across rules and companion tools.

---

## Requirements

- Python 3.9+
- Optional: `vulture` (`pip install vulture`) for dead-code and unused function detection (rule 21).

---

## Documentation

- [docs/LINTER_RULES.md](file:///docs/LINTER_RULES.md) - Deep dive into all 35 linter codes, legend descriptions, and suppression rules (`# noqa`, `# long-comment-ok`).
- [docs/SETUP_GUIDE.md](file:///docs/SETUP_GUIDE.md) - Step-by-step setup walkthrough for Windows, macOS, and Linux across all AI tools.
