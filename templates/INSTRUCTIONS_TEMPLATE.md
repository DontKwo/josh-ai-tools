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

# Grilling
- Grill the user relentlessly about a plan, decision, or idea when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
- Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.
- Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.
- Format a round like so:
  ❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>
  ➡️ <your recommended answer>
  ---
  ❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>
  ➡️ <your recommended answer>
- Word each question so "yes" accepts your recommended answer.
- Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.
- Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent with a fresh context window to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.
- The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

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
