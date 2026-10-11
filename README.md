# AI Order Processing Agent

[![CI](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/ci.yml)
[![PostgreSQL Integration](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/postgres-integration.yml/badge.svg)](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/postgres-integration.yml)
[![Real LLM Integration](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/real-llm-integration.yml/badge.svg)](https://github.com/forgeblueai/ai-order-processing-agent/actions/workflows/real-llm-integration.yml)

A local-first, zero-cost B2B order-processing system that combines **LLM extraction** with **deterministic business rules**, **persistent order state**, and a **human approval boundary**.

Built as a portfolio-grade example of how to use AI where it helps — understanding unstructured customer requests — without giving the model authority over pricing, inventory, approval, database state, or customer communication.

**Developed by Anis Torabi · ForgeBlue AI**

## Why this project exists

B2B orders often arrive as free-form emails or messages:

> “We need 50 F-200 and 20 PV-10.”

A useful AI system should be able to understand that text, but it should **not** be trusted to invent prices, bypass stock rules, approve an order, or send a response on its own.

This project separates those responsibilities deliberately.

```mermaid
flowchart LR
    A[Untrusted customer text] --> B[LLM structured extraction]
    B --> C[Strict Pydantic schema]
    C --> D[Deterministic validation]
    D --> E[Inventory + pricing rules]
    E --> F{Safe to continue?}
    F -- No --> G[Human review]
    F -- Yes --> H[Ready for approval]
    G --> H
    H --> I[Human approval]
    I --> J[Response draft]
    J --> K[Human-confirmed send]
    K --> L[Completed]
```

## What is implemented

- **FastAPI REST API** for order ingestion and lifecycle operations
- **Provider-neutral extraction contract** with a real local **Ollama/Qwen** adapter
- **Strict structured extraction** with confidence and clarification handling
- **Fail-closed behavior** when the model/provider fails
- **Deterministic inventory, pricing, and validation logic**
- **Explicit order state machine** with invalid-transition protection
- **SQLAlchemy persistence** with SQLite by default
- **Alembic migrations** as the database schema source of truth
- **Real PostgreSQL 16 integration testing** in GitHub Actions
- **Human-in-the-loop approval and rejection workflow**
- **Deterministic customer-response drafting**
- **Human-send boundary** before a customer response can be marked sent
- **Versioned reliability benchmark corpus** with auditable numerator/denominator metrics
- **Real Qwen benchmark execution** in GitHub Actions
- **Docker support** for the API runtime

## Safety model

The central rule is simple:

> **The model may interpret input. It does not own business authority.**

The LLM cannot directly:

- change product prices
- mutate inventory
- approve or reject an order
- write directly to the database
- bypass lifecycle transitions
- send a customer response

Provider failures and ambiguous extraction are routed to human review instead of being treated as successful automation.

## Order lifecycle

```text
received
  -> extracted
  -> validating
      -> ready_for_approval
          -> approved
              -> response_drafted
                  -> response_sent
                      -> completed
          -> rejected
      -> requires_review
          -> reviewed
              -> ready_for_approval
          -> rejected
```

Invalid transitions are rejected by deterministic application code.

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/forgeblueai/ai-order-processing-agent.git
cd ai-order-processing-agent

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure the local runtime

```bash
cp .env.example .env
```

Default configuration:

```env
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
DATABASE_URL=sqlite:///./orders.db
```

Run Ollama locally and make sure the configured model is available:

```bash
ollama pull qwen3:8b
ollama serve
```

No paid API or hosted inference service is required.

### 3. Apply database migrations

```bash
alembic upgrade head
```

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Example request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/process \
  -H 'Content-Type: application/json' \
  -d '{
    "subject": "Order Request - ABC Trading",
    "body": "We need 50 F-200 and 20 PV-10."
  }'
```

The model extracts the requested items, but deterministic code owns product lookup, stock checks, pricing, subtotal calculation, and the decision to route the order to review.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service health |
| `POST` | `/api/v1/orders/process` | Extract, validate, persist, and route an order |
| `GET` | `/api/v1/orders` | List persisted orders |
| `GET` | `/api/v1/orders/{order_id}` | Fetch one order |
| `POST` | `/api/v1/orders/{order_id}/review` | Mark a review step complete |
| `POST` | `/api/v1/orders/{order_id}/ready` | Move an order toward approval |
| `POST` | `/api/v1/orders/{order_id}/approve` | Human approval transition |
| `POST` | `/api/v1/orders/{order_id}/reject` | Human rejection transition |
| `POST` | `/api/v1/orders/{order_id}/response/draft` | Create a deterministic customer-response draft |
| `POST` | `/api/v1/orders/{order_id}/response/send` | Confirm that the response was sent |
| `POST` | `/api/v1/orders/{order_id}/complete` | Complete the order lifecycle |

## PostgreSQL

SQLite is the zero-cost local default. PostgreSQL is supported through the same repository boundary.

Example:

```bash
export DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/orders'
alembic upgrade head
```

GitHub Actions also runs a real **PostgreSQL 16** service, applies migrations, exercises persistence/lifecycle invariants, performs a downgrade, and verifies a clean re-upgrade.

## Reliability benchmark

The repository includes a versioned synthetic B2B order corpus covering:

- clean extraction cases
- ambiguity and clarification cases
- unknown products
- insufficient stock
- exception routing
- injection-like input

The benchmark reports:

- schema validity
- exact extraction accuracy
- item-level product match accuracy
- exception detection rate
- human-review rate
- mean processing time
- raw numerator/denominator counts
- per-case results

Run the deterministic benchmark tests with:

```bash
pytest -q tests/test_benchmark.py
```

The Real LLM workflow also runs the corpus against a real local Qwen model in GitHub Actions and uploads the JSON report as a workflow artifact.

> The current corpus is intentionally small and synthetic. Its measurements are useful for regression visibility, not production-grade statistical claims.

## Test and CI gates

### Unit/API suite

```bash
pytest -q
```

### PostgreSQL integration

```bash
pytest -q integration_tests/postgres_repository.py
```

### Real local-LLM smoke test

With Ollama running:

```bash
pytest -q integration_tests/real_llm_smoke.py
```

Three GitHub Actions workflows cover:

1. Python 3.12 unit/API tests
2. PostgreSQL 16 migration + persistence integration
3. Real Ollama/Qwen smoke test + benchmark execution

## Project structure

```text
app/
  ai/          provider contract, prompts, extraction, Ollama adapter
  adapters/    persistence adapters
  api/         FastAPI routes
  domain/      immutable order domain model
  ports/       repository and response-drafting boundaries
  schemas/     Pydantic contracts
  services/    deterministic business logic and lifecycle

alembic/       versioned database migrations
benchmarks/    corpus, runner, ground-truth scorer control
integration_tests/
tests/
.github/workflows/
```

## Engineering principles

- **Local-first and zero-cost by default**
- **AI for interpretation, deterministic code for authority**
- **Fail closed instead of silently guessing**
- **Human approval for consequential transitions**
- **Provider-neutral boundaries**
- **Database migrations are explicit and testable**
- **Measured reliability over demo-only happy paths**
- **No benchmark number is hard-coded to manufacture a green build**

## Current status

Active development. The repository currently includes the complete vertical slice from unstructured order intake through structured extraction, deterministic validation, persistence, human approval, response drafting, confirmed send, and reliability benchmarking.

The next improvements are focused on stronger evaluation coverage, clearer observability, security hardening, and a polished end-to-end demo.

## Contributing

Issues, technical feedback, and focused pull requests are welcome. If you find a correctness, safety, or architecture problem, please open an issue with a minimal reproduction or concrete example.

---

If this architecture is useful for your own AI automation work, consider starring the repository so you can find it again later.
