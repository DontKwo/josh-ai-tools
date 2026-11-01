---
name: doc-to-markdown
description: >-
  Convert documents including PDF, DOCX, XLSX, PPTX, CSV, HTML, and IPYNB into structured, token-efficient Markdown tables and text without external dependencies. Use when parsing or ingesting non-code documentation.
---

# Document to Markdown

Extract clean Markdown from diverse document formats using Python standard library parsers.

## Supported Formats

- PDF (`.pdf`) - stream and text extraction fallback
- Microsoft Word (`.docx`)
- Microsoft Excel (`.xlsx`)
- Microsoft PowerPoint (`.pptx`)
- Comma-Separated Values (`.csv`)
- Jupyter Notebooks (`.ipynb`)
- HTML (`.html`, `.htm`)

## Command

Convert an individual file or an entire directory of documents:

```bash
uv run --no-project python scripts/to_markdown.py <file_or_dir> [--out <output_file>]
```

Options:
- `--out <path>`: Write converted Markdown to a specific file instead of stdout.
- `--max-pages <N>`: Limit page count for large PDF documents.

## Output Characteristics

- Tables are converted into GitHub Flavored Markdown table format.
- Formatting clutter, proprietary binary tags, and XML metadata are stripped.
