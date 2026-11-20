# AI Order Processing Agent

**A Python/FastAPI backend for LLM-assisted B2B order processing with deterministic validation and human review.**

This project explores a safer way to process unstructured customer order requests: language models help interpret the request, while application code remains responsible for business rules, authorization, and state transitions.

## Core Workflow

```text
Unstructured customer request
            |
            v
LLM structured extraction (provider boundary)
            |
            v
Pydantic schema + source-evidence checks
            |
            v
Deterministic product, quantity, stock, and pricing validation
            |
            v
Persisted order lifecycle + role-authorized human decisions
```

## Implemented on `main`

- **LLM integration:** provider abstraction with a local Ollama structured-completion adapter.
- **Evidence-aware extraction:** Pydantic contracts and source-evidence checks that prevent unsupported product references or quantities from silently entering business processing.
- **Deterministic business logic:** product/catalog checks, stock and pricing validation, and explicit order-state transitions remain in application code.
- **Persistence:** SQLAlchemy order repository and Alembic migrations; SQLite is the default local database, with PostgreSQL integration support.
- **API authorization:** authenticated order routes with role-specific permissions for operators, reviewers, approvers, and senders.
- **Evaluation:** an 85-case synthetic corpus, benchmark runner, and measured local-model baseline. Synthetic benchmark results are not production customer metrics.

## Technology

Python · FastAPI · Pydantic · Ollama · SQLAlchemy · Alembic · SQLite · PostgreSQL · Pytest · Docker

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure DATABASE_URL, Ollama settings, and ORDER_API_KEY_HASHES_JSON
# as described in docs/SECURITY_GATE.md. Never commit plaintext tokens.
alembic upgrade head
uvicorn app.main:app --reload
```

Run the automated tests:

```bash
pytest
```

## Security and Operational Boundaries

- Model output is untrusted data. It cannot set trusted prices, inventory, roles, permissions, or approval outcomes.
- Ambiguous, unsupported, or invalid extraction must be reviewed or rejected rather than silently promoted to an approved order.
- The current bearer-token/RBAC model is a bounded application control, not enterprise identity management or multi-tenant authorization.
- The `response/send` endpoint records a human confirmation in the order lifecycle; it does **not** deliver an external email.
- The project is not presented as production-ready.

## Current Status — 2026-11-20

- Reliability improvements ([PR #19](https://github.com/forgeblueai/ai-order-processing-agent/pull/19)) and API authentication/RBAC ([PR #22](https://github.com/forgeblueai/ai-order-processing-agent/pull/22)) have been merged into `main`.
- The reproducible private API + PostgreSQL + Ollama demo is being validated in [Draft PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25). The current PR head is `ad299df42dd84f38ab113fe0c7c6fc0844b72d3f`.
- On that exact PR head, CI #120, PostgreSQL Integration #82, Private Demo Stack Integration #41, and Real LLM Integration #54 all succeeded on 2026-11-20. The Real LLM workflow completed its 85-case benchmark integrity step and uploaded the `qwen-benchmark-report` artifact.
- PR #25 remains **open, Draft, and unmerged**. Manual human acceptance is still required before G3 can be accepted; the demo is not a public release.
- The complete PostgreSQL/Ollama Compose runtime is not part of the current `main` branch.

See [the benchmark baseline](benchmarks/BASELINE_QWEN3_0.6B.md), [security gate](docs/SECURITY_GATE.md), and [portfolio delivery checklist](docs/PORTFOLIO_DELIVERY.md) for methods, limits, and status.
