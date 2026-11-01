---
name: workspace-checkpoint
description: >-
  Create snapshot checkpoints of the workspace and execute one-step rollbacks if code or tests break. Use before complex or destructive refactoring sessions.
---

# Workspace Checkpoint and Rollback

Maintain safety checkpoints during multi-step refactors or automated code modifications.

## Commands

### 1. Save a Checkpoint

Create an instant file snapshot with a descriptive label:

```bash
uv run --no-project python scripts/rollback.py save "<label>"
```

### 2. List Checkpoints

View saved checkpoints and creation timestamps:

```bash
uv run --no-project python scripts/rollback.py list
```

### 3. Review Diffs

Preview modifications made since a checkpoint:

```bash
uv run --no-project python scripts/rollback.py diff [label]
```

### 4. Restore Workspace

Revert modified files to the exact checkpoint state:

```bash
uv run --no-project python scripts/rollback.py restore [label]
```

## Recommended Workflow

1. Always save a checkpoint before running broad automated refactors or complex AST rewrites.
2. Run test suites.
3. If tests fail or code breaks unexpectedly, restore the checkpoint immediately.

