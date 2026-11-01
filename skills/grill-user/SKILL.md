---
name: grill-user
description: >-
  Stress-test a plan, architectural decision, design proposal, or user idea through rigorous adversarial questioning. Use when the user requests grilling, before executing risky refactors, or when validating technical architecture.
---

# Grill User

Critique and pressure-test plans and architectural designs before implementation.

## Guidelines

1. Question one assumption or design choice at a time.
2. Require concrete trade-off analysis for dependencies, state management, and edge cases.
3. Probe failure modes, error handling, performance ceilings, and rollback strategies.
4. Do not offer premature solutions or validation. Force clear technical justification.

## Command

Launch the terminal grilling guide script:

```bash
uv run --no-project python scripts/grill_user.py "<topic_or_plan>"
```

## Workflow

1. State the core premise or proposed architecture under review.
2. Formulate 2 to 3 direct, challenging questions regarding unstated assumptions.
3. Wait for the user response.
4. Evaluate answers against reliability, performance, and simplicity before accepting the design.

