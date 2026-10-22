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
SINGLE_SHORTAGE = "Please send 20 PV-10."
SAFE = "Please send 2 F-200."

EXPECTED_SHORTAGE = {
    "F-200": (2, 120.0, 80),
    "PV-10": (20, 75.0, 15),
}
EXPECTED_SINGLE_SHORTAGE = {"PV-10": (20, 75.0, 15)}
EXPECTED_SAFE = {"F-200": (2, 120.0, 80)}


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



def validate_multi_sku_shortage(order: dict) -> bool:
    """Diagnostic: complete extraction OR explicit, safely blocked partial result.

    Never call a partly extracted order fully validated. The independent
    one-SKU shortage fixture must prove real catalog stock checking.
    """
    expected = EXPECTED_SHORTAGE
    actual = order["items"]
    normalized = {item["sku"]: item for item in actual}
    if len(normalized) != len(actual):
        raise AssertionError("Duplicate product lines in multi-SKU model result")
    if not set(normalized).issubset(expected):
        raise AssertionError("Unexpected SKU in synthetic multi-SKU output")

    for sku, item in normalized.items():
        qty, price, stock = expected[sku]
        assert (item["quantity"], item["unit_price"], item["available_stock"]) == (
            qty, price, stock
        ), "Inconsistent model quantity or backend catalog value for " + sku

    assert order["status"] == "requires_review", (
        "Stock-shortage or partially extracted order cannot be ready for approval"
    )
    types = {issue["type"] for issue in order["issues"]}
    if set(normalized) == set(expected):
        assert abs(order["subtotal"] - 1740.0) < 0.0001
        assert any(
            issue["type"] == "insufficient_stock" and issue["sku"] == "PV-10"
            for issue in order["issues"]
        ), "Missing deterministic stock shortfall issue for complete extraction"
        return True

    # The missing field must remain UNRESOLVED, not silently approved.
    assert types.intersection(
        {"requires_clarification", "missing_quantity", "missing_product_reference",
         "extraction_provider_unavailable"}
    ), "Partial LLM extraction missing human-review reason"
    assert abs(
        order["subtotal"] - sum(item["quantity"] * item["unit_price"] for item in actual)
    ) < 0.0001, "Partial subtotal must only include actually validated lines"
    return False


def load_state() -> dict[str, str]:
    if not STATE.is_file():
        raise RuntimeError("Missing smoke state. Run the 'submit' phase first.")
    data = json.loads(STATE.read_text(encoding="utf-8"))
    if not all(
        isinstance(data.get(key), str)
        for key in ("multi_shortage", "single_shortage", "safe")
    ):
        raise RuntimeError("Invalid smoke state")
    return data


def submit(tokens: dict[str, str]) -> None:
    health = expect_status("GET", "/health", 200)
    assert health == {"status": "ok"}
    expect_status("GET", "/api/v1/orders", 401)
    expect_status(
        "POST", "/api/v1/orders/process", 403, token=tokens["reviewer"],
        body={"subject": "DENIED", "body": "We need 1 F-200."},
    )
    expect_status("GET", "/api/v1/orders", 200, token=tokens["reviewer"])

    multi = expect_status(
        "POST", "/api/v1/orders/process", 200, token=tokens["operator"],
        body={"subject": "Synthetic multi-SKU stock-shortage diagnostic", "body": SHORTAGE},
    )
    multi_complete = validate_multi_sku_shortage(multi)
    # A flaky two-SKU extract must NOT suppress deterministic stock validation
    # on a separate explicit one-SKU shortage input.
    single = expect_status(
        "POST", "/api/v1/orders/process", 200, token=tokens["operator"],
        body={"subject": "Synthetic single-SKU stock shortage", "body": SINGLE_SHORTAGE},
    )
    validated_lines(single, EXPECTED_SINGLE_SHORTAGE, 1500.0)
    assert single["status"] == "requires_review"
    assert any(
        issue["type"] == "insufficient_stock" and issue["sku"] == "PV-10"
        for issue in single["issues"]
    ), "Real-model single-SKU stock shortage must be caught deterministically"

    safe = expect_status(
        "POST", "/api/v1/orders/process", 200, token=tokens["operator"],
        body={"subject": "Synthetic safe order", "body": SAFE},
    )
    validated_lines(safe, EXPECTED_SAFE, 240.0)
    assert safe["status"] == "ready_for_approval"
    assert safe["issues"] == []

    state = {
        "multi_shortage": multi["order_id"],
        "single_shortage": single["order_id"],
        "safe": safe["order_id"],
    }
    old_mask = None
    try:
        import os
        old_mask = os.umask(0o077)
        STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        STATE.chmod(0o600)
    finally:
        if old_mask is not None:
            os.umask(old_mask)

    outcome = "COMPLETE" if multi_complete else "PARTIAL — HUMAN REVIEW REQUIRED"
    print(f"Multi-SKU diagnostic: {outcome}. No human approval or fulfillment performed.")
    print("PASS: real Qwen single-SKU stock shortfall, safe order, deterministic prices, RBAC.")
    print("Restart API, then run: python scripts/private_demo_smoke.py verify")


