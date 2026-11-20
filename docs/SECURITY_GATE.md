# Security Baseline — API Authentication and Role Authorization

Status: **IMPLEMENTED ON `main`**. API authentication and role-based authorization were merged through [PR #22](https://github.com/forgeblueai/ai-order-processing-agent/pull/22) on 2026-10-19. This document describes the current main-branch baseline and its limitations; it is not a production-readiness certification.

## Verified pre-change exposure

Before PR #22, the `app/api/orders.py` router lacked authentication and authorization dependencies, allowing unauthenticated access to order data and lifecycle transitions. State-machine legality did not authenticate the caller.

## Implemented boundary on `main`

`app/api/security.py` reads server-owned `ORDER_API_KEY_HASHES_JSON`, a JSON map from **64-character lowercase SHA-256 token digests** to non-empty lists of explicit roles. Configuration is validated and digest comparisons use `hmac.compare_digest`. Plaintext bearer tokens must never be committed or written to application logs.

| Endpoint | Required role |
| --- | --- |
| POST /api/v1/orders/process | operator |
| GET /api/v1/orders and GET /api/v1/orders/{id} | Any authenticated configured role (operator, reviewer, approver, sender) |
| POST /api/v1/orders/{id}/review and /ready | reviewer |
| POST /api/v1/orders/{id}/approve and /reject | approver |
| POST /api/v1/orders/{id}/response/draft, /response/send and /complete | sender |
| GET /health | public; returns health status only |

Authentication behavior:

- Missing or malformed server-side auth configuration: **503**, fail closed.
- Missing or invalid Bearer credentials: **401**, without disclosing whether a token exists.
- Valid credentials without the required role: **403**.
- A forbidden approval or send request must not mutate the persisted order state.
- Client input cannot declare its own role; role assignments come from server-side configuration.
- The current role model permits authenticated configured roles to inspect orders so that review and approval decisions can be made. It is a single-application authorization model, **not tenant isolation or per-record authorization**.

Use independent, high-entropy tokens per role for demonstrations. Generate credentials securely, store plaintext values outside version control, and configure only their SHA-256 digests. Never commit example credentials as if they were deployment secrets.

## Current `main` deployment boundary

The `docker-compose.yml` on `main` is an API-only local configuration:

- The API host port is bound to **127.0.0.1:8000**, not a wildcard interface.
- Authentication configuration is required; missing configuration prevents a usable authenticated API.
- The main Compose file does **not** provide the complete PostgreSQL + Ollama demo stack.
- Do not expose the API through a public reverse proxy or change the host bind to `0.0.0.0` without a separate deployment-security review.

The complete private API + PostgreSQL + Ollama runtime is being validated separately in [Draft PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25). That PR remains open, Draft, and unmerged; it must not be treated as part of `main` or as a public release.

## Test coverage

The merged test suite includes:

- Anonymous and wrong-role denial across the ten order API routes.
- Missing, malformed, and invalid authentication configuration/credentials.
- Four distinct role-specific credentials for the complete review/approval lifecycle.
- Negative checks proving unauthorized approval and send requests do not change stored state.
- A Compose guard against accidental wildcard host binding or omission of required authentication configuration.

The current PR #25 head also passed its CI workflow on 2026-11-20: [CI #120](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/44697177061).

## Known limitations — not production IAM

The current bearer-token/RBAC implementation does not claim:

- Enterprise identity-provider integration or managed identity lifecycle.
- Token rotation/revocation workflows suitable for production.
- Multi-tenant isolation or per-record access policies.
- Rate limiting or abuse detection.
- Complete audit attribution and centralized security monitoring.
- Public-facing TLS/reverse-proxy deployment hardening.

These controls require separate design and validation before public or multi-tenant deployment.

## Human-action semantics

The `response/send` endpoint records a human confirmation in the order lifecycle. It does **not** send an external email. A status transition must never be described as proof of external delivery.

## Release policy

Do not publicly expose the API or describe the system as production-ready based only on the merged authentication controls. The private-demo release gate, deployment threat model, identity lifecycle, tenant model, and external communication integration remain separate concerns.
