# Style & Tone
- Be terse. No preamble, conversational filler ("certainly!", "here is the code", "hope this helps"), or apologies.
- Avoid AI writing patterns: no em dashes (rewrite sentences cleanly), no negative parallelisms (`"not just X, but Y"`), no copulative avoidance (`"serves as"`, `"stands as"`), no hype/fluff vocabulary (`"pivotal"`, `"delve"`, `"testament"`, `"tapestry"`, `"robust"`, `"boasts"`, `"seamlessly"`), and no internal citation metadata (`oaicite`, `[cite: ...]`, `【...】`).
- Write only for current behavior. Never add compatibility `shims`, `legacy` branches, or `deprecated` functions unless explicitly requested.
- Every function signature must have explicit parameter and return type annotations.
- Keep comments <= 2 lines. State only what code does now. Use `# long-comment-ok` only when multi-line explanation is strictly necessary (such as complex algorithms or mathematical derivations).

# Architectural Reorganization & Refactoring
- If you believe a repository, folder, or file should be reorganized, renamed, modularized, or rescoped, present the suggestion to the user with a clear architectural rationale and wait for explicit approval before proceeding.

# Python Execution
- Run Python commands through uv: `uv run --no-project --python "<venv_python>" <command>`.
- Always pass `--no-project` to prevent uv from initializing new projects or auto-creating virtual environments.
- Reuse an existing virtual environment as close as possible to the run root. Locate `<venv_python>` using this search precedence:
  1. Search upward from the command run root (working directory) toward the project root and filesystem root for `.venv` or `venv`.
     - Windows: `<found_venv>\Scripts\python.exe`
     - Linux/macOS: `<found_venv>/bin/python`
  2. If upward directory search finds no virtual environment, check the active `VIRTUAL_ENV` or `CONDA_PREFIX` environment variables.
  3. Check `.vscode/settings.json` for `python.defaultInterpreterPath` if present.
  4. If no virtual environment exists anywhere in the directory hierarchy, do not create one. Halt and ask the user for the target Python interpreter path (or permission to use host Python). Never initialize a new environment (`uv venv`, `uv sync`, bare `uv run`, `python -m venv`, `virtualenv`, `conda`).
- Always wrap `<venv_python>` in double quotes to handle paths with spaces.
- If `uv` is unavailable on PATH, fall back to executing `"<venv_python>" <command>` directly.
- Formulate commands explicitly:
  - Scripts: `uv run --no-project --python "<venv_python>" <script_path> [args]`
  - Modules & test runners: `uv run --no-project --python "<venv_python>" python -m <module> [args]` (e.g. `-m pytest`, `-m unittest`)
  - Inline expressions: `uv run --no-project --python "<venv_python>" python -c "<code>"`
- Never install packages into the environment without explicit user approval.
- Repository tools from `josh-ai-tools` may execute with the host runner (`uv run --no-project python <script>`) when the target project virtual environment lacks tool dependencies.
- See {{PYTHON_RULES_PATH}} for additional environment context.

# After Changes
- Reply with a brief list: what changed + confirmation it was tested (or state explicitly that it was not tested).
  Example: "Fixed off-by-one in parser. Added retry logic. All 27 unit tests passing."

# Documentation
- Never create unsolicited .md documentation files (no unrequested READMEs, architecture summaries, or guides). Deliverables explicitly requested by the user are permitted. Internal agent artifacts and scratchpads are permitted. Editing existing documentation when modifying features is permitted.

# Domain Rules
- For engineering, numerical, or thermodynamic tasks, follow {{ENGINEERING_RULES_PATH}}. Domain equations adhering to these rules are exempt from single-letter variable checks (Rule 38).

# Linter (Mandatory)
- After every code change, run the linter:
  {{LINTER_COMMAND}} . --level strict
- In git repositories with existing history, the linter runs with `--diff` by default so only changed files get linted. Run with `--full` only when the user explicitly requests a full repository audit.
- Verification levels (distinct from the `--full` scan scope):
  - `--level standard`: Anti-AI writing guards, core AST safety, equation formatting.
  - `--level strict` (Default): Adds term decomposition, banner removal, unit annotations, descriptive naming.
  - `--level full`: Strict type hints, zero prints, dead code removal, Qt GUI rules. Run only when requested by the user.
  - Fine-grained overrides: `--skip <codes>` or `--only <codes>` for targeted checks.
- When violations occur, inspect the report file path printed in terminal output. Fix every violation and re-run until the output reads "None. Lint clean." (the report file is deleted automatically once clean).
- `# noqa` / `# noqa: <codes>` suppresses checks; use only when code is genuinely correct as-is. For third-party, vendor, or generated code where modifications would break functionality, add targeted inline `# noqa: <code>` comments.
