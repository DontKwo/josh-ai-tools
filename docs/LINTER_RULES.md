# Claudemd Linter Rules & Reference

`claudemd_linter.py` enforces high-signal AI coding standards, anti-hallucination/anti-fluff prose constraints, Python best practices, multi-language code cleanliness, and GUI design rules (specifically tailored for PyQt/PySide applications).

---

## Command Line Usage

### Standard Run
Run the linter against a single file, a subdirectory, or the entire repository root (or use the `ailint` CLI shortcut):
```bash
uv run --no-project python scripts/claudemd_linter.py <file_or_directory>
```
The report is written to:
`scripts/lint_report_<project>.txt`

If there are no violations, the report will state:
```
None. Lint clean.
```

### Git Diff Scoped Linting (`--diff` / `--staged`)
Lint only files modified or untracked in git to accelerate iterative workflows (pass `--full` for a whole-repository audit):
```bash
# Lint all modified and untracked files
uv run --no-project python scripts/claudemd_linter.py --diff

# Lint only staged git changes
uv run --no-project python scripts/claudemd_linter.py --staged
```

### Incremental Caching (`--no-cache`)
By default, `claudemd_linter.py` uses `.lint_cache.json` to store hashes and violation results. Clean, unmodified files are skipped automatically:
```bash
# Force a clean re-scan bypassing the cache
uv run --no-project python scripts/claudemd_linter.py . --no-cache
```

### Parallel File Scanning (`--no-parallel`)
For large codebases, the linter utilizes parallel worker processes capped at `min(cpu_count, 4)`:
```bash
# Force single-threaded sequential execution
uv run --no-project python scripts/claudemd_linter.py . --no-parallel
```

### Suppression Audit (`--noqa`)
Audit all suppressions across your codebase:
```bash
uv run --no-project python scripts/claudemd_linter.py <file_or_directory> --noqa
```
This scans and reports every instance of `# noqa`, `// noqa`, `# type: ignore`, `# pragma: no cover`, `# pylint: disable`, `# nosec`, and `TODO/FIXME/HACK/XXX` comments.

---

## Suppression Rules

- **Inline suppression**: End a line with `# noqa` (or `// noqa`) to suppress all checks on that line, or `# noqa: <code>` (e.g. `# noqa: 11, 25`) to suppress specific codes.
- **Strict suppression policy**: `# noqa` must only be used when an exception is genuinely correct as-is; it is never a shortcut.
- **Comment block exemption**: Place `# long-comment-ok` (or `// long-comment-ok`) on or directly above a multi-line comment block to exempt it from Rule 17 (2-line comment limit).

---

## Complete Rule Legend

