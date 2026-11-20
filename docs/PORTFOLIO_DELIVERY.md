# Portfolio Delivery Checklist — AI Order Processing Agent

Status: **IN PROGRESS — automated private-demo checks pass; manual acceptance and release review remain open.** This document tracks observed evidence, not promises.

## Demo acceptance contract

1. A reproducible, zero-paid-service setup starts the API, persistent database, and local Ollama model, with setup steps documented.
2. A user submits a synthetic B2B order and can inspect structured extraction, deterministic SKU/quantity validation, stock/pricing calculation, and exception routing.
3. An authenticated and role-authorized reviewer/approver can complete the permitted workflow. Unauthorized callers cannot read order data or perform protected lifecycle actions.
4. A human explicitly confirms the response-sent state. The demo must not imply that an external email was actually delivered.
5. CI, PostgreSQL integration, private-demo integration, and real-model evidence are checked on the exact candidate SHA. Benchmark reports must identify the model, corpus, scope, limitations, and artifact.
6. The public case study uses only synthetic examples and discloses limitations. No customer content, credentials, or private operational data are published.
7. A versioned demo release, reproducible commands, short walkthrough, and architecture diagram are available before calling the portfolio demo complete.

## Evidence and gate status — 2026-11-20

| Gate | Required evidence | Current disposition |
| --- | --- | --- |
| G1 Reliability | Benchmark integrity, regression tests, review/exception behavior, and evidence-backed evaluation | **MERGED into `main`** via [PR #19](https://github.com/forgeblueai/ai-order-processing-agent/pull/19) on 2026-10-19 |
| G2 Security | Authentication, role authorization, negative access tests, and no unauthorized state mutation | **MERGED into `main`** via [PR #22](https://github.com/forgeblueai/ai-order-processing-agent/pull/22) on 2026-10-19 |
| G3 Reproducible private demo | Fresh API + PostgreSQL + Ollama startup, real-model smoke, RBAC negatives, persistence after API restart | **AUTOMATED CHECKS PASS; MANUAL HUMAN ACCEPTANCE PENDING** in [Draft PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25) |
| G4 Portfolio release | Accurate documentation, architecture diagram, walkthrough, versioned demo release, known limitations | **IN PROGRESS**; not a public demo release |

### G1/G2 merge evidence

- Reliability PR #19 merged to `main` on 2026-10-19.
- Security/RBAC PR #22 merged to `main` on 2026-10-19; merge commit is `ab1481147c33388b8a952d0b71d4e821eaecc80e`.
- Main-branch CI and PostgreSQL integration passed on that exact merge commit: [CI](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744565) · [PostgreSQL Integration](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744442).

### G3 current-head evidence

All four workflows below ran against the same PR #25 head, `ad299df42dd84f38ab113fe0c7c6fc0844b72d3f`, on 2026-11-20:

- [CI #120 — SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/44697177061): 155 Python tests passed; the private Compose configuration contract was validated.
- [PostgreSQL Integration #82 — SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/44697177065): migration upgrade, integration test, downgrade, and clean re-upgrade passed.
- [Private Demo Stack Integration #41 — SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/44697177103): fresh Compose stack, real-Qwen smoke, negative RBAC checks, API restart, PostgreSQL persistence verification, and ephemeral-resource cleanup passed.
- [Real LLM Integration #54 — SUCCESS](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/44697177068): real-model smoke, 85-case benchmark, benchmark safety-integrity step, and report upload passed. Artifact: `qwen-benchmark-report`; SHA-256 `7cd675f29dc206b7a373209e63639e6176bb7f8c079d20b23eb5c59b8e48cbb9`.

These are automated checks on the PR head. They do not replace a real human acceptance walkthrough and do not make PR #25 merged.

## Remaining G3 acceptance

A human operator must still follow the `human` procedure in `docs/DEMO_RUNBOOK.md`:

1. Start the private stack using the documented local setup.
2. Inspect a safe synthetic order's ID, SKU, quantity, trusted price, available stock, and subtotal.
3. Enter the order-specific approval phrase after reviewing the order.
4. Confirm the simulated-send step, understanding that no external email is transmitted.
5. Record the acceptance result without exposing credentials or customer data.

CI cannot impersonate or replace this human acceptance. After the walkthrough, review the exact PR head, all checks, benchmark artifact, and residual limitations. G3 remains pending until that evidence is recorded.

## Invariants and limitations

- LLM output is untrusted data; it cannot grant permissions, set trusted prices/inventory, approve orders, or trigger external actions by itself.
- Unknown SKUs, missing quantities, ambiguous syntax, provider failures, and unresolved review issues must fail closed into review/error handling.
- The hybrid demo's deterministic parser is intentionally narrow, English-only, single-line, and SKU-first. It is not a general multilingual extraction system.
- The 85-case Qwen benchmark is synthetic and model-only; deterministic parser behavior must not be attributed to Qwen. It is not production customer-workload evidence.
- The current bearer-token/RBAC model is not enterprise IAM or multi-tenant authorization.
- `response/send` records a human confirmation only; it does not deliver external email.
- The project is not production-ready and must not be publicly exposed as a live service.

## Release sequence

1. G1 and G2 are merged and documented on `main`.
2. Complete and record the manual G3 human-acceptance walkthrough.
3. Review the exact PR #25 head, benchmark artifact, and all limitations.
4. Obtain explicit owner approval before merging PR #25 or creating a tagged demo release.
5. Publish the public case study only after the demo release is accepted; distinguish a bounded demo from production readiness.

## Release evidence record

- Main SHA: `ab1481147c33388b8a952d0b71d4e821eaecc80e`
- Candidate PR: [#25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25)
- Candidate SHA: `ad299df42dd84f38ab113fe0c7c6fc0844b72d3f`
- CI: [#120](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/44697177061) — SUCCESS
- PostgreSQL: [#82](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/44697177065) — SUCCESS
- Private demo: [#41](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/44697177103) — SUCCESS
- Real LLM: [#54](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/44697177068) — SUCCESS
- Human acceptance evidence: **PENDING**
- Versioned demo release: **NOT CREATED**
- Public exposure: **NOT APPROVED**
