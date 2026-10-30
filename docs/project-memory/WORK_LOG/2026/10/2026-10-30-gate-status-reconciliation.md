# Work report — 2026-10-30 — Reconcile README and delivery-gate status

- Status: authored on `docs/project-memory-bootstrap`; not merged; no pull request opened.
- Repository: `forgeblueai/ai-order-processing-agent`
- Main baseline: `ab1481147c33388b8a952d0b71d4e821eaecc80e`
- Branch baseline: `aedc43f261ca04c840fabdfb3697b3481e6d61fb`
- Objective: reconcile stale README and gate-status prose against merged PRs, exact-SHA workflow runs and active draft PR descriptions without changing application source or CI configuration.

## Sources inspected

- Main branch metadata, recursive tree, README, `app/api/security.py`, `.env.example`, `docker-compose.yml`, `.github/workflows/ci.yml`, `.github/workflows/postgres-integration.yml`, and `.github/workflows/real-llm-integration.yml`.
- PRs #19, #20, #21, #22, #25 and #27: metadata, descriptions, relevant patches, base/head SHAs and status.
- Exact workflow-run metadata for PR #19, PR #22, post-merge main, PR #25 and the earlier PR #27 head.
- Central project index, memory map, memory policy and the reusable project-memory template.

## Evidence and findings

| Gate / source | Verified result | Scope and limitation |
|---|---|---|
| G1 / PR #19 | Merged as `e60cbef5c5ed7aa5853c481e606431b08aa07a5e`; exact tested head `b6a1751a39d0f8508d7ed970d5fd045cb34ba9a9` | Historical, bounded 85-case synthetic Qwen3 0.6B benchmark; not production reliability |
| G1 CI | [#59 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/38144847162) | Exact PR #19 head |
| G1 PostgreSQL | [#21 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/38144847168) | Exact PR #19 head |
| G1 Real LLM | [#15 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/38144847161) | Exact PR #19 head; final guarded benchmark |
| G2 / PR #22 | Merged to main at `ab1481147c33388b8a952d0b71d4e821eaecc80e` | Static hashed bearer roles for single-organization private demo only |
| G2 CI / PostgreSQL | [CI #76 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281272292); [PG #38 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281271961) | Exact PR #22 head `e78fb19e0d9c422e2b9ecfbdc604ade6d2f88e28` |
| Post-merge main | [CI SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744565); [PG SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744442) | Exact merged main SHA `ab1481147c33388b8a952d0b71d4e821eaecc80e` |
| G3 / PR #25 | Open Draft; latest checked head `d86f09224bca7449aaaa8a6bf1110d6ce793dbe3` | Not in main; owner-operated human actions and final Gate review remain |
| G3 exact-head checks | [CI #115 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096747), [PG #77 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096864), [Private Demo #38 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096835), [Real LLM #51 SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096817) | PR #25 exact head. Real LLM #51 is model-only and reported 54/85 exact; it is not a hybrid score |
| Qwen 1.7B candidate | [Run #11 FAILED](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39713790373) with ReadTimeout | Candidate not promoted |
| PR #27 | Open Draft; current head `88f8b3aa2cabf8d4f6b7c4e9a0ca65ffa70b98a0` | Proposal/documentation only. Earlier CI/PG checks were on predecessor `6ba22909d2f698a9cff8eb34ca67559a2bbab6ab`, not latest head |
| PR #20 | Open, README-only; compare is 1 ahead / 3 behind current main | Existing quick start omits required bearer-auth configuration; do not merge as-is |

G1 final guarded PR #19 metrics: 85/85 schema-valid; 71/85 exact (83.5%); product match 83/95 (87.4%); exception precision 62.9%; exception recall 78.0%; review FN 0; review precision 93.0%; review recall 100%; P95 22.42 seconds. These values apply to that exact synthetic run only. Issue #23 tracks methodology debt.

G2 residual production gaps: tenant isolation, per-user identity/audit attribution, managed token rotation/revocation, production identity, TLS/reverse proxy, rate limiting and deployment operations.

## Changes authored

- Replaced the obsolete Sprint 1 root README with a current-main implementation description, role matrix, bearer-auth-aware local start, exact gate dispositions and explicit distinction between main and Draft PR #25.
- Reconciled `docs/SECURITY_GATE.md` to state that PR #22 is merged and tests passed on the exact PR head and post-merge main, while retaining production security limitations.
- Reconciled `docs/PORTFOLIO_DELIVERY.md` G1–G4 statuses and added run links, SHA boundaries, G3 human-acceptance requirements and G4 README/portfolio blockers.
- Updated repository-local `CURRENT_STATE.md`, `OPEN_QUESTIONS.md`, and `PROJECT_PROFILE.md`.
- Added this evidence report.
- No app source, tests, migrations, benchmark corpus/scorer, CI/workflow files or PR branches were modified.

## Limitations

- Remote GitHub readback only; no local checkout, build, pytest, runtime startup, PostgreSQL process, Ollama process, or owner-operated demo was performed.
- No GitHub Actions workflow was triggered or retried.
- The historical workflow successes do not certify this documentation branch or any future release candidate.
- PR #20 was not altered or closed. Its final disposition is left for owner review.
- PR #25 and PR #27 were not modified, merged or closed.
- No pull request was opened for this documentation branch.

## Next action

Resolve whether to supersede/rebase stale PR #20 in favor of this refreshed README, then complete owner-operated G3 acceptance on Draft PR #25 after the permitted CI window. Keep release NOT APPROVED until G3/G4 and exact-candidate checks are accepted.
