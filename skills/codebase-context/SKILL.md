---
name: codebase-context
description: >-
  Generate token-efficient symbol maps, visual directory trees, targeted file slices, packed prompt bundles, and token counts. Use when surveying unfamiliar codebases or constructing prompt context.
---

# Codebase Context

Inspect repository structure and extract concise code representations without token waste.

## Tools and Commands

### 1. AST Symbol Map

Generate a compact map of classes, methods, and functions:

```bash
uv run --no-project python scripts/repo_map.py [target]
```

Options:
- `--depth N`: Restrict AST parsing depth.
- `--tokens`: Output token estimates for the generated map.

### 2. Directory Hierarchy Overview

Print a visual directory tree with line counts and file sizes:

```bash
uv run --no-project python scripts/dir_overview.py [target]
```

Options:
- `--depth N`: Maximum directory traversal depth (default: 3).

### 3. File Slicing

Read targeted line ranges with line numbering:

```bash
uv run --no-project python scripts/slice_file.py <path> <start_line>-<end_line>
```

### 4. Pack Context Bundle

Combine source files into an organized prompt package:

```bash
uv run --no-project python scripts/pack_context.py [target] --out <output_file>
```

### 5. Token Budget Analyzer

Measure token consumption across project files:

```bash
uv run --no-project python scripts/token_budget.py [target]
```

## Best Practice

Target file slices and symbol maps instead of reading entire files into prompt context.

