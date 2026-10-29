# Python Execution & Environment Directives

## Universal uv Invocation
- Run Python commands through uv: `uv run --no-project --python "<venv_python>" <command>`.
- Always pass `--no-project` to prevent uv from initializing projects or auto-creating virtual environments.
- Always wrap `<venv_python>` in double quotes to handle paths with spaces.
- If `uv` is unavailable on PATH, fall back to executing `"<venv_python>" <command>` directly.
- Formulate commands explicitly:
  - Scripts: `uv run --no-project --python "<venv_python>" <script_path> [args]`
  - Modules and test runners: `uv run --no-project --python "<venv_python>" python -m <module> [args]` (e.g. `-m pytest`, `-m unittest`)
  - Inline expressions: `uv run --no-project --python "<venv_python>" python -c "<code>"`

## Virtual Environment Reuse & Discovery
- Reuse an existing virtual environment as close as possible to the run root. Never create a new environment (`uv venv`, `uv sync`, bare `uv run`, `python -m venv`, `virtualenv`, `conda create`).
- Locate `<venv_python>` using this search precedence:
  1. Search upward from the run root (command working directory) toward the project root and filesystem root for `.venv` or `venv`.
     - Windows: `<found_venv>\Scripts\python.exe`
     - Linux / macOS: `<found_venv>/bin/python`
  2. If upward directory search finds no virtual environment, check the active `VIRTUAL_ENV` or `CONDA_PREFIX` environment variables.
  3. Check `.vscode/settings.json` for `python.defaultInterpreterPath` if present.
  4. Select the first matching virtual environment found.

## Missing Environment Protocol
- If no virtual environment exists anywhere in the parent directory tree:
  - Never create or initialize a virtual environment.
  - Halt Python execution immediately.
  - Ask the user to specify the target Python interpreter or virtual environment to reuse, or ask for explicit permission to execute using host Python.

## Package Installation Protocol
- Never install packages into the virtual environment without explicit user approval.

## Tooling Exemption
- Global repository tooling from `josh-ai-tools` (such as `claudemd_linter.py`) may execute using the host runner (`uv run --no-project python`) when the target workspace virtual environment lacks tool dependencies.

