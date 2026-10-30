# Security Gate — API authentication and role authorization

**Status as of 2026-10-30:** authentication and role authorization are **implemented and merged on `main`** for the current single-organization private-demo API. **Production/public deployment remains NOT APPROVED.** This is a bounded static-bearer demo boundary, not enterprise IAM or a multi-tenant security design.

## 1. Previously verified exposure

Before PR #22, order routes lacked authentication and authorization dependencies. A caller could read order data and invoke lifecycle operations without proving an authorized role.

## 2. Implemented main-branch boundary

Current main SHA: `ab1481147c33388b8a952d0b71d4e821eaecc80e`.

`app/api/security.py` reads server-owned `ORDER_API_KEY_HASHES_JSON`, a JSON map from a **64-character lowercase SHA-256 token digest** to a non-empty list of explicit roles. It validates configuration and compares digests using `hmac.compare_digest`. Plaintext bearer tokens must never be stored in source control or application logs.

| Endpoint | Required role |
|---|---|
| `POST /api/v1/orders/process` | operator |
| `GET /api/v1/orders` and `GET /api/v1/orders/{id}` | Any configured authenticated role (operator, reviewer, approver, sender) |
| `POST /api/v1/orders/{id}/review` and `/ready` | reviewer |
| `POST /api/v1/orders/{id}/approve` and `/reject` | approver |
| `POST /api/v1/orders/{id}/response/draft`, `/response/send` and `/complete` | sender |
| `GET /health` | Public; contains no order data |

- Missing/malformed server auth configuration: **503 fail closed**.
- Missing/invalid Bearer credentials: **401**.
- Valid credentials without the required role: **403**.
- Unauthorized mutation must be rejected before persisted state changes.
- Authorized but invalid lifecycle transitions remain rejected by the state machine with **409**.
- Client input cannot assign its own role; role mappings are server-owned.
- Read permission is intentionally shared across the four configured roles only within the current single-organization private demo; it is not tenant isolation or per-record authorization.
- `response/send` records a human confirmation only; it does not deliver external email.

Use independent, high-entropy tokens per role for real demonstrations. Generate with `secrets.token_urlsafe(32)`, store safely outside version control, and configure only SHA-256 digests. Never reuse test credentials.

## 3. Network and local-runtime boundary

- The current main-branch `docker-compose.yml` binds the API to **127.0.0.1:8000 only**, not a wildcard host interface.
- The current main Compose file is **API-only**. It is not the complete PostgreSQL + Ollama private demo runtime.
- Compose requires `ORDER_API_KEY_HASHES_JSON` and fails configuration when it is missing.
- Uvicorn may listen on `0.0.0.0` inside a container for Docker port forwarding; the host-side published port must remain loopback-only.
- Do not expose the API publicly, publish a port, or introduce a public reverse proxy until the deployment architecture is separately reviewed for TLS, identity, auditing, secret management, abuse controls and network policy.

The complete PostgreSQL/Ollama private demo stack is proposed in [Draft PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25). Its changes are not in main until that PR is reviewed and merged.

## 4. Verification evidence

### PR #22 — exact final head

PR #22 was merged on 2026-10-19. Its exact head was `e78fb19e0d9c422e2b9ecfbdc604ade6d2f88e28`.

- [CI #76](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281272292): completed **SUCCESS**; PR description records 85 Python tests passed, 0 failures, 1 warning.
- [PostgreSQL Integration #38](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281271961): completed **SUCCESS**; PR description records migration, downgrade and re-upgrade verification.
- [PR #22](https://github.com/forgeblueai/ai-order-processing-agent/pull/22): merged into main.

### Post-merge main SHA

On merged main SHA `ab1481147c33388b8a952d0b71d4e821eaecc80e`:

- [CI push run](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744565): completed **SUCCESS**.
- [PostgreSQL Integration push run](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39285744442): completed **SUCCESS**.

These are historical checks for the exact recorded commits. They do not replace fresh release-candidate checks or prove production security.

## 5. Residual risks and production blockers

The following remain outside the current single-organization demo contract:

- no tenant isolation or per-record authorization;
- static role-token provisioning without managed rotation/revocation lifecycle;
- no individual principal identity/audit attribution for shared role credentials;
- no production identity provider or user/session lifecycle;
- no production TLS/reverse-proxy deployment configuration;
- no rate limiting or abuse controls established by this gate;
- operational secret distribution, revocation, log redaction and incident procedures require deployment-specific validation;
- complete PostgreSQL/Ollama private stack remains under Draft PR #25 and still needs owner-operated acceptance.

Before any public or production deployment, perform a separate threat-model and deployment review, verify token rotation/revocation and least privilege, establish auditable individual identity and tenant boundaries, implement TLS/network policy and rate limiting, and test secret redaction and incident response.

## 6. Release policy

Do not publicly expose the API, run a public demo, or publish a release merely because PR #22 was merged or its tests passed. G1 reliability, G3 reproducible private demo and G4 portfolio evidence must also be reconciled and accepted. Real email delivery remains out of scope; `/response/send` records human confirmation only.
