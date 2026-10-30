# AI Order Processing Agent

[![CI](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/ci.yml)
[![PostgreSQL Integration](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/postgres-integration.yml/badge.svg)](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/postgres-integration.yml)

A local-first B2B order-processing API that combines structured LLM extraction with deterministic business rules, persistent order state, and human authorization boundaries.

**Developed by Anis Torabi · ForgeBlue AI**

> **Status:** active engineering / bounded private-demo candidate. Not production-ready and not approved for public deployment or release.

## Problem and design boundary

B2B orders arrive as unstructured emails or messages. The system extracts candidate products and quantities, then deterministic application code validates product references, stock, prices, order state and permissions.

**The model may interpret customer text. It does not own business authority.** Customer input and model output are untrusted. Neither may directly change price, inventory, authorization, approval, persistence, or outbound communication.

## Architecture on `main`

The current default branch includes:

- FastAPI order-processing and lifecycle API with Pydantic contracts.
- Provider-neutral extraction boundary and local Ollama/Qwen adapter.
- Fail-closed handling for provider/schema errors and uncertain extraction.
- Deterministic inventory, pricing, validation, and order lifecycle services.
- SQLAlchemy persistence adapters, SQLite local default, and Alembic migrations.
- Bearer authentication and server-owned role authorization for order endpoints.
- Synthetic reliability corpus, scorer, and benchmark evidence.
- Unit/API/security tests and a PostgreSQL integration test path.

The **strict evidence-first deterministic parser plus Ollama fallback** and the complete PostgreSQL/Ollama private demo stack are proposed in [Draft PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25). They are **not part of `main`** until that PR is reviewed and merged.

## Trust and authorization model

The LLM is an untrusted extractor, not a business authority. The server owns catalog lookup, stock, pricing, state transitions, role mapping and access control.

The current main-branch API uses `ORDER_API_KEY_HASHES_JSON`: a JSON mapping of 64-character lowercase SHA-256 bearer-token digests to one or more server-defined roles.

| Role | Mutations authorized |
|---|---|
| `operator` | Process an order |
| `reviewer` | Review an order and mark it ready for approval |
| `approver` | Approve or reject |
| `sender` | Create response draft, record human send confirmation, complete |

Any configured role can read orders in the current **single-organization private demo**. This is not tenant isolation, per-user audit attribution, or enterprise identity management. `GET /health` is public and contains no order data.

The `response/send` endpoint records a human confirmation in the workflow; it does not transmit an external email.

## Order API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Public health check |
| `POST` | `/api/v1/orders/process` | Extract, validate, persist and route an order |
| `GET` | `/api/v1/orders` | List persisted orders (authenticated) |
| `GET` | `/api/v1/orders/{order_id}` | Read an order (authenticated) |
| `POST` | `/api/v1/orders/{order_id}/review` | Reviewer action |
| `POST` | `/api/v1/orders/{order_id}/ready` | Reviewer action |
| `POST` | `/api/v1/orders/{order_id}/approve` | Approver action |
| `POST` | `/api/v1/orders/{order_id}/reject` | Approver action |
| `POST` | `/api/v1/orders/{order_id}/response/draft` | Sender action |
| `POST` | `/api/v1/orders/{order_id}/response/send` | Record human send confirmation |
| `POST` | `/api/v1/orders/{order_id}/complete` | Sender action |

Invalid state transitions are rejected by deterministic application code. An authenticated user without the required role receives `403`; missing/invalid credentials receive `401`; missing or malformed server-side auth configuration fails closed with `503`.

## Local development

The following starts the API against the configured local database. The example creates a short-lived, operator-only credential in the current shell; it is not written to the repository.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export LOCAL_OPERATOR_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ORDER_API_KEY_HASHES_JSON="$(python -c 'import hashlib,json,os; print(json.dumps({hashlib.sha256(os.environ["LOCAL_OPERATOR_TOKEN"].encode()).hexdigest(): ["operator"]}))')"

uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Submit a synthetic order:

```bash
curl --fail -X POST http://127.0.0.1:8000/api/v1/orders/process \
  -H "Authorization: Bearer ${LOCAL_OPERATOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"subject":"Synthetic order","body":"We need 2 F-200 and 20 PV-10."}'
```

For reviewer, approver and sender actions, generate separate high-entropy credentials and map each digest only to its required role. Do not commit plaintext tokens, put them in shell history, or reuse test credentials. See [SECURITY_GATE.md](docs/SECURITY_GATE.md) before running a multi-role demo.

### Database and Docker boundaries

- `DATABASE_URL` selects the database; the checked-in example defaults to SQLite.
- Alembic migrations are the schema source of truth.
- PostgreSQL 16 migration/integration checks run in GitHub Actions.
- The current root `docker-compose.yml` is an API-only local configuration, bound to `127.0.0.1:8000`; it is **not** the complete PostgreSQL + Ollama stack.
- The complete private stack and its runbook are in Draft PR #25, not merged to main.

Do not bind the API to a public interface, expose PostgreSQL/Ollama, or add a public reverse proxy based on this local setup.

## Reliability evidence and limits

The repository contains a frozen 85-case synthetic Qwen3 0.6B benchmark. PR #19's final guarded run reported 85/85 schema-valid results, 71/85 exact extractions, exception recall 78%, review recall 100%, and P95 latency 22.42 seconds. The source run, case-level caveats and artifact are recorded in [PR #19](https://github.com/forgeblueai/ai-order-processing-agent/pull/19) and [BASELINE_QWEN3_0.6B.md](benchmarks/BASELINE_QWEN3_0.6B.md).

These results are regression evidence from a bounded synthetic corpus and one model run, not a production reliability guarantee. Issue [#23](https://github.com/forgeblueai/ai-order-processing-agent/issues/23) tracks benchmark methodology debt. The later model-only run on PR #25's head reported 54/85 exact extractions; it does not measure the new hybrid parser. Do not combine model-only scores with deterministic-parser coverage or claim hybrid accuracy without a separately versioned evaluation.

## Tests and CI

Run local checks:

```bash
pytest -q
pytest -q integration_tests/postgres_repository.py
```

GitHub Actions includes Python tests, PostgreSQL migration/integration checks, and an opt-in/triggered real-LLM benchmark workflow. Historical green runs establish only the result for their exact commit; rerun and inspect evidence for any release candidate SHA.

## Current delivery gates

| Gate | Current disposition |
|---|---|
| G1 — Reliability | Accepted for a bounded private portfolio-demo candidate only; synthetic benchmark and methodology limitations remain |
| G2 — Security | Authentication/RBAC merged to main for a single-organization private demo; production identity, tenancy and deployment controls remain open |
| G3 — Reproducible private demo | Draft PR #25; stack checks passed on its exact head, but owner-operated human acceptance and final gate review remain |
| G4 — Portfolio delivery | In progress; current README refresh and release evidence require review/merge |

See [PORTFOLIO_DELIVERY.md](docs/PORTFOLIO_DELIVERY.md) for exact run links, SHA boundaries, residual work and release criteria.

## Engineering principles

- AI for interpretation; deterministic code for authority.
- Fail closed instead of silently guessing.
- Human authorization for consequential transitions.
- Synthetic data in examples and CI.
- Preserve frozen benchmark integrity; report raw denominators and failures.
- Evidence before readiness claims.
- No public release until all gates have current evidence and explicit approval.
