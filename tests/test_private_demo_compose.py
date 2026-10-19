"""Static guard against accidental unauthenticated LAN exposure by Compose."""

from pathlib import Path


def test_private_compose_binds_loopback_and_requires_hashed_auth_config():
    compose = (Path(__file__).resolve().parents[1] / "docker-compose.yml").read_text()
    assert '"127.0.0.1:8000:8000"' in compose
    assert "ORDER_API_KEY_HASHES_JSON: ${ORDER_API_KEY_HASHES_JSON:?" in compose
    assert '"0.0.0.0:8000:8000"' not in compose
    assert '"8000:8000"' not in compose
