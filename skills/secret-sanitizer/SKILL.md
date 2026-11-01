---
name: secret-sanitizer
description: >-
  Scan code, environment files, and diffs for exposed secrets, API keys, credentials, and tokens. Use before commits, PRs, or pushing to remote repositories.
---

# Secret Sanitizer

Detect leaked credentials and authentication secrets before code changes leave the local workstation.

## Command

Scan the repository or specific files:

```bash
uv run --no-project python scripts/secret_sanitizer.py [target]
```

Options:
- `--fail-on-secrets`: Return non-zero exit code if potential secrets are detected.
- `--git-diff`: Limit scan to uncommitted git modifications.

## Monitored Secrets

- Private cryptographic keys (`BEGIN RSA PRIVATE KEY`, etc.)
- API tokens (OpenAI, Anthropic, GitHub, AWS, Google, Stripe)
- Database connection URIs containing embedded passwords
- JWT tokens and high-entropy secret assignments
