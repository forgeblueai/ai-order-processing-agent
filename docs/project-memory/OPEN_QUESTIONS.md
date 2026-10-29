# Open questions

These items represent evidence gaps or conflicting sources, not confirmed code defects.

- [ ] **README freshness:** reconcile the root README's Sprint 1 status and architecture description with current main, merged PR #22, and the existing README-refresh PR #20. Evidence needed: review the current PR diff and update/rebase decision.
- [ ] **Gate status conflict:** reconcile the stale status prose in `docs/SECURITY_GATE.md` and `docs/PORTFOLIO_DELIVERY.md` with merged PR #19/#22 and current evidence. Keep production, identity, network-exposure, and reproducibility gaps separate from implementation being merged.
- [ ] **G3 private demo:** inspect the latest head and acceptance evidence for Draft PR #25. Confirm clean startup, PostgreSQL migrations/persistence, local Ollama behavior, and failure/ambiguity cases before describing the private demo as reproducible.
- [ ] **Grounded-correction design:** review Draft PR #27 and linked Issue #26. Keep it marked proposal-only unless implementation and acceptance evidence are separately verified.
- [ ] **Current CI evidence:** establish status checks and workflow run links for the exact target SHA when permitted. The status query during the 2026-10-30 bootstrap returned no status entries and is not a pass result.
- [ ] **Frozen benchmark discipline:** preserve the Qwen3 0.6B baseline and scorer. If hybrid deterministic parsing is evaluated, use an independently versioned corpus/scorer and report model-only versus hybrid results separately.
- [ ] **PR #20 base freshness:** inspect whether the open README refresh branch is behind the current main and reconcile it before any merge decision.

## Resolution convention

When an item is resolved, mark it complete only after recording the date, exact SHA, commands or source links, observed result, limitations, and a dated entry under `WORK_LOG/`. Reopen it if later evidence changes the conclusion.
