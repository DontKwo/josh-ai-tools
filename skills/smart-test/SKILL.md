---
name: smart-test
description: >-
  Analyze modified files from git diffs and automatically run only the unit test suites impacted by those changes. Use to accelerate feedback loops during incremental development.
---

# Smart Test Runner

Execute only relevant test files affected by local modifications.

## Command

Run impacted tests:

```bash
uv run --no-project python scripts/smart_test_runner.py
```

Options:
- `--runner <tool>`: Choose test runner (`pytest` or `unittest`).
- `--verbose`: Show full test discovery traces and mapping logic.
- `--all`: Execute full test suite regardless of git diff status.

## Mechanics

1. Inspects git status and uncommitted diffs to identify modified modules.
2. Traces import dependencies and naming patterns (`test_<module>.py`).
3. Formulates a targeted runner command containing only mapped test suites.
4. Falls back to a full test run if shared configuration or core templates were modified.
