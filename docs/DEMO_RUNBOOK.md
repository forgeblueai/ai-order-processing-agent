# Private portfolio demo runbook — G3

**Status: implementation in progress. Not production-ready. No public exposure or release.**

This runbook describes a **single-organization, zero-paid-service, local-only** demo of the AI Order Processing Agent, including FastAPI, PostgreSQL 16, Alembic migrations, Ollama Qwen3 0.6B, role-specific authentication, and human approval. Only synthetic order data may be used.

## Prerequisites and limits

- Docker Engine + Compose v2, Docker daemon access, Python 3.12+, sufficient free disk for two container images plus the Qwen model, and sufficient CPU/RAM for local inference. GPU is **not** required; CPU inference may take tens of seconds.
- Network access is needed **once** to download Python and container images and the local Qwen model. The application does not use a paid LLM API.
- Only port `127.0.0.1:8000` is published on the **host**. PostgreSQL and Ollama have no host port mappings. Do not forward port 8000 or connect a public reverse proxy.
- The app image is built from Python 3.12 and runs as a non-root UID; Alembic migrations execute in a separate one-shot service before API startup.
- **Version caveat:** the Docker images currently use `postgres:16-alpine` and `ollama/ollama:latest`, which are mutable tags. Freeze image digests for any audited release; this is not a production supply-chain guarantee.

## 1. Start from an approved checkout

Use the intended PR #G3 commit. **Do not demo from an unreviewed branch as though it were released.**

```bash
git switch feat/private-demo-runtime
git pull --ff-only

python3 scripts/setup_demo_env.py
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 1500
docker compose ps
curl --fail http://127.0.0.1:8000/health
```

The generator writes:
- `.env` (PostgreSQL password and **hashed** role-token mapping);
- `.demo-credentials.json` (four independent **plaintext** role tokens).

Both files are local-only, mode `0600`, excluded from Git and Docker build context. No secrets or bearer tokens should be pasted into issues, logs, screenshots, or demo videos. They are intentionally **not** printed. Running the generator again will refuse to overwrite active credentials.

The `postgres` service must become healthy before `db-migrate` runs `alembic upgrade head`. The `ollama` service must be ready before `model-init` pulls `qwen3:0.6b`. Both one-shot bootstrap services must finish successfully before the API starts.

If `docker compose up` fails, inspect `docker compose ps` first. Treat unexpected credential or raw database URL appearances in logs as potentially sensitive. Do not attach unredacted logs to public PRs.

## 2. Exercise the REAL model and negative authorization

```bash
python3 scripts/private_demo_smoke.py submit
```

This invokes the real API and Ollama provider (not a mock). It verifies:
- GET orders without Bearer token returns `401`;
- wrong-role process returns `403`;
- authenticated reviewer can view orders;
- synthetic shortage `We need 2 F-200 and 20 PV-10.` is extracted to the two exact SKUs/quantities, prices come from the fixed catalog, subtotal is `1740.00`, and `PV-10` exceeds its stock of 15, yielding `requires_review` and `insufficient_stock`;
- synthetic safe order `We need 2 F-200 and 3 PV-10.` yields fixed subtotal `465.00` and `ready_for_approval`.

If Qwen extracts the wrong SKU/quantity or requests additional review, the test **fails closed**. Do not fake or bypass it with a lower confidence threshold, altered benchmark, or forced approval. Investigate the real-model output and rerun only after an appropriate engineering decision.

## 3. Verify database persistence after API restart

```bash
docker compose restart api
python3 scripts/private_demo_smoke.py verify
```

This reads the same synthetic order IDs from `.demo-smoke-state.json`, confirms line items/prices/status survived API restart, checks unauthorized access is rejected, and proves an approver cannot bypass `requires_review` or claim a response was sent without its proper role.

The script does **not** approve, reject, send, or complete any order during unattended phases.

## 4. Optional human-controlled safe-order completion

Only after `submit` and `verify` succeed:

```bash
python3 scripts/private_demo_smoke.py human
```

A human must inspect the **safe synthetic order** and type an explicit approval phrase containing its UUID. A draft response is then generated deterministically; the human must type a second explicit phrase before the app records **SIMULATED send confirmation**. This **does not send email**. The stock-shortage order remains in `requires_review`, never silently fulfilled.

The tokens are loaded from the private local credential file; the script never prints them.

## 5. Evidence and teardown

Evidence: commit SHA, two CI results, Compose configuration validation, real-model smoke run, migration logs (redacted), statuses, persistence check, denied actions, and human-action demonstration. Use only synthetic values and redact secrets.

```bash
# Preserve the named volumes (order data/model) while stopping services:
docker compose down

# DESTRUCTIVE: delete both database and downloaded model volume when appropriate:
docker compose down --volumes
rm -f .env .demo-credentials.json .demo-smoke-state.json
```

Do not run destructive teardown until the data is intentionally disposable. **Any change to .env database password while preserving the old PostgreSQL volume may prevent connection**; either restore the previous credentials or deliberately reset disposable volumes.

## Acceptance Gate

Before a tagged demo release, require **all** of: merged Security PR #22, final-head CI, PostgreSQL migrations and integration, clean Compose startup, genuine Qwen smoke, isolated role checks, persistence proof, and a manually authorized safe-order completion. Missing evidence => G3 **BLOCKED**. Public deployment, actual external email delivery, multi-tenancy, customer PII and production IAM are **out of scope**.
