---
name: dependency-guard
description: >-
  Scan Python source files to detect undeclared third-party imports and non-existent AI-hallucinated packages. Use when checking dependencies before deployment or after adding libraries.
---

# Dependency Guard

Audit project imports against installed environments and declared package configurations.

## Command

Scan the project for undeclared or non-existent packages:

```bash
uv run --no-project python scripts/check_dependencies.py [target]
```

## Behavior

1. Parses all Python files in the target directory into AST representations.
2. Identifies all top-level imports.
3. Compares imports against standard library modules, local workspace packages, and declared configuration files (`pyproject.toml`, `requirements.txt`, `setup.cfg`).
4. Flags undeclared external packages and hallucinations.

## Resolution Steps

1. If an import is valid but missing from configuration, add it to `pyproject.toml` or `requirements.txt`.
2. If an import is hallucinated by an AI, replace it with standard library or actual project dependencies.
