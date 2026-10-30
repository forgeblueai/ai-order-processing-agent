# Current state — AI Order Processing Agent

- State recorded: 2026-10-30
- Main branch reviewed: `main`
- Main SHA: `ab1481147c33388b8a952d0b71d4e821eaecc80e`
- Main tree: `2e57eb2bbfd27fb371ea1e3dc73c383e03b49605`
- Working tree: **not checked**; remote GitHub review only.
- Documentation work branch: `docs/project-memory-bootstrap`
- Documentation branch before this reconciliation commit: `aedc43f261ca04c840fabdfb3697b3481e6d61fb`
- Confidence: high for inspected remote GitHub refs, PR metadata, source files and named workflow run states; no local runtime or tests executed in this task.

## Main implementation baseline

The current main commit is the merge of PR #22 and contains persistence, migrations, the order lifecycle, bearer authentication and role authorization. This is materially beyond the old Sprint 1 description that was present in the main README at the reviewed SHA.

### G1 — reliability

- PR #19 is merged as `e60cbef5c5ed7aa5853c481e606431b08aa07a5e`.
- Exact PR head `b6a1751a39d0f8508d7ed970d5fd045cb34ba9a9` has [CI #59 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/38144847162), [PostgreSQL #21 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/38144847168), and [Real LLM #15 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/38144847161).
- The final guarded 85-case run reported 85/85 schema-valid, 71/85 exact (83.5%), exception precision 62.9%, exception recall 78.0%, review FN 0, review precision 93.0%, review recall 100%, and P95 22.42 seconds.
- Gate interpretation: accepted for a bounded private portfolio-demo candidate only. This is not a production reliability guarantee; issue #23 retains scorer/corpus caveats.

### G2 — security

- PR #22 merged to main at `ab1481147c33388b8a952d0b71d4e821eaecc80e`.
- Exact PR head `e78fb19e0d9c422e2b9ecfbdc604ade6d2f88e28`: [CI #76 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281272292), [PostgreSQL #38 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281271961).
- Post-merge on exact main SHA: [CI push SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744565), [PostgreSQL push SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744442).
- Gate interpretation: authentication/RBAC is implemented and merged for a single-organization private demo. Tenant isolation, individual principal attribution, token lifecycle, production identity/TLS, reverse proxy and rate limiting remain open.

## Open PRs observed 2026-10-30

- [PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25): open Draft; head `d86f09224bca7449aaaa8a6bf1110d6ce793dbe3`, base current main. Exact-head checks: [CI #115 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096747) (155 tests per PR record), [PostgreSQL #77 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096864), [Private Demo #38 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096835), [Real LLM #51 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096817). Real LLM #51 is **model-only**, not a hybrid benchmark; it reported 54/85 exact, 85/85 schema-valid, review FN=0. Draft remains open pending owner-operated human workflow acceptance and final gate review.
- [PR #27](https://github.com/forgeblueai/ai-order-processing-agent/pull/27): open Draft, proposal/documentation only; current head `88f8b3aa2cabf8d4f6b7c4e9a0ca65ffa70b98a0`. Earlier CI/PostgreSQL runs were on prior head `6ba22909d2f698a9cff8eb34ca67559a2bbab6ab`; the latest head must not be described as checked by those earlier runs. No new grounding/correction endpoint is implemented on main by this PR.
- [PR #20](https://github.com/forgeblueai/ai-order-processing-agent/pull/20): open README refresh. Compare against current main: 1 commit ahead, 3 behind. The proposed README quick start does not configure `ORDER_API_KEY_HASHES_JSON`, so it is not safe to merge without rework/rebase.
- The Qwen 1.7B candidate run [#11](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39713790373) failed with a ReadTimeout and did not promote the model.

## Documentation reconciliation completed on this branch

- Root README rewritten for the actual main-branch state, including bearer-auth configuration and explicit boundary that PR #25's hybrid/private runtime is not in main.
- `docs/SECURITY_GATE.md` status updated from stale FIXING/VALIDATING wording to implemented/merged for the bounded private-demo API, while retaining production blockers.
- `docs/PORTFOLIO_DELIVERY.md` G1–G4 dispositions reconciled against exact merged PRs and exact-head workflow runs; G3 and G4 remain open.
- PR #20 was not modified or closed. The overlapping README branch remains an owner decision; do not merge it as-is.

## Evidence gaps / constraints

- No local checkout, tests, demo startup, database, or model was executed during this review.
- No GitHub Actions workflow was started or retried by this task.
- Current main tests from 2026-10-19 and PR #25/27 runs are historical, exact-SHA-specific evidence; not evidence for this new documentation branch.
- G1 synthetic evaluation does not establish production reliability or multilingual behavior.
- PR #25's model-only metrics must not be attributed to its hybrid deterministic parser.
- PR #27's previous checks do not cover its latest head.
- Keep the API private/loopback-only; no public release is approved.

## Next objective

Resolve the review decision for the README refresh (PR #20 is stale and overlaps the new corrected README), then complete owner-operated G3 human acceptance on Draft PR #25 after the permitted CI window. Keep G5 proposal PR #27 marked proposal-only until architecture approval and implementation evidence exist.
