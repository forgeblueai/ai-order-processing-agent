"""Real Ollama + PostgreSQL private-demo smoke (stdlib only).

Phase 1: python scripts/private_demo_smoke.py submit
Restart API with: docker compose restart api
Phase 2: python scripts/private_demo_smoke.py verify
Optional explicit HUMAN decision on SAFE synthetic order only:
         python scripts/private_demo_smoke.py human

No automated approvals, sends, or outbound messages are performed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CREDS = ROOT / ".demo-credentials.json"
STATE = ROOT / ".demo-smoke-state.json"
HOST = "http://127.0.0.1:8000"
SHORTAGE = "We need 2 F-200 and 20 PV-10."
SAFE = "We need 2 F-200 and 3 PV-10."

EXPECTED_SHORTAGE = {
    "F-200": (2, 120.0, 80),
    "PV-10": (20, 75.0, 15),
}
EXPECTED_SAFE = {
    "F-200": (2, 120.0, 80),
    "PV-10": (3, 75.0, 15),
}


def credentials() -> dict[str, str]:
    if not CREDS.is_file():
        raise RuntimeError("Missing local credential file. Run scripts/setup_demo_env.py first.")
    tokens = json.loads(CREDS.read_text(encoding="utf-8"))
    if any(len(tokens.get(role, "")) < 32 for role in ("operator", "reviewer", "approver", "sender")):
        raise RuntimeError("Incomplete demo credentials")
    return tokens


def api_request(
    method: str,
    route: str,
    *,
    token: str | None = None,
    body: dict | None = None,
) -> tuple[int, dict | list]:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = Request(HOST + route, method=method, headers=headers, data=data)
    try:
        with urlopen(request, timeout=95) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))
    except URLError as error:
        raise RuntimeError("API not reachable at 127.0.0.1:8000; inspect docker compose ps/logs") from error


def expect_status(
    method: str, route: str, expected: int, *, token: str | None = None, body: dict | None = None
) -> dict | list:
    status, data = api_request(method, route, token=token, body=body)
    if status != expected:
        # The test data is synthetic, but never print credentials.
        raise AssertionError(f"{method} {route}: expected HTTP {expected}, got {status}; {data!r}")
    return data


def validated_lines(order: dict, expected: dict[str, tuple[int, float, int]], subtotal: float) -> None:
    actual = {item["sku"]: item for item in order["items"]}
    if len(order["items"]) != len(expected) or len(actual) != len(expected):
        # This script uses ONLY two synthetic fixtures. Log field-level evidence,
        # never bearer credentials, raw request bodies or provider response text.
        actual_pairs = sorted((item["sku"], item["quantity"]) for item in order["items"])
        issue_types = sorted({issue["type"] for issue in order["issues"]})
        label = "stock-shortage" if expected == EXPECTED_SHORTAGE else "safe"
        raise AssertionError(
            f"Unreliable {label} Qwen extraction: expected {sorted(expected)}, "
            f"got {actual_pairs}, status={order['status']}, issues={issue_types}; "
            "aborting before any approval"
        )
    for sku, (qty, price, available) in expected.items():
        assert sku in actual, f"Missing validated SKU {sku}; fail closed"
        line = actual[sku]
        assert line["quantity"] == qty, f"Unsupported/incorrect quantity for {sku}; fail closed"
        assert line["unit_price"] == price, f"Pricing invariant violated for {sku}"
        assert line["available_stock"] == available, f"Inventory invariant violated for {sku}"
    assert abs(order["subtotal"] - subtotal) < 0.0001, "Backend subtotal does not match catalog"


def load_state() -> dict[str, str]:
    if not STATE.is_file():
        raise RuntimeError("Missing smoke state. Run the 'submit' phase first.")
    data = json.loads(STATE.read_text(encoding="utf-8"))
    if not all(isinstance(data.get(key), str) for key in ("shortage", "safe")):
        raise RuntimeError("Invalid smoke state")
    return data


def submit(tokens: dict[str, str]) -> None:
    health = expect_status("GET", "/health", 200)
    assert health == {"status": "ok"}
    expect_status("GET", "/api/v1/orders", 401)
    expect_status("POST", "/api/v1/orders/process", 403, token=tokens["reviewer"],
                  body={"subject": "DENIED", "body": "We need 1 F-200."})
    expect_status("GET", "/api/v1/orders", 200, token=tokens["reviewer"])

    short = expect_status(
        "POST", "/api/v1/orders/process", 200, token=tokens["operator"],
        body={"subject": "Synthetic stock-shortage order", "body": SHORTAGE},
    )
    validated_lines(short, EXPECTED_SHORTAGE, 1740.0)
    assert short["status"] == "requires_review", "Shortage MUST require human review"
    assert any(issue["type"] == "insufficient_stock" and issue["sku"] == "PV-10"
               for issue in short["issues"]), "Inventory shortage issue missing"

    safe = expect_status(
        "POST", "/api/v1/orders/process", 200, token=tokens["operator"],
        body={"subject": "Synthetic safe order", "body": SAFE},
    )
    validated_lines(safe, EXPECTED_SAFE, 465.0)
    assert safe["status"] == "ready_for_approval", (
        "Safe order still requires review; do not bypass model safety/review guards"
    )
    state = {"shortage": short["order_id"], "safe": safe["order_id"]}
    old_mask = None
    try:
        import os
        old_mask = os.umask(0o077)
        STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        STATE.chmod(0o600)
    finally:
        if old_mask is not None:
            os.umask(old_mask)
    print("PASS: real Qwen structured extraction, deterministic pricing/stock, and review routing.")
    print("Restart only the API: docker compose restart api")
    print("Then verify persistence: python scripts/private_demo_smoke.py verify")


def verify(tokens: dict[str, str]) -> None:
    state = load_state()
    for name, order_id in state.items():
        expected = EXPECTED_SHORTAGE if name == "shortage" else EXPECTED_SAFE
        amount = 1740.0 if name == "shortage" else 465.0
        detail = expect_status("GET", f"/api/v1/orders/{order_id}", 200, token=tokens["operator"])
        validated_lines(detail, expected, amount)
        assert detail["status"] == ("requires_review" if name == "shortage" else "ready_for_approval")
        expect_status("GET", f"/api/v1/orders/{order_id}", 401)
        expect_status("GET", f"/api/v1/orders/{order_id}", 200, token=tokens["approver"])

    shortage_url = f"/api/v1/orders/{state['shortage']}"
    safe_url = f"/api/v1/orders/{state['safe']}"
    expect_status("POST", shortage_url + "/approve", 409, token=tokens["approver"])
    expect_status("POST", safe_url + "/approve", 403, token=tokens["operator"])
    expect_status("POST", safe_url + "/response/send", 403, token=tokens["approver"])
    fresh = expect_status("GET", shortage_url, 200, token=tokens["reviewer"])
    assert fresh["status"] == "requires_review", "Denied transition altered persisted shortage"
    print("PASS: PostgreSQL persistence across API restart, role isolation, and human-approval boundary.")
    print("Optionally run 'human' mode for an explicit human-controlled SAFE synthetic order flow.")


def human(tokens: dict[str, str]) -> None:
    # Do not proceed until the real model, persistence and forbidden-actions checks pass.
    verify(tokens)
    safe_id = load_state()["safe"]
    route = f"/api/v1/orders/{safe_id}"
    detail = expect_status("GET", route, 200, token=tokens["approver"])
    validated_lines(detail, EXPECTED_SAFE, 465.0)
    prompt = f"Type APPROVE {safe_id} to authorize only this validated synthetic SAFE order: "
    if input(prompt).strip() != f"APPROVE {safe_id}":
        raise SystemExit("No human approval. State unchanged.")
    approved = expect_status("POST", route + "/approve", 200, token=tokens["approver"])
    assert approved["status"] == "approved"
    draft = expect_status("POST", route + "/response/draft", 200, token=tokens["sender"])
    assert draft["status"] == "response_drafted" and draft["response_draft"]
    print("\n--- Synthetic response DRAFT (not sent to any external service) ---")
    print(draft["response_draft"])
    print("--- End draft ---\n")
    instruction = f"Type RECORD SIMULATED SEND {safe_id} to confirm LOCAL DEMO ONLY (NO email sent): "
    if input(instruction).strip() != f"RECORD SIMULATED SEND {safe_id}":
        raise SystemExit("Draft remains pending; no send confirmation recorded.")
    sent = expect_status("POST", route + "/response/send", 200, token=tokens["sender"])
    assert sent["status"] == "response_sent" and sent["response_sent_at"] is not None
    complete = expect_status("POST", route + "/complete", 200, token=tokens["sender"])
    assert complete["status"] == "completed"
    print("PASS: human-approved synthetic order completed, simulated send recorded, NO external email.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("submit", "verify", "human"))
    args = parser.parse_args()
    try:
        {"submit": submit, "verify": verify, "human": human}[args.phase](credentials())
    except (AssertionError, RuntimeError) as exc:
        print(f"DEMO GATE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
