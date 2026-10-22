# Private Portfolio Demo — Evidence-First Hybrid Orders (G3)

**Status:** engineering validation in PR #25. No public deployment, tag or Release. All data is synthetic.

This private, single-organization demonstration runs FastAPI, PostgreSQL 16 and Ollama through Docker Compose, with four server-owned roles and mandatory human approval. It deliberately distinguishes **reliable deterministic extraction of fully explicit SKU orders** from **LLM extraction of free-form or ambiguous messages**. A passing hybrid Demo is not evidence that Qwen accurately extracts every request.

## Extraction contract and truthful quality metrics

Two separate paths operate under the same pricing, stock and state-machine rules:

1. **Evidence-first**: a body consisting *entirely* of an explicit English order command and one or more `quantity SKU` terms (e.g. `Please send 20 PV-10.` or `We need 2 F-200 and 20 PV-10.`) is parsed deterministically. Complete-string match, distinct SKU names, explicit quantities, source-evidence validation, and catalog lookup are required. No LLM call is necessary for this narrow syntax. Unknown SKU goes to review; insufficient stock is detected by deterministic application logic.
2. **LLM fallback**: all other bodies (ambiguous quantities, generic names, extra clauses, pricing notes, instructions, multiline or unsupported syntax) go through Qwen via Ollama. The Pydantic schema and source-evidence guards remain in effect. Missing fields, invented SKU/quantity, provider failure, low confidence or other validation issues must enter human review. No invented amount or line is silently inserted.

This is an **explicit architecture change**, not a claim of improvement to Qwen's weights or its extraction accuracy. The **frozen 85-case LLM-only benchmark** still calls `LLMOrderExtractor` directly and uses its unchanged corpus, scorer and confidence threshold. It must be reported independently from these evidence-first API tests. No hybrid accuracy figure is published until a distinct, versioned, representative hybrid corpus is evaluated.

The default demo uses `qwen3:0.6b`, Ollama `think: false`, `temperature: 0`, `seed: 42`. Qwen3 1.7B thinking is a *separate unapproved candidate experiment*. Neither model reliably extracts every simple order in raw-LLM-only evaluation; fail-closed safety is not the same as high extraction quality.

## Prerequisites / deployment boundary

- Docker Engine + Compose v2 and Python 3.12+, free disk for two service images and Qwen model, CPU/RAM for local inference; internet initially to download images and the model.
- API is published on **host loopback only** at `127.0.0.1:8000`; PostgreSQL and Ollama are internal, without published host ports. Never expose to the internet.
- Containers initialize PostgreSQL, run Alembic migrations, pull the local model, then start the API after healthy dependencies. The application image runs as non-root.
- Container image tags (`postgres:16-alpine` and `ollama/ollama:latest`) are mutable; pin reviewed digests for audited release. There is no paid LLM API, production IAM or tenant isolation.
- Static digest-configured Bearer tokens are only acceptable for this local private demonstration; no customer PII or real orders.

## Set up the private environment

From the intended PR #25 working tree:

```bash
git switch feat/private-demo-runtime
git pull --ff-only
python3 scripts/setup_demo_env.py
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 1500
docker compose ps
curl -fsS http://127.0.0.1:8000/health
```

`setup_demo_env.py` creates local, private mode-0600 files: `.env` for a random database password and hashed role mapping, and `.demo-credentials.json` for separate raw test credentials. Both are ignored by Git and Docker build context. The tool never prints token values or overwrites existing files. Never paste credentials or unredacted logs into GitHub.

## Noninteractive acceptance: hybrid plus actual Ollama fallback

```bash
python3 scripts/private_demo_smoke.py submit
```

Four synthetic orders are processed via the real API:

| Case | Responsible extractor | Required result |
|---|---|---|
| `We need 2 F-200 and 20 PV-10.` | **Deterministic evidence-first** | Both exact items, trusted subtotal $1740, PV-10 stock shortage, `requires_review` |
| `Please send 20 PV-10.` | **Deterministic evidence-first** | PV-10 × 20, trusted subtotal $1500, stock 15 and `requires_review` |
| `Please send 2 F-200.` | **Deterministic evidence-first** | F-200 × 2, trusted subtotal $240, `ready_for_approval` **not approved** |
| `We need PV-10. Please confirm availability.` | **Real Ollama / LLM fallback** | No guessed quantity or priced item; `requires_review`. Provider errors are **not** accepted as a successful LLM diagnostic |

The test additionally checks unauthenticated 401, wrong-role 403 and no implicit approval. The real LLM's exact-item quality remains assessed independently by the frozen benchmark; the above fallback test is a **safety and connectivity diagnostic**, not a full model-accuracy claim.

## Persistence and fail-closed review

```bash
docker compose restart api
timeout 90 bash -c 'until curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; do sleep 2; done'
python3 scripts/private_demo_smoke.py verify
```

This re-reads all four order IDs from `.demo-smoke-state.json`. It verifies that PostgreSQL retains items, trusted pricing and statuses after API restart, the shortage cannot be directly approved (HTTP 409), forbidden operations return 403, and a reviewer acknowledging the stock-shortage order cannot promote it to ready while any validation issues remain. The ambiguous Qwen order stays under review.

There is no structured human correction endpoint yet: unresolved orders must remain blocked/rejected, never silently approved.

## Separate actual human approval step (not CI)

Only after both noninteractive phases pass:

```bash
python3 scripts/private_demo_smoke.py human
```

A **human operator** must inspect the *safe synthetic* order's ID, SKU, quantity, trusted unit price, available stock and subtotal. Only then may they type an order-specific `APPROVE <UUID>` phrase. The CLI displays a deterministic draft; a **second**, separate `RECORD SIMULATED SEND <UUID>` confirmation is required. This only writes a confirmation record: **no email is transmitted**.

Neither the GitHub runner nor the assistant should impersonate those human confirmations. Without this completed human evidence, G3 remains unaccepted even if CI is green.

## Security, limitations, teardown and release decision

- LLM cannot authorize approval, override catalog prices, stock, credentials or state transitions. Evidence-first mode has a very narrow grammar and abstains on nonmatching text.
- Static role keys have no full identity lifecycle, tenant isolation, audit attribution or managed rotation. Not suitable for a public deployment.
- Missing: robust multilingual/free-form extraction, structured correction flow, representative customer dataset, pricing decimal types, pinned image digests and external system integrations.
- Clean up **only intentionally disposable** demo resources:

```bash
docker compose down
# Optional destructive cleanup of all synthetic orders and downloaded model:
docker compose down --volumes
rm -f .env .demo-credentials.json .demo-smoke-state.json
```

Do not regenerate a new DB password against an existing PostgreSQL volume without an explicit credential-migration/reset plan. No Release or PR merge without passing final-head CI, PostgreSQL and private Compose; documenting honest LLM-only metrics; actual human sign-off; and separate explicit owner authorization.
