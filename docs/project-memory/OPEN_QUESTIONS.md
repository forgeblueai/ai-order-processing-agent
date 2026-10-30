# Open questions

These items represent evidence gaps or decisions requiring owner review, not confirmed code defects.

- [ ] **README refresh route:** the current-main README is now accurately rewritten on `docs/project-memory-bootstrap`. PR #20 remains open but is 1 commit ahead / 3 behind main, and its quick-start does not configure the required bearer-auth environment. Decide whether to supersede/rebase PR #20 or use the corrected README branch; do not merge PR #20 as-is.
- [ ] **G3 owner-operated acceptance:** Draft PR #25 has exact-head CI, PostgreSQL, private-demo and model-only Real LLM workflow runs marked SUCCESS. A real owner-operated clean startup and human review/approval/draft/simulated-confirmation sequence remains required. Do not impersonate a human or accept CI evidence as this step.
- [ ] **G3 hybrid measurement:** Real LLM #51 on PR #25 measured the model-only extractor (54/85 exact), not the strict deterministic + LLM hybrid. Build a separate versioned hybrid evaluation before making a hybrid accuracy claim; preserve the frozen v1 corpus/scorer.
- [ ] **Production security:** tenant isolation, individual principal identity/audit attribution, managed token rotation/revocation, production TLS/reverse proxy, rate limiting and deployment operations remain outside the current private-demo control.
- [ ] **Grounded-correction design:** PR #27 remains a proposal-only Draft. Its current head is `88f8b3aa2cabf8d4f6b7c4e9a0ca65ffa70b98a0`; its available earlier CI/PostgreSQL runs are on predecessor `6ba22909d2f698a9cff8eb34ca67559a2bbab6ab`. Re-verify exact latest head before relying on test claims.
- [ ] **Benchmark methodology:** issue #23 tracks corpus/scorer issues; a single synthetic run cannot establish production reliability. Keep model-only, deterministic and hybrid measurements separate.
- [ ] **G4 portfolio evidence:** create and review a synthetic-data case study, a truthful owner-operated walkthrough, architecture illustration and versioned demo-release evidence only after G3 acceptance and release approval.
- [ ] **Fresh release-candidate checks:** when release work is authorized, run CI, PostgreSQL and any applicable private-stack checks on the exact candidate SHA and preserve run links/artifact hashes.

## Resolved by current documentation branch (not yet merged to main)

- [x] Main README's Sprint 1 / temporary-regex status was replaced on this branch with current main implementation and gate status.
- [x] Security Gate's stale "FIXING / VALIDATING / not merged" header was reconciled with merged PR #22 and exact PR-head/post-merge checks.
- [x] Portfolio Delivery G1/G2 stale BLOCKED dispositions were reconciled; G3/G4 remain open with explicit evidence and blockers.

## Resolution convention

When an item is resolved, record date, exact SHA, source/commands, observed result and limits in a dated `WORK_LOG/` entry. A branch-local correction is not considered merged into main until the PR is reviewed and merged.
