# AI Order Processing Agent

Portfolio-grade B2B order processing, validation, and human-in-the-loop automation system.

**Developed by Anis Torabi — AI Automation & AI Agent Developer**  
Part of the ForgeBlue AI engineering portfolio.

## Problem

B2B orders often arrive as unstructured emails or messages. Staff must manually read the request, identify products and quantities, check inventory and pricing, handle exceptions, and prepare an order for approval.

This project demonstrates a safer automation architecture: AI is responsible for understanding unstructured input, while deterministic application code owns validation, pricing, inventory checks, and approval rules.

## Sprint 1 — Foundation

Sprint 1 establishes the deterministic core before introducing an LLM:

- FastAPI application and health endpoint
- Strict Pydantic request/response contracts
- Mock B2B product catalog and inventory
- Order processing endpoint
- Inventory validation and human-review routing
- Automated API tests
- Docker runtime

The temporary regex extractor is intentionally isolated behind the processing boundary. Sprint 2 will replace it with structured LLM extraction without moving business rules into the model.

## API

### Health

```http
GET /health
```

### Process an order

```http
POST /api/v1/orders/process
Content-Type: application/json
```

Example request:

```json
{
  "subject": "Order Request - ABC Trading",
  "body": "We need 50 F-200 and 20 PV-10."
}
```

Because only 15 units of `PV-10` are available, the order is routed to human review rather than automatically approved.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the interactive API documentation at `http://127.0.0.1:8000/docs`.

## Tests

```bash
pytest
```

## Docker

```bash
docker compose up --build
```

## Architecture principle

```text
Untrusted customer input
        ↓
Understanding / extraction
        ↓
Strict structured schema
        ↓
Deterministic validation
        ↓
Inventory + pricing rules
        ↓
Human approval / review
```

Customer text is treated as untrusted data. It cannot directly change prices, inventory, approval rules, or database state.

## Roadmap

- Sprint 2: LLM structured extraction and ambiguity handling
- Sprint 3: PostgreSQL persistence and order state machine
- Sprint 4: approval/rejection workflow and response drafting
- Sprint 5: security hardening, evaluation dataset, benchmarks, CI, and portfolio demo

## Status

🚧 Active portfolio project — Sprint 1 foundation.
