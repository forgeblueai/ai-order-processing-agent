# Security Gate: API authentication and authorization

Status: **BLOCKED — implementation and negative tests required before release**.

## Current exposure (verified in app/api/orders.py)
The router currently has no authentication dependency. Unauthenticated callers can list/read customer order records (including message content), process orders, and invoke review, approval, rejection, response draft, send confirmation, and completion. Legal state transitions do **not** establish caller authority.

## Proposed zero-cost first release boundary
- Require an authenticated identity for every `/api/v1/orders` endpoint, including list, read and process; keep `/health` public and free of sensitive data.
- Use a server-configured credential mechanism that fails closed when credentials are absent or invalid. Do not commit tokens, accept role claims from request bodies, or log secrets.
- Bind authorization to server-side role assignments: `operator` for create/read; `reviewer` for review/ready; `approver` for approve/reject; `sender` for response/send and completion. Define draft permission explicitly.
- Ensure role checks run before database access or state transitions. Missing/invalid identity -> 401; insufficient role -> 403; no order data leaked.
- Preserve state-machine checks as a separate invariant, including 409 on invalid transitions for authorized actors.
- Add tests for anonymous and wrong-role access to **every** route, authorized happy path, missing configuration, no data mutation on denial, and no sensitive logging.
- Document that a static demo credential is not a multi-tenant production identity system; do not publish the service publicly until authorization and operational controls are validated.

## Acceptance evidence
- CI on final SHA; PostgreSQL integration; negative authorization matrix with pass/fail counts.
- End-to-end test with two distinct roles; denied approval/send attempts must not alter persisted order state.
- Security review of credential storage, comparison, rotation, auditability, and deployment exposure.

Do not merge this gate merely because documentation exists.
