# Project profile — AI Order Processing Agent

- Last reviewed: 2026-10-30
- Repository: [forgeblueai/ai-order-processing-agent](https://github.com/forgeblueai/ai-order-processing-agent)
- Visibility: public
- Default branch: `main`
- Baseline reviewed: `ab1481147c33388b8a952d0b71d4e821eaecc80e`
- Project status: active portfolio/demo engineering project; **not established as production-ready**
- Evidence boundary: the review was against GitHub's remote tree and files. A local working tree, local tests, and the full CI state were not checked in this bootstrap.

## Purpose and scope

Demonstrate B2B order processing with structured extraction and deterministic validation, inventory/pricing logic, persistence, and human review/approval boundaries. It is intended to show a safe automation architecture, not autonomous authority over business decisions.

## Architecture and stack

| Area | Verified details | Evidence / location |
|---|---|---|
| Language / runtime | Python; CI workflow configures Python 3.12 | `.github/workflows/ci.yml` |
| API | FastAPI-style application and order routes | `app/main.py`, `app/api/orders.py`, root README |
| Contracts | Pydantic request/response and extraction schemas | `app/schemas/` |
| Extraction | Provider-neutral extractor interface, Ollama provider, source-evidence support | `app/ai/` |
| Business logic | Order application service, lifecycle, inventory service | `app/services/` |
| Persistence | In-memory and SQLAlchemy repository adapters; Alembic migration files | `app/adapters/`, `alembic/` |
| Tests | Unit/API/security tests, benchmark tests, PostgreSQL integration test and real-LLM smoke test paths | `tests/`, `integration_tests/` |
| Benchmarks | Frozen 85-case Qwen3 0.6B baseline document and runner/corpus | `benchmarks/` |
| Docker | Root Compose exists; checked-in delivery document states main Compose is API-only, while the complete private demo stack is being developed in draft PR #25 | `docker-compose.yml`, [PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25) |

## Non-negotiable invariants

- Treat all customer input and all LLM-produced values as untrusted data.
- Deterministic application code, not the model, owns catalog identity, inventory, pricing, authorization, approval, and lifecycle transitions.
- Ambiguous inputs, unknown products, insufficient stock, missing information, and extraction/provider failures must remain reviewable or fail closed rather than inventing a valid order.
- Human confirmation of a draft response is not evidence that an external email was actually sent; no real email delivery is claimed by the checked-in security gate.
- Do not represent role-based demo tokens as an enterprise identity provider, individual audit attribution, tenant isolation, or production-ready access control.
- Do not expose a demo publicly until security, reliability, reproducibility, and portfolio gates have current evidence and approval.
- Use synthetic orders and test-only credentials in examples. Never commit secrets or real customer/order data.

## Important paths

| Path | Responsibility | Notes / limits |
|---|---|---|
| `app/ai/` | extraction/provider/source evidence | LLM outputs remain candidates, not trusted business decisions |
| `app/api/security.py` | bearer-token authentication and role mapping | Reviewed by path and main-commit context; this memory bootstrap did not execute security tests |
| `app/services/` | deterministic processing and order lifecycle | Current source and tests remain authoritative |
| `tests/test_api_auth.py` | authorization negative tests | Existence does not prove the current SHA passed CI |
| `benchmarks/BASELINE_QWEN3_0.6B.md` | measured model-only baseline | Do not mix these metrics with a deterministic/hybrid parser result |
| `docs/SECURITY_GATE.md` | security and exposure checklist | Status wording conflicts with merged PR #22; see CURRENT_STATE.md |
| `docs/PORTFOLIO_DELIVERY.md` | release gates and evidence checklist | Some gate statuses conflict with merged PRs; verify before making claims |

## Git, review, and CI constraints

- Keep memory bootstrap changes isolated from active application/runtime work.
- Open PRs #25 and #27 are drafts on branches based on the current main SHA as observed on 2026-10-30. They are not merged implementation/release evidence.
- PR #20 remains open but is based on older base SHA `6beed5cfb096a57cac6748516cba9db8a4da08dc`, not the current main SHA; review/rebase state before relying on it.
- CI and PostgreSQL workflows trigger on pull requests to `main`; therefore do not open a PR or initiate workflows before the explicitly deferred CI window begins (2026-11-01).
- Keep the current documentation-only bootstrap on its own branch. No application files or workflow definitions should be changed in this step.
