# Project memory — AI Order Processing Agent

This directory stores durable, repository-specific context for this project. Keep statements evidence-linked and distinguish implemented behavior from proposals, draft PRs, intended work, and release readiness.

## Files

- [PROJECT_PROFILE.md](PROJECT_PROFILE.md): purpose, architecture map, constraints, and sources of truth.
- [CURRENT_STATE.md](CURRENT_STATE.md): verified baseline, active change requests, known documentation conflicts, and next objective.
- [DECISIONS.md](DECISIONS.md): durable architecture and safety decisions supported by project evidence.
- [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md): unresolved status conflicts and concrete evidence gaps.
- [WORK_LOG/](WORK_LOG/): dated records of inspections, decisions, and validation.

## Update rules

1. For repository-specific claims, record exact branch, commit SHA, path or PR link where material.
2. Label claims `verified`, `observed`, `inferred`, or `not checked`; do not turn intended work into implementation evidence.
3. For tests and CI, record the exact commit/run and the limits of the evidence. Say `NOT RUN` where appropriate.
4. Treat LLM output as untrusted candidate data; do not weaken the deterministic business or authorization boundaries in memory notes.
5. Update `CURRENT_STATE.md` when fresh evidence materially changes the baseline or next objective. Preserve prior observations in work logs.
6. Keep project details here; cross-project preferences and coordination rules belong in the central memory repository.
7. Never store bearer tokens, token plaintext, API keys, customer content, real order details, or other secrets / identifying data.
8. Before committing further changes, inspect the staged file list and whitespace check; do not claim broader correctness than the observed checks establish.

## Source-of-truth hierarchy

- Application behavior: current code and tests in `app/`, `tests/`, and `integration_tests/`.
- Current repository baseline: the live GitHub default branch and exact commit SHA.
- Security and delivery gates: [SECURITY_GATE.md](../SECURITY_GATE.md) and [PORTFOLIO_DELIVERY.md](../PORTFOLIO_DELIVERY.md), but reconcile their statuses against merged PRs and code because the checked-in gate documents currently contain stale/conflicting status statements.
- Frozen Qwen3 0.6B baseline: [BASELINE_QWEN3_0.6B.md](../../benchmarks/BASELINE_QWEN3_0.6B.md). Do not alter the baseline scorer or thresholds just to conceal regressions.
- A draft PR or an unmerged branch is evidence of proposed work, not proof that its changes are present in `main`.
