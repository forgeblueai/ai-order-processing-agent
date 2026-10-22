# Portfolio delivery checklist — AI Order Processing Agent

Status: **IN PROGRESS — not production-ready**. This document tracks evidence, not promises.

## Demo acceptance contract

1. A reproducible, zero-paid-service setup starts the API, persistent database, and a local Ollama model, or clearly documents any manual steps.
2. A user submits a sample B2B order and sees structured extraction, deterministic SKU/quantity validation, stock and price calculation, and exception routing.
3. A **properly authenticated and authorized** reviewer can approve or reject. Unauthorized callers cannot read sensitive orders or invoke approval, send confirmation, or completion endpoints.
4. An authorized human confirms sending a response; the demo must not imply that an external email was actually sent.
5. Tests and CI for the exact release SHA pass, and real-model benchmark evidence is attached with sample count, model, limits, and latency.
6. The public case study contains only synthetic examples and discloses limitations. No customer content, secrets, or tokens are published.
7. A versioned release, reproducible commands, short walkthrough, and architecture diagram are available.

## Evidence and current blockers

| Gate | Required evidence | Current disposition |
| --- | --- | --- |
| G1 Reliability | PR #19 benchmark on 85 synthetic cases, triple CI, fail-closed extraction evidence | **MERGED** via PR #19, merge SHA `e60cbef5c5ed7aa5853c481e606431b08aa07a5e`; benchmark v2 debt tracked in issue #23 |
| G2 Security | Authenticated roles; denied-action tests; CI #76 / PostgreSQL #38 | **MERGED** via PR #22, merge SHA `ab1481147c33388b8a952d0b71d4e821eaecc80e`. Demo-private, not production IAM |
| G3 Reproducibility | Full private Compose, Qwen3:0.6b, Alembic, real-model smoke and persistence | **IMPLEMENTING** on `feat/private-demo-runtime`; see issue #24 and `docs/DEMO_RUNBOOK.md`. No clean-stack proof yet |
| G4 Portfolio | Accurate README, case study, walkthrough, release evidence | **BLOCKED** until G3 passes; README and versioned release remain unfinished |

## Invariants

- LLM output is **untrusted data**; never an authority for pricing, inventory, approval, permissions, tool execution, or sending.
- Unknown products, ambiguous quantities, insufficient stock, and model/schema errors must fail closed into review/error handling.
- Approval, rejection, send confirmation, and completion must be bound to authenticated authorized actors before public exposure.
- All mandatory services, models, and CI must remain usable without paid subscriptions or API credits.
- No benchmark thresholds, corpus labels, or scorer logic may be changed to make a regression disappear.

## Delivery sequence

1. Resolve G1 on its existing branch and merge only after final-head CI and evidence review.
2. Implement G2 in an isolated PR with authorization regression tests.
3. Implement G3 in an isolated PR, testing fresh startup and demo workflow.
4. Finish G4 and publish a tagged **demo** release, clearly distinct from production readiness.

## Demonstration scenario

Use synthetic order: `We need 2 F-200 and 20 PV-10.` The stock shortfall for PV-10 should route the order for human review. Show the deterministic decision and an authorized human action. A second, safe order may demonstrate the normal path. Never present a draft or recorded send confirmation as a delivered external email.

## Release evidence template

- Release tag / SHA:
- PRs and merged SHAs:
- Python/API CI run:
- PostgreSQL integration run:
- Ollama smoke + benchmark run / artifact digest:
- Authentication/RBAC negative test counts:
- Clean-stack startup and persistence verification:
- Demo video / screenshots:
- Known limitations:
- Sign-off: NOT APPROVED until all gates complete
