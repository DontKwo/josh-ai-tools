---
name: clean-encoding
description: >-
  Scan files for mojibake sequences, double-encoded UTF-8, Windows-1252 corruption, and stray placeholders, repairing text cleanly. Use when fixing corrupted text or imported files.
---

# Clean Encoding

Audit and fix character encoding corruption across source and text files.

## Command

Scan and repair files in a path:

```bash
uv run --no-project python scripts/clean_encoding.py [target]
```

Options:
- `--dry-run`: Display potential replacements without writing changes.
- `--degrees-to-word`: Convert degree symbols (`°`) to the word `degrees`.

## Fix Categories

1. Mojibake Sequences: Replaces double-encoded UTF-8 and Windows-1252 character pairs with correct Unicode characters.
2. Corrupted Placeholders: Normalizes corrupted placeholder tags back to standard tokens.
3. Stray Replacement Characters: Removes orphan Unicode replacement characters (`\ufffd`).

## Verification

Confirm files remain valid UTF-8 and run unit tests.
