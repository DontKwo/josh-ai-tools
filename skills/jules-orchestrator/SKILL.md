---
name: jules-orchestrator
description: >-
  Orchestrate autonomous Google Jules coding sessions, poll task progress, review pull request diffs, run local pytest suites, and merge approved changes into target branches such as redesign-next.
---

# Google Jules Continuous Orchestrator

Coordinate Google Jules tasks through the Jules REST API, review pull requests, run tests, and merge into target branches.

## Requirements

1. `JULES_API_KEY`: API key from Google Jules settings (`https://jules.google.com/settings`).
2. GitHub Repository Access: Google Jules GitHub App installed on the target repository.
3. Target Branch: Defaults to `redesign-next` (configurable via `--branch <name>`).

## Commands

Run from `C:\Users\Josh\projects\jules-orchestrator`:

### 1. Identify Next Gap or Queued Task
```bash
uv run --no-project --python "C:/Users/Josh/projects/FOSSEverything/.venv/Scripts/python.exe" python -m jules_orchestrator.cli gaps
```

### 2. Execute a Single Orchestration Step
Advances the engine state (dispatches next task, approves plan, checks completion, or reviews PR):
```bash
uv run --no-project --python "C:/Users/Josh/projects/FOSSEverything/.venv/Scripts/python.exe" python -m jules_orchestrator.cli step
```

### 3. Review a Specific Pull Request
Fetches the PR branch, checks diff guidelines, runs pytest and the strict linter:
```bash
uv run --no-project --python "C:/Users/Josh/projects/FOSSEverything/.venv/Scripts/python.exe" python -m jules_orchestrator.cli review --pr <number>
```

### 4. Continuous Background Daemon
Runs the continuous loop until interrupted or max cycles reached:
```bash
uv run --no-project --python "C:/Users/Josh/projects/FOSSEverything/.venv/Scripts/python.exe" python -m jules_orchestrator.cli run --branch redesign-next
```

### 5. Check Engine Status
```bash
uv run --no-project --python "C:/Users/Josh/projects/FOSSEverything/.venv/Scripts/python.exe" python -m jules_orchestrator.cli status
```

### 6. List Jules Sources and Sessions
```bash
uv run --no-project --python "C:/Users/Josh/projects/FOSSEverything/.venv/Scripts/python.exe" python -m jules_orchestrator.cli sources
uv run --no-project --python "C:/Users/Josh/projects/FOSSEverything/.venv/Scripts/python.exe" python -m jules_orchestrator.cli sessions
```
