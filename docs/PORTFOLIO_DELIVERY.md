# Portfolio delivery checklist — AI Order Processing Agent

**Status as of 2026-10-30: IN PROGRESS — bounded private-demo candidate, NOT production-ready and NOT approved for public release.** This document tracks evidence, not promises. A merged implementation gate is not the same as a production-readiness sign-off.

## Demo acceptance contract

1. A reproducible, zero-paid-service setup starts the API, persistent database and local Ollama model, or clearly documents every manual step.
2. A user submits synthetic B2B orders and sees extraction, deterministic SKU/quantity validation, stock/price calculation and exception routing.
3. Authentication and role authorization protect order data and lifecycle mutations. Unauthorized actors cannot read sensitive orders or invoke approval, send-confirmation or completion endpoints.
4. An authorized human performs the actual review/approval actions. A CI fixture or test credential is not human acceptance evidence.
5. A human confirms a response action; the demo must not imply that an external email was delivered.
6. Tests and CI for the exact release SHA pass; real-model evidence includes model, sample count, route, limits, latency and artifact.
7. Public case-study material uses synthetic examples only and discloses limitations. No customer content, secrets or tokens are published.
8. A versioned demo release, reproducible commands, walkthrough and architecture diagram are available before release sign-off.

## Evidence and current gate dispositions

| Gate | Required evidence | Current disposition |
|---|---|---|
| **G1 Reliability** | Frozen synthetic benchmark, source-evidence safety checks, case-level regression evidence and exact-head CI/LLM/PostgreSQL results | **ACCEPTED for a bounded private portfolio-demo candidate only.** PR #19 is merged. The 85-case Qwen3 0.6B evaluation is synthetic, bounded and not a production reliability guarantee. Issue #23 tracks scorer/corpus limitations; one run is not a statistical reliability study. |
| **G2 Security** | Authentication/RBAC, negative authorization matrix, persistence non-mutation checks and network boundary | **IMPLEMENTED and MERGED on main for a single-organization private demo.** PR #22 and post-merge main CI/PostgreSQL checks passed. This does not establish enterprise IAM, tenant isolation, individual attribution or production deployment security. |
| **G3 Reproducibility** | Complete private API + PostgreSQL + Ollama stack, clean startup, migrations/persistence, real fallback and owner-operated lifecycle acceptance | **IN VALIDATION; NOT MERGED.** Draft PR #25 has passing checks on its exact head, but owner-operated human acceptance and final gate review remain. |
| **G4 Portfolio** | Accurate architecture/status README, case study, runbook, walkthrough, diagrams and versioned release evidence | **IN PROGRESS.** A refreshed README and reconciled gates are prepared on `docs/project-memory-bootstrap`; they are not yet in main. The older README PR #20 is stale and must be reworked/rebased or superseded before merge. |

## G1 — reliability evidence and limits

PR #19 merged as commit `e60cbef5c5ed7aa5853c481e606431b08aa07a5e`. Its exact tested head was `b6a1751a39d0f8508d7ed970d5fd045cb34ba9a9`.

