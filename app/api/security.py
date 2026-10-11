"""Fail-closed bearer-key authentication and server-owned demo RBAC.

Configure SHA-256 bearer-token digests, NEVER plaintext keys, through
ORDER_API_KEY_HASHES_JSON. This is a single-instance demo boundary, not an
enterprise identity provider; tokens must be distributed out of band.
"""

import hashlib
import hmac
import json
import os
import re
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ROLES = frozenset({"operator", "reviewer", "approver", "sender"})
_BEARER = HTTPBearer(auto_error=False)
_DIGEST = re.compile(r"[0-9a-f]{64}")


def _stored_credentials() -> dict[str, frozenset[str]]:
    """Fail closed on missing/malformed configuration. Never echo secret data."""
    try:
        value = os.environ["ORDER_API_KEY_HASHES_JSON"]
        parsed = json.loads(value)
        if not isinstance(parsed, dict) or not parsed:
            raise ValueError("empty mapping")
        mapping: dict[str, frozenset[str]] = {}
        for digest, roles in parsed.items():
            if (
                not isinstance(digest, str)
                or _DIGEST.fullmatch(digest) is None
                or not isinstance(roles, list)
                or not roles
                or not all(isinstance(role, str) and role in ROLES for role in roles)
            ):
                raise ValueError("invalid credential roles")
            mapping[digest] = frozenset(roles)
        return mapping
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="authentication unavailable") from exc


def authenticate(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER)],
) -> frozenset[str]:
    mapping = _stored_credentials()
    if credentials is None or len(credentials.credentials) < 32:
        raise HTTPException(
            status_code=401,
            detail="authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    supplied = hashlib.sha256(credentials.credentials.encode("utf-8")).hexdigest()
    matched_roles: frozenset[str] | None = None
    # A uniform comparison for each configured hash avoids easy key-prefix leakage.
    for digest, roles in mapping.items():
        if hmac.compare_digest(supplied, digest):
            matched_roles = roles
    if matched_roles is None:
        raise HTTPException(
            status_code=401,
            detail="authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return matched_roles


def require_role(role: str) -> Callable[..., frozenset[str]]:
    if role not in ROLES:
        raise ValueError("invalid server-side role")

    def check(roles: Annotated[frozenset[str], Depends(authenticate)]) -> frozenset[str]:
        if role not in roles:
            raise HTTPException(status_code=403, detail="insufficient permission")
        return roles

    return check
