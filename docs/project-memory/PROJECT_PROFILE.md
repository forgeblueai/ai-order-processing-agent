# Project profile — AI Order Processing Agent

- Last reviewed: 2026-10-30
- Repository: [forgeblueai/ai-order-processing-agent](https://github.com/forgeblueai/ai-order-processing-agent)
- Visibility: public
- Default branch: `main`
- Main baseline reviewed: `ab1481147c33388b8a952d0b71d4e821eaecc80e`
- Documentation branch: `docs/project-memory-bootstrap`
- Project status: active portfolio/demo engineering project; **not production-ready and not approved for public release**
- Evidence boundary: remote GitHub review only for this task; no local working-tree, local test or runtime inspection.

## Purpose and scope

Demonstrate B2B order processing with structured extraction and deterministic validation, inventory/pricing logic, persistence, and human review/approval boundaries. The model interprets untrusted text; it has no authority over business decisions.

## Architecture and stack on main

| Area | Verified details | Evidence / location |
|---|---|---|
| Language / runtime | Python; CI configures Python 3.12 | `.github/workflows/ci.yml` |
| API | FastAPI application and order routes | `app/main.py`, `app/api/orders.py` |
| Contracts | Pydantic request/response and extraction schemas | `app/schemas/` |
| Extraction | Provider-neutral extractor interface, Ollama provider, source-evidence checks | `app/ai/` |
| Business logic | Order application service, lifecycle and inventory service | `app/services/` |
| Persistence | In-memory and SQLAlchemy repository adapters; Alembic migrations | `app/adapters/`, `alembic/` |
| Security | Server-configured bearer-token SHA-256 digests and explicit operator/reviewer/approver/sender roles | `app/api/security.py` |
| Tests | Unit/API/security tests, PostgreSQL integration and real-LLM test paths | `tests/`, `integration_tests/` |
| Benchmarks | Frozen 85-case Qwen3 0.6B baseline and scorer | `benchmarks/` |
| Docker | Main Compose is API-only and host-loopback-bound; complete PostgreSQL/Ollama runtime is proposed in Draft PR #25 | `docker-compose.yml`, [PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25) |

## Non-negotiable invariants

- Treat all customer input and all LLM-produced values as untrusted data.
- Deterministic application code owns catalog identity, inventory, pricing, authorization, approval and lifecycle transitions.
- Ambiguous inputs, unknown products, insufficient stock, missing information and extraction/provider failures must remain reviewable or fail closed.
- Human confirmation of a response draft is not evidence that external email was delivered.
- Do not represent role-based demo tokens as enterprise IAM, individual audit identity, tenant isolation or production-ready access control.
- Do not expose a demo publicly until security, reliability, reproducibility and portfolio gates have current evidence and approval.
- Use synthetic orders and test-only credentials in examples. Never commit secrets or real customer/order data.

## Key source paths

| Path | Responsibility | Notes / limits |
|---|---|---|
| `app/ai/` | extraction/provider/source evidence | PR #25's evidence-first hybrid parser is not yet in main |
| `app/api/security.py` | bearer-token authentication and role mapping | PR #22 merged; see SECURITY_GATE.md for scope and residual risk |
| `app/services/` | deterministic processing and order lifecycle | Code/tests remain authoritative |
| `tests/test_api_auth.py` | authorization negative tests | Test files existing is not itself proof; exact run links are in SECURITY_GATE.md |
| `benchmarks/BASELINE_QWEN3_0.6B.md` | frozen model-only baseline | Never conflate with hybrid parser accuracy |
| `docs/SECURITY_GATE.md` | implemented private-demo auth boundary and production blockers | Reconciled on this documentation branch |
| `docs/PORTFOLIO_DELIVERY.md` | G1–G4 disposition and release criteria | Reconciled on this documentation branch |
| `docs/project-memory/` | repository-specific durable project context | This directory itself is a branch-local bootstrap pending review/merge |

## Current PR boundaries

- [PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25): Draft private runtime; exact-head checks passed, but owner-operated human acceptance remains.
- [PR #27](https://github.com/forgeblueai/ai-order-processing-agent/pull/27): Draft architecture proposal only; not implementation.
- [PR #20](https://github.com/forgeblueai/ai-order-processing-agent/pull/20): stale README refresh branch; currently behind main and omits bearer-auth setup in its quick start. Do not merge as-is.
- Keep the documentation reconciliation isolated from application/runtime work. Do not change source code, migrations, benchmark assets or workflow definitions in this task.