- [CI #59](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/38144847162): completed **SUCCESS**.
- [PostgreSQL Integration #21](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/38144847168): completed **SUCCESS**.
- [Real LLM Integration #15](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/38144847161): completed **SUCCESS**; the frozen 85-case Qwen3 0.6B benchmark ran.
- Final guarded metrics in PR #19: 85/85 schema-valid; 71/85 exact extraction (83.5%); product match 83/95 (87.4%); exception precision 62.9%; exception recall 78.0%; review false negatives 0; review precision 93.0%; review recall 100%; P95 22.42 seconds.
- These numbers belong to the exact recorded synthetic run, not a production population. The corpus has repeated/related inputs, one stochastic model run is insufficient for production-scale reliability, and issue #23 records scorer omissions and corpus-format debt. The final guard had three false-positive reviews and conservative lexical evidence may over-route unusual inputs.
- Do not alter the frozen corpus/scorer/threshold to make metrics appear better. Any new hybrid parser evaluation requires an independently versioned corpus and scorer.

## G2 — security implementation evidence and limits

PR #22 merged into main as `ab1481147c33388b8a952d0b71d4e821eaecc80e`.

- Exact PR head: `e78fb19e0d9c422e2b9ecfbdc604ade6d2f88e28`.
- [CI #76](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281272292): completed **SUCCESS**; PR record reports 85 tests passed, 0 failures, 1 warning.
- [PostgreSQL Integration #38](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281271961): completed **SUCCESS**.
- Post-merge [main CI](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744565) and [main PostgreSQL Integration](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744442) both completed **SUCCESS** on the merged main SHA.
- Residual production blockers remain in [SECURITY_GATE.md](SECURITY_GATE.md): static role tokens, missing tenant isolation, no individual identity attribution, token lifecycle, production TLS/reverse proxy and rate limiting.

## G3 — private demo runtime

Draft [PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25) head on 2026-10-30: `d86f09224bca7449aaaa8a6bf1110d6ce793dbe3`.

On that exact head:

- [CI #115](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096747): **SUCCESS**, 155 Python tests, 0 failures (per PR record).
- [PostgreSQL Integration #77](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096864): **SUCCESS**.
- [Private Demo Stack Integration #38](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096835): **SUCCESS**; the record describes deterministic explicit-SKU scenarios, real Ollama fallback for ambiguous text, RBAC denials and persistence after API restart.
- [Real LLM Integration #51](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39714096817): workflow **SUCCESS**, but it measures the model-only extractor, not the hybrid route. It reported 54/85 exact extractions, 85/85 schema-valid and review FN=0; it is not a hybrid accuracy claim.
- The Qwen 1.7B candidate run [#11](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39713790373) **FAILED** with a ReadTimeout in the real-model smoke; it was not promoted.

Still required before closing G3:

1. Owner-operated clean private stack startup using locally generated credentials; no CI or assistant impersonation of a human.
2. Owner manually inspects and performs the real review/approval/draft/simulated-confirmation sequence on synthetic orders.
3. Confirm exact final PR head, all applicable checks, privacy/network boundaries and remaining acceptance criteria.
4. Update the evidence and gate status from observed results. No simulated email may be described as delivered email.

The strict deterministic parser in PR #25 is intentionally narrow and English/SKU-oriented. Free-form/multilingual inputs still depend on the raw model and review path. A separate representative hybrid benchmark is required before claiming general extraction improvements.

## G4 — portfolio and release

- The current main README still contained stale Sprint 1 wording at the reviewed baseline. This branch prepares a refreshed, auth-aware README based on current main; it is not merged yet.
- [PR #20](https://github.com/forgeblueai/ai-order-processing-agent/pull/20) is open but its head compares as **1 commit ahead / 3 behind** current main. Its README quick-start does not configure the bearer-auth environment now required by the main-branch API. Do not merge it as-is; rebase/review or supersede it.
- The current main tree does not yet contain the complete G3 runbook/stack; those are in Draft PR #25.
- Case study, owner-reviewed walkthrough, diagram and versioned demo-release evidence remain to be finalized.

## Invariants

- LLM output is untrusted data; never an authority for pricing, inventory, approval, permissions, tool execution or outbound communication.
- Unknown products, ambiguous quantities, insufficient stock and model/schema errors must fail closed into review/error handling.
- Approval, rejection, send confirmation and completion must be bound to authorized actors.
- Keep mandatory services/models usable without paid API subscriptions or hosted inference.
- Do not change benchmark labels, scorer or thresholds to conceal regressions.
- No real customer data, credentials or tokens in public examples or artifacts.

## Release decision

**NOT APPROVED** for production deployment, public demo, public exposure or tagged release at this time. Revisit only after G3 owner-operated acceptance, G4 portfolio evidence, fresh exact-release-SHA CI/integration checks and an explicit release decision.

## Release evidence template

- Release tag / SHA:
- PRs and merged SHAs:
- Python/API CI run:
- PostgreSQL integration run:
- Private-stack fresh-start run:
- Ollama smoke + benchmark run / artifact digest:
- Authentication/RBAC negative-test evidence:
- Owner-operated human-flow evidence:
- Public case study / walkthrough:
- Known limitations:
- Sign-off: **NOT APPROVED until every required gate is accepted**