def verify(tokens: dict[str, str]) -> None:
    state = load_state()
    multi_id = state["multi_shortage"]
    multi_url = f"/api/v1/orders/{multi_id}"

    multi = expect_status("GET", multi_url, 200, token=tokens["operator"])
    # After an earlier verify() the reviewer may have acknowledged the issue.
    assert multi["status"] in ("requires_review", "reviewed")
    snapshot = multi.copy()
    snapshot["status"] = "requires_review"
    is_complete = validate_multi_sku_shortage(snapshot)

    for key, expected, amount, status in (
        ("single_shortage", EXPECTED_SINGLE_SHORTAGE, 1500.0, "requires_review"),
        ("safe", EXPECTED_SAFE, 240.0, "ready_for_approval"),
    ):
        order_id = state[key]
        url = f"/api/v1/orders/{order_id}"
        detail = expect_status("GET", url, 200, token=tokens["operator"])
        validated_lines(detail, expected, amount)
        assert detail["status"] == status
        expect_status("GET", url, 401)
        expect_status("GET", url, 200, token=tokens["approver"])

    # Two shortage variants must be blocked before approval.
    single_url = f"/api/v1/orders/{state['single_shortage']}"
    expect_status("POST", single_url + "/approve", 409, token=tokens["approver"])
    expect_status("POST", multi_url + "/approve", 409, token=tokens["approver"])
    if multi["status"] == "requires_review":
        reviewed = expect_status("POST", multi_url + "/review", 200, token=tokens["reviewer"])
        assert reviewed["status"] == "reviewed"
    expect_status("POST", multi_url + "/ready", 409, token=tokens["reviewer"])
    expect_status("POST", multi_url + "/approve", 409, token=tokens["approver"])

    safe_url = f"/api/v1/orders/{state['safe']}"
    expect_status("POST", safe_url + "/approve", 403, token=tokens["operator"])
    expect_status("POST", safe_url + "/response/send", 403, token=tokens["approver"])
    after = expect_status("GET", multi_url, 200, token=tokens["reviewer"])
    assert after["status"] == "reviewed"
    assert after["issues"] == multi["issues"], "Denied transition mutated unresolved issues"
    print(
        "PASS: PostgreSQL restart persistence, separate RBAC, and blocked review-to-ready "
        "with unresolved issues."
    )
    print("Multi-SKU extraction evidence: " + ("COMPLETE" if is_complete else "PARTIAL; BLOCKED"))
    print("Only an actual human may authorize the optional safe-order completion.")



def format_human_approval_summary(order: dict) -> str:
    """Show actual validated synthetic order facts before asking for approval.

    Do not disclose bearer tokens, customer contact info, or any LLM chain of thought.
    A reviewer must verify SKU, quantity, trusted price and stock in the terminal.
    """
    if order.get("status") != "ready_for_approval" or order.get("issues"):
        raise AssertionError("Cannot request human approval of an unresolved order")
    if not order.get("items"):
        raise AssertionError("Cannot approve an order without validated items")
    lines = [
        "PRIVATE SYNTHETIC DEMO — HUMAN APPROVAL REQUIRED",
        f"Order: {order['id']}",
        f"Status: {order['status']}",
        "Validated items (trusted catalog values):",
    ]
    for item in order["items"]:
        lines.append(
            f"  {item['sku']} x {item['quantity']} @ "
            f"${item['unit_price']:.2f} "
            f"(stock: {item['available_stock']})"
        )
    lines.append(f"Order subtotal: ${order['subtotal']:.2f}")
    lines.append("No external email will be sent by this script.")
    return "\n".join(lines)


def human(tokens: dict[str, str]) -> None:
    # Do not proceed until the real model, persistence and forbidden-actions checks pass.
    verify(tokens)
    safe_id = load_state()["safe"]
    route = f"/api/v1/orders/{safe_id}"
    detail = expect_status("GET", route, 200, token=tokens["approver"])
    validated_lines(detail, EXPECTED_SAFE, 240.0)
    print(format_human_approval_summary(detail))
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
