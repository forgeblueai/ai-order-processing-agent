"""Create PRIVATE local-only demo credentials; no tokens are printed or committed.

Run from any directory: python scripts/setup_demo_env.py
Creates .env (hashes + DB secret) and .demo-credentials.json (plaintext role tokens).
Both files are ignored by Git and excluded from Docker build context.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
CREDENTIALS = ROOT / ".demo-credentials.json"
ROLES = ("operator", "reviewer", "approver", "sender")


def main() -> None:
    if ENV.exists() or CREDENTIALS.exists():
        raise SystemExit(
            "Existing demo secrets detected. Not overwriting. "
            "Move/remove BOTH local files intentionally only after stopping the stack."
        )

    original_umask = os.umask(0o077)
    try:
        tokens = {role: secrets.token_urlsafe(32) for role in ROLES}
        digests = {
            hashlib.sha256(token.encode("utf-8")).hexdigest(): [role]
            for role, token in tokens.items()
        }
        password = secrets.token_hex(24)  # URL-safe for SQLAlchemy PostgreSQL DSN.
        mapping = json.dumps(digests, separators=(",", ":"))
        env_content = (
            f"DEMO_DB_PASSWORD={password}\n"
            f"ORDER_API_KEY_HASHES_JSON='{mapping}'\n"
        )
        with ENV.open("x", encoding="utf-8") as file:
            file.write(env_content)
        try:
            with CREDENTIALS.open("x", encoding="utf-8") as file:
                json.dump(tokens, file, indent=2)
                file.write("\n")
        except Exception:
            ENV.unlink(missing_ok=True)
            raise
        ENV.chmod(0o600)
        CREDENTIALS.chmod(0o600)
    finally:
        os.umask(original_umask)

    print(
        "Created private .env and .demo-credentials.json (mode 0600). "
        "No token values printed. Do not upload or share these files."
    )


if __name__ == "__main__":
    main()
