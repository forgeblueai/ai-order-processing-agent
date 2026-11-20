# Security Gate — API authentication and role authorization

Status: **G2 IMPLEMENTED AND MERGED TO MAIN** via [PR #22](https://github.com/forgeblueai/ai-order-processing-agent/pull/22).
Merge SHA: `ab1481147c33388b8a952d0b71d4e821eaecc80e`.

**Accepted scope:** a bounded, private, single-organization demonstration with loopback-only host access. This is not a production security approval, an enterprise identity provider, or a multi-tenant authorization design.

## Historical pre-G2 exposure

Before PR #22, the `app/api/orders.py` router lacked authentication and authorization dependencies. Unauthenticated callers could read stored order content and invoke order lifecycle operations. State-machine legality alone did not authenticate a caller.

That exposure was addressed by the implementation merged through PR #22.

## Implemented authorization boundary

`app/api/security.py` reads the server-owned `ORDER_API_KEY_HASHES_JSON` setting: a JSON map from **64-character lowercase SHA-256 token digests** to non-empty lists of explicit roles. Configuration is validated and digest comparisons use `hmac.compare_digest`. Bearer-token plaintext must never be committed to source control or written to application logs.

| Endpoint | Required role |
| --- | --- |
| POST /api/v1/orders/process | operator |
| GET /api/v1/orders and GET /api/v1/orders/{id} | Any authenticated configured role (operator, reviewer, approver, sender) |
| POST /api/v1/orders/{id}/review and /ready | reviewer |
| POST /api/v1/orders/{id}/approve and /reject | approver |
| POST /api/v1/orders/{id}/response/draft, /response/send and /complete | sender |
| GET /health | Public; exposes no order data |

- Missing or malformed server-side authentication configuration returns **503** (fail closed).
- Missing or invalid Bearer credentials return **401** without disclosing whether a token exists.
- Valid credentials without the required role return **403**.
- Read access is shared across the four configured roles **only within the current single-organization private demo**, so reviewers and approvers can inspect orders before taking action. This is not tenant isolation or per-record authorization.
- Only an authorized actor reaches a state-changing operation. The existing state machine continues to reject invalid transitions with **409**.
- Client input cannot assign its own role; role assignments come from server-side configuration.
- Use independent, high-entropy tokens per role for private demonstrations. Generate with `secrets.token_urlsafe(32)`, store securely outside version control, and configure only SHA-256 digests.
- For local testing, a digest can be calculated with Python `hashlib.sha256(token.encode()).hexdigest()`. Never commit example token values as deployment secrets.

## Host and container network boundary

On `main` after G2, `docker-compose.yml` binds the API host port to **127.0.0.1:8000** and requires the hashed authentication mapping. This is a local demonstration configuration, not a production reverse proxy.

The G3 work in [PR #25](https://github.com/forgeblueai/ai-order-processing-agent/pull/25) extends the private local stack with PostgreSQL and Ollama. Its runbook specifies that only the API is published on host loopback; PostgreSQL and Ollama remain internal to the Compose network and have no published host ports.

- Running Uvicorn on `0.0.0.0` **inside the API container** is required for Docker port forwarding. The security boundary is the host-side loopback-only bind.
- Do not change the host bind to `0.0.0.0`, open a public port forward, or add a public reverse proxy until TLS, identity, auditing, and deployment controls receive a separate review.
- A valid static bearer token alone is insufficient for public exposure.
- Protect the development host: environment variables and Compose configuration may be visible to local privileged users.

## G2 verification evidence

PR #22 merged to `main` at `ab1481147c33388b8a952d0b71d4e821eaecc80e`.

The checks below ran on the exact final PR head (`e78fb19e0d9c422e2b9ecfbdc604ade6d2f88e28)) before merge:

- [Python CI #76](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281272292): **SUCCESS**, 85 Python tests passed.
- [PostgreSQL Integration #38](https://github.com/forgeblueai/ai-order-processing-agent/actions/runs/39281271961): **SUCCESS**, migration upgrade, integration test, downgrade, and clean re-upgrade passed.
- Anonymous and wrong-role requests are tested across the order routes.
- Tests verify that denied approval and send-confirmation operations do not mutate persisted order state.
- The full review/approval/send-confirmation lifecycle is exercised with four separate role-specific test tokens.
- A Compose contract test prevents wildcard host binding and missing hashed-auth configuration.

These results establish the recorded G2 implementation and regression coverage for the bounded demo scope. They do not establish production readiness.

## Remaining security work before wider deployment

- Establish managed identity and token lifecycle, including rotation and revocation.
- Implement tenant isolation and per-user audit attribution.
- Add rate limiting and production-grade network controls.
- Review TLS, reverse proxy, deployment configuration, secret management, and log redaction.
- Define least-privilege credential provisioning and operational recovery.
- Revalidate the route inventory whenever endpoints or roles change.
- Do not describe static bearer keys as enterprise IAM. No managed identity lifecycle, rate limiting, or per-tenant isolation is claimed.

## Release policy

G2 being merged does **not** authorize public deployment, an external demo, or a release. The independent G1 limitations and G3 reproducibility/human-acceptance requirements remain separate gates. PR #25 must pass final-head review and its human-run acceptance procedure, and a release requires separate explicit owner authorization.

Real email delivery is out of scope. `/response/send` records a human confirmation in the workflow; it does not transmit an external email.