| Code | Category | Rule & Description | How to Fix |
|:---:|:---|:---|:---|
| **1** | AI Writing | Em dash (`—`) present | Rewrite the sentence fully; do not just swap punctuation. (Automated replacement is strictly forbidden). |
| **2** | AI Writing | Non-standard unicode (curly quotes, ellipsis `…`, en dash, nbsp, BOM, etc.) | Replace with plain standard ASCII characters. |
| **3** | AI Writing | Emoji present | Remove entirely from code, comments, and strings. |
| **4** | AI Writing | AI-style filler/transition/hype phrase (Over 300+ guards against AI copulatives, significance inflations, and conversational fluff) | Delete or rewrite plainly with direct technical language. |
| **5** | AI Writing | Negative-parallelism construction (`"not X, it's Y"` / `"not just X but Y"` / `"Y rather than X"`) | Rewrite as a direct, positive statement. |
| **6** | AI Writing | Vague or unsupported attribution (`"some argue"`, `"studies show"`, `"critics say"`) | Replace with a specific, sourced statement or delete. |
| **7** | Documentation | Reasoning or history comment (`explaining past changes` or `referencing old behavior`) | Rewrite to state only what the code does now. |
| **8** | Architecture | Historical construct (`delete legacy shim`) | Delete fallback wrapper; maintain only one active version. |
| **9** | Python AST | Bare `except:` clause | Specify exact exception type(s) (e.g., `except ValueError:`). |
| **10** | Python AST | Bare `pass` as the entire body of a function or except block | Implement logic or raise `NotImplementedError`. |
| **11** | Python AST | Missing type hints on function signature | Add type annotations to all parameters and the return value (e.g., `def parse(val: str) -> int:`). |
| **12** | Python AST | Import not at top of file | Move imports to the top-level import block. |
| **13** | Python AST | Import performed inside a function body | Move to top of file unless explicitly justified with `# noqa: 13`. |
| **14** | Python AST | Mutable default argument (list, dict, set) | Use `None` as default sentinel and assign inside the function. |
| **15** | Python AST | Equality check using `== None` or `!= None` | Use identity comparisons `is None` or `is not None`. |
| **16** | Python AST | String formatting via `.format()` or `%` operator | Convert to modern f-strings. |
| **17** | Code Cleanliness | Comment block longer than 2 lines without `# long-comment-ok` | Condense comment to &le; 2 lines, or add `# long-comment-ok`. |
| **18** | Documentation | Docstring excessively long (&gt; 6 lines) | Shorten docstring while retaining core technical summary. |
| **19** | Documentation | AI title-case heading pattern or skipped heading levels in Markdown | Rewrite headings plainly without excessive capitalization or boldface. |
| **20** | Architecture | Duplicate / near-duplicate code block across functions | Consolidate duplicate blocks into a single reusable function. |
| **21** | Code Cleanliness | Unused function, method, or import (via `vulture`) | Remove dead code or suppress with `# noqa: 21`. |
| **22** | Python AST | Import performed inside `try/except` block | All dependencies must be managed via project env/uv; move import to top level. |
| **23** | UI / Qt | Tooltip text passed as an inline literal string | Import from master tooltip module instead of hardcoding strings inline. |
| **24** | Code Cleanliness | `TODO` / `FIXME` / `HACK` / `XXX` comment left in code | Resolve the issue directly or track in issue tracker, then remove comment. |
| **25** | Code Cleanliness | Leftover debug print/console call (`print()`, `console.log()`, `fmt.Println()`, `println!()`, `std::cout`) | Use standard logging (`logger.debug()`) or remove debug print. |
| **26** | Portability | Hardcoded absolute filesystem path (e.g. `C:\...`, `/home/...`) | Use relative paths (`Path(__file__).parent`) or configuration constants. |
| **27** | Python AST | Exception caught and re-raised as a different type without `raise ... from` | Chain exceptions using `raise NewException(...) from err` or preserve original. |
| **28** | UI / Styling | Hardcoded hex color literal outside the theme module | Reference central theme/palette tokens instead of literal `#RRGGBB`. |
| **29** | Architecture | Dead file: file is never imported anywhere in scanned tree | Delete unused file or suppress with `# noqa: 29` on line 1. |
| **30** | Architecture | Circular import detected in project dependency graph | Break circular dependency chain (e.g. via dependency injection or restructuring). |
| **31** | UI / Qt | Raw `QSpinBox` / `QDoubleSpinBox` usage | Use a scroll-safe wrapper widget (e.g. `NoScrollDoubleSpinBox`) to prevent accidental wheel scrolling. |
| **32** | Portability | OS-specific API/command used in un-scoped function | Wrap in platform check (`sys.platform`), suffix function with platform name (e.g. `_thing_windows`), or provide cross-platform fallback. |
| **33** | UI / Qt | Word-wrapped `QLabel` in dialog/wizard lacking `setTextInteractionFlags` | Call `setTextInteractionFlags(Qt.TextSelectableByMouse)` to allow user text selection. |
| **34** | UI / Qt | `setDecimals()` called with a low literal on a spin box | Avoid low literal truncation; allow full precision or suppress with `# noqa: 34` if currency. |
| **35** | UI / Qt | Button/input widget lacking `setToolTip()` | Assign a tooltip to every interactive control via tooltip registry. |
| **36** | AI Artifacts | LLM internal metadata bug or citation artifact (`oaicite`, `[cite: X]`, `【X】`, `turn0search0`, `utm_source=chatgpt`) | Delete internal citation artifact or hallucinated search query link entirely. |
| **37** | AI Writing | Conversational AI filler or salutation (`"certainly!"`, `"here is the updated code"`, `"hope this helps"`) | Remove chatbot conversational residue completely. |
| **38** | Code Quality | Non-descriptive or generic variable name (single-letter or vague identifier) | Rename variable to a descriptive identifier. |
| **39** | Engineering | Collapsed complex equation or developer typo | Decompose into intermediate terms (`term1`, `num`, `denom`) and fix typos. |
| **40** | Code Cleanliness | Docstring bloat on simple function or ruff violation | Avoid multi-line docstrings on short math helpers; run standard linter. |
| **41** | Style | Heavy AI divider banners (`######`, `======`) | Replace with concise single-line comment. |
| **42** | Engineering | Cryptic micro-optimization in loop or comprehension | Use straightforward forward loops over nested walrus generators. |
| **43** | Engineering | Missing physical units or unit suffix on constant | Add unit suffix (`_kg`, `_m`, `_pa`, `_kw`) or comment. |
| **44** | Style | Artificial equation line break when under 140 characters | Keep expressions on a single horizontal line up to 140 chars. |
| **45** | Engineering | Over-engineered OOP in numerical code | Favor plain dictionaries and data structures over abstract base classes. |

---

## Supported Languages

The linter scans code across multiple ecosystems:
- **Python**: `.py` (Full AST, typing, Qt widgets, dead-code detection)
- **Web & JavaScript**: `.js`, `.jsx`, `.ts`, `.tsx`, `.html`, `.css`, `.scss`, `.vue`, `.svelte`
- **Systems & Native**: `.rs` (Rust), `.go` (Go), `.c`, `.cpp`, `.h`, `.hpp`
- **Shell**: `.sh`, `.bash`, `.zsh`
- **Documentation**: `.md`, `.txt`, `.rst`

---

## Companion Tools

### 1. Safe Auto-Fixer (`scripts/lint_fixer.py`)
Applies guaranteed, low-risk, formulaic fixes:
- Fixes Rule 15 (`== None` $\to$ `is None`, `!= None` $\to$ `is not None`)
- Normalizes Rule 2 Unicode curly quotes, ellipsis, and non-breaking spaces
- Safely strips Rule 3 emojis (with `--fix-emojis`)
- **Safety Guarantee**: Rule 1 (em dash) is **never** automated and requires manual sentence rewriting.

```bash
# Preview changes safely without touching files
uv run --no-project python scripts/lint_fixer.py . --dry-run

# Apply safe fixes
uv run --no-project python scripts/lint_fixer.py .
```

### 2. Symbol & Dependency Map Generator (`scripts/repo_map.py`)
Builds a compressed AST-level structural map of codebases for LLM context in under 500 lines:
```bash
uv run --no-project python scripts/repo_map.py . -o repo_map.txt
```

### 3. Prompt Minifier (`scripts/minify_instructions.py`)
Compacts instruction files (`CLAUDE.md`, `.cursorrules`, etc.) while retaining 100% directive strength:
```bash
uv run --no-project python scripts/minify_instructions.py templates/INSTRUCTIONS_TEMPLATE.md -i
```

### 4. Search Utility (`scripts/grep_keywords.py`)
Smart directory-aware regex search ignoring cache and build folders:
```bash
uv run --no-project python scripts/grep_keywords.py "noqa" . --ext py
```
