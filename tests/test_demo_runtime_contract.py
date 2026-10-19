"""G3 stack contract tests that do not require Docker/Ollama for unit CI."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts import setup_demo_env

ROOT = Path(__file__).resolve().parents[1]


def test_generate_private_credentials_once_and_never_print_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = tmp_path / ".env"
    tokens_file = tmp_path / ".demo-credentials.json"
    monkeypatch.setattr(setup_demo_env, "ENV", env)
    monkeypatch.setattr(setup_demo_env, "CREDENTIALS", tokens_file)
    setup_demo_env.main()
    assert env.stat().st_mode & 0o777 == 0o600
    assert tokens_file.stat().st_mode & 0o777 == 0o600
    tokens = json.loads(tokens_file.read_text(encoding="utf-8"))
    assert set(tokens) == {"operator", "reviewer", "approver", "sender"}
    assert len(set(tokens.values())) == 4
    assert all(len(token) >= 32 for token in tokens.values())
    text = env.read_text(encoding="utf-8")
    assert "DEMO_DB_PASSWORD=" in text
    prefix = "ORDER_API_KEY_HASHES_JSON='"
    mapping = json.loads(next(line for line in text.splitlines() if line.startswith(prefix))[len(prefix):-1])
    expected = {hashlib.sha256(token.encode()).hexdigest(): [role] for role, token in tokens.items()}
    assert mapping == expected
    assert not any(token in text for token in tokens.values())
    assert not any(token in capsys.readouterr().out for token in tokens.values())
    first = env.read_bytes()
    with pytest.raises(SystemExit, match="Not overwriting"):
        setup_demo_env.main()
    assert env.read_bytes() == first


def test_stack_has_isolated_database_and_ollama_and_gate_bootstrap() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "  postgres:" in compose
    assert "  ollama:" in compose
    assert "  model-init:" in compose
    assert "  db-migrate:" in compose
    assert "  api:" in compose
    assert "postgres-data:" in compose and "ollama-models:" in compose
    assert "service_healthy" in compose
    assert "service_completed_successfully" in compose
    assert '["alembic", "upgrade", "head"]' in compose
    assert '["pull", "qwen3:0.6b"]' in compose
    assert "OLLAMA_URL: http://ollama:11434" in compose
    assert "OLLAMA_MODEL: qwen3:0.6b" in compose
    assert '127.0.0.1:8000:8000' in compose
    assert "      - 5432:5432" not in compose
    assert "      - 11434:11434" not in compose


def test_api_image_contains_migrations_runs_nonroot_and_excludes_secrets() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "COPY --chown=10001:10001 alembic ./alembic" in dockerfile
    assert "COPY --chown=10001:10001 alembic.ini ./alembic.ini" in dockerfile
    assert "USER 10001:10001" in dockerfile
    for path in (".env", ".demo-credentials.json", ".demo-smoke-state.json"):
        assert path in dockerignore
        assert path in gitignore


@pytest.fixture
def multi_sku_order() -> dict:
    return {
        "items": [
            {"sku": "F-200", "quantity": 2, "unit_price": 120.0, "available_stock": 80},
            {"sku": "PV-10", "quantity": 20, "unit_price": 75.0, "available_stock": 15},
        ],
        "status": "requires_review",
        "issues": [{"type": "insufficient_stock", "sku": "PV-10"}],
        "subtotal": 1740.0,
    }


def test_multi_sku_complete_diagnostic_reports_full_stock_shortage(multi_sku_order: dict) -> None:
    from scripts.private_demo_smoke import validate_multi_sku_shortage

    assert validate_multi_sku_shortage(multi_sku_order) is True


def test_multi_sku_omission_passes_only_as_incomplete_blocked_review(
    multi_sku_order: dict,
) -> None:
    from scripts.private_demo_smoke import validate_multi_sku_shortage

    multi_sku_order["items"] = multi_sku_order["items"][:1]
    multi_sku_order["subtotal"] = 240.0
    multi_sku_order["issues"] = [{"type": "requires_clarification", "sku": "unknown"}]
    assert validate_multi_sku_shortage(multi_sku_order) is False


@pytest.mark.parametrize("change", ["ready", "wrong_quantity", "no_issue", "invented_product"])
def test_multi_sku_unsafe_partial_or_ready_never_passes(
    multi_sku_order: dict, change: str,
) -> None:
    from scripts.private_demo_smoke import validate_multi_sku_shortage

    multi_sku_order["items"] = multi_sku_order["items"][:1]
    multi_sku_order["subtotal"] = 240.0
    multi_sku_order["issues"] = [{"type": "requires_clarification", "sku": "unknown"}]
    if change == "ready":
        multi_sku_order["status"] = "ready_for_approval"
    elif change == "wrong_quantity":
        multi_sku_order["items"][0] = dict(multi_sku_order["items"][0], quantity=1)
    elif change == "no_issue":
        multi_sku_order["issues"] = []
    else:
        multi_sku_order["items"].append({
            "sku": "P-500", "quantity": 1, "unit_price": 850.0,
            "available_stock": 8,
        })
    with pytest.raises(AssertionError):
        validate_multi_sku_shortage(multi_sku_order)
