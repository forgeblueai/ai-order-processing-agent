# Security Gate — API authentication and role authorization

Status: **FIXING / VALIDATING**. These controls are implemented on this branch, not yet merged or approved for public deployment.

## Verified pre-change exposure

Before this PR, the `app/api/orders.py` router lacked authentication and authorization dependencies, allowing unauthenticated access to sensitive order content and all lifecycle transitions. State-machine legality did not authenticate the caller.

## Implemented boundary

`app/api/security.py` reads server-owned `ORDER_API_KEY_HASHES_JSON`, a JSON map from **64-character lowercase SHA-256 token digest** to a non-empty list of explicit roles. It validates configuration and compares digests using `hmac.compare_digest`. Never include bearer-token plaintext in source control or application logs.

| Endpoint | Required role |
| --- | --- |
| POST /api/v1/orders/process | operator |
| GET /api/v1/orders and GET /api/v1/orders/{id} | operator |
| POST /api/v1/orders/{id}/review and /ready | reviewer |
| POST /api/v1/orders/{id}/approve and /reject | approver |
| POST /api/v1/orders/{id}/response/draft, /response/send and /complete | sender |
| GET /health | public, no order data |

- Missing or malformed server auth configuration: **503 fail closed**.
- Missing/invalid Bearer credentials: **401**, without disclosing whether a token exists.
- Valid credentials without a required role: **403**.
- Only an authorized actor reaches the existing state machine, which still rejects invalid transitions with **409**.
- Client input cannot declare its own role; role assignments come entirely from server configuration.
- Use independent, high-entropy tokens per role for real demonstrations. Generate with `secrets.token_urlsafe(32)`, store safely outside version control, and configure only SHA-256 digests.
- In a private local testing session, calculate a digest with Python `hashlib.sha256(token.encode()).hexdigest()`. Never commit an example token as if it were a deployment secret.

## Private demo network boundary

- `docker-compose.yml` binds the API to **127.0.0.1:8000 only**, not a wildcard host interface. This is a local demo configuration, **not** a production reverse proxy or a complete database/Ollama Compose stack.
- Compose now fails at configuration time when `ORDER_API_KEY_HASHES_JSON` is missing. The container receives only SHA-256 token digests and their server-owned role mappings, not plaintext credentials.
- Running Uvicorn on `0.0.0.0` **inside the container** is required for Docker port forwarding and is not itself a public exposure; the critical control is the **host-side loopback-only port bind**. Do not change the Compose host bind to `0.0.0.0`, open a public port forward, or add a public reverse proxy until TLS, identity, auditing, and deployment controls are reviewed. A valid static token alone is insufficient for public exposure.
- Credentials must be generated securely and stored outside the repository. Environment variables and Compose configuration may be visible to local privileged users, so protect the development host.

## Tests

- `tests/test_api_auth.py`: anonymous and wrong-role access for **all ten routes**, invalid/missing configuration, invalid bearer, authenticated operator list, public health.
- `tests/test_api.py`: existing order lifecycle integration tests now use a separate all-role **test-only** fixture credential; never reuse it outside tests.
- `tests/test_api_auth.py` also verifies a complete lifecycle using **four distinct role-specific tokens**, and that a forbidden approve/send never changes stored state.
- `tests/test_private_demo_compose.py` prevents accidental wildcard port binds or omission of the required auth environment mapping.
- All token hashes and role mappings in tests are generated in-memory from deliberately non-production fixture strings.

## Before merge

- Confirm CI and PostgreSQL checks on **the final SHA**, including regression tests and negative authorization matrix.
- Verify a denied approve/send operation leaves persistent state unchanged.
- Validate token rotation/revocation, least-privilege key provisioning, audit attribution, network exposure, and log redaction for intended deployment scope.
- Review endpoint inventory whenever a new route is added; this branch protects the current ten order endpoints.
- Do not call static bearer keys an enterprise IdP or a production multi-tenant auth solution. No rate limiting, identity lifecycle, or per-tenant isolation is claimed.

## Release policy

Do not publicly expose the API, run a public Demo, or publish a portfolio release until this security gate and the independent Reliability Gate are accepted. Real email delivery is out of scope; /response/send records human confirmation only.
