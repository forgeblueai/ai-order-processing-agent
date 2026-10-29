# Decisions

Record durable architecture and workflow decisions with evidence. These entries summarize existing project constraints; they do not authorize new public exposure, release, or CI activity.

## DEC-001 — Deterministic code owns business decisions

- Status: accepted project invariant
- Decision: LLM output is untrusted extraction/candidate data. Application code owns SKU identity validation, inventory, pricing, authorization, approval, and lifecycle transitions.
- Rationale: model output may be incomplete, ambiguous, malformed, or adversarial.
- Evidence: `README.md`; `app/services/`; `app/ai/source_evidence.py`; `tests/test_extraction.py`; `docs/SECURITY_GATE.md`.
- Boundary: this record does not prove all routes, deployments, or current tests are correct.

## DEC-002 — Ambiguity and failure must not silently become approval

- Status: accepted project invariant
- Decision: uncertain/missing order information, unknown products, insufficient stock, or provider/schema failure remain reviewable or fail closed. Invalid state transitions must not mutate persisted order state.
- Evidence: `docs/SECURITY_GATE.md`; `docs/PORTFOLIO_DELIVERY.md`; `tests/test_api_auth.py`; `tests/test_order_lifecycle.py`; `tests/test_source_evidence.py`.
- Boundary: the files/tests exist in the current tree; this bootstrap did not execute the tests.

## DEC-003 — Response confirmation is not email delivery

- Status: accepted documented boundary
- Decision: a human action may record confirmation to send a response, but the demo must not imply an external email was delivered.
- Evidence: `docs/SECURITY_GATE.md` and `docs/PORTFOLIO_DELIVERY.md`.
- Boundary: real email delivery remains out of scope unless separately designed and verified.

## DEC-004 — Release requires evidence across independent gates

- Status: accepted release policy; current gate dispositions require reconciliation
- Decision: no public demo/release until security, reliability, reproducibility, and portfolio evidence have been reconciled and accepted. Do not call the system production-ready while these requirements are not established.
- Evidence: `docs/PORTFOLIO_DELIVERY.md`; current drafts [PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25) and [PR #27](https://github.com/forgeblueai/ai-order-processing-agent/pull/27).
- Boundary: this decision preserves the gate; it does not label any gate complete on its own.
