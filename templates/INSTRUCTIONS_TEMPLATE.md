# Style & Tone
- Be terse. No preamble, conversational filler ("certainly!", "here is the code", "hope this helps"), or apologies.
- Never use AI writing patterns: no em dashes (rewrite sentences cleanly), no negative parallelisms ("not just X, but Y"), no copulative avoidance ("serves as", "stands as"), no hype/fluff vocabulary ("pivotal", "delve", "testament", "tapestry", "robust", "boasts", "seamlessly"), and no internal citation metadata (`oaicite`, `[cite: ...]`, `【...】`).
- There is no old version of code. Never add compatibility shims, legacy branches, or deprecated functions.
- Every function signature must have explicit parameter and return type annotations.
- Keep comments <= 2 lines. State only what code does now; never explain history, reasons, or old behavior. Use `# long-comment-ok` only when detailed documentation is strictly necessary.

# Architectural Reorganization & Refactoring
- If at any time you believe a repository, folder, or file should be reorganized, renamed, modularized, or rescoped, ALWAYS present the suggestion to the user with a clear architectural rationale and wait for explicit approval before proceeding.

# Engineering & Human Reviewability Directives
- Step-by-Step Readability: Prefer straightforward loops and explicit state transitions over nested comprehensions or generator reductions.
- Horizontal Flow & Term Decomposition: Decompose multi-operation equations into named intermediate terms (`term1`, `term2`, `num`, `denom`, `exp`). Allow expressions to extend horizontally up to 140 characters; never artificially break equations across lines to meet 79-character limits.
- Calculation Function Naming: Prefix engineering and thermodynamic calculation functions with `calc_` (e.g. `calc_T0_from_T`, `calc_ISP_from_TSFC`, `calc_m_prop`).
- Units & Domain Shorthand: Use standard domain shorthand (`gam`, `cp`, `R`, `T04`, `TSFC`, `ISP`, `GLOW`, `TW0`, `dV`). Suffix ambiguous quantities with units (`_kg`, `_m`, `_pa`, `_deg`, `_psi`, `_kw`). Provide unit conversion helpers (`lb2kg`, `deg2rad`) or use `pint.UnitRegistry` for dimensional tracking.
- Physical Defaults: Place physical constants as keyword defaults in signatures (`gam: float = 1.4`, `cp: float = 1005.0`, `R: float = 287.0`).
- Encapsulation: Structure modular computation scripts into discrete problem functions (`prob1()`, `prob2()`, `main()`).
- Simulation Loops: Use explicit forward time-stepping loops (`for t_step in t:`) and plain lists.
- Plain Data Structures: Favor plain dictionaries and Plain Old Data structures over abstract base classes, metaclasses, or deep OOP hierarchies in numerical code.
- Design Sweeps: Accumulate constraint violations in dictionary counters instead of aborting loops with exceptions.
- Zero AI Docstring Bloat: Never generate multi-line Google/Sphinx docstrings (`Args:`, `Returns:`) for short mathematical functions. Never use decorative divider banners (`######`, `======`).
- Multi-Language Standards:
  - Python: Use Matplotlib with raw LaTeX labels (`r'$T_0/T_x$'`), `plt.grid(True)`, and shared axes.
  - C++: Use `#pragma once`, `#define M_PI`, templated solvers, capture lambdas (`[&]`), and Eigen.
  - MATLAB: Use `readmatrix`, in-place table filtering, and anonymous function handles.

# After Changes
- Reply with a brief list: what changed + confirmation it was tested.
  Example: "Fixed off-by-one in parser. Added retry logic. All 27 unit tests passing."

# Documentation
- Never write .md documentation files unless explicitly requested. No unsolicited guides or README expansions.

# Linter (Mandatory)
- After every code change, run the linter against the entire project root:
  {{LINTER_COMMAND}} <project_root> --level strict
- Verification levels:
  - `--level standard`: Anti-AI writing guards, core AST safety, equation formatting.
  - `--level strict` (Default): Adds `calc_` naming, term decomposition, banner removal, unit annotations.
  - `--level full`: Adds strict type hints, zero prints, dead code removal, Qt GUI rules.
  - Fine-grained overrides: `--skip <codes>` or `--only <codes>` for targeted checks.
- Then read {{REPORT_PATH}} in full.
- Fix every violation listed using the code's legend entry. This applies to every file in the project folder.
- Re-run until the report reads "None. Lint clean."
- `# noqa` / `# noqa: <codes>` suppresses checks; use only when code is genuinely correct as-is. Never use noqa as a shortcut.
