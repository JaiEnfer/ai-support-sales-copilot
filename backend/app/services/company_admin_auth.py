"""Per-company admin-key hashing and signed-session helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from backend.app.core.config import settings

HASH_ITERATIONS = 120_000
TOKEN_VERSION = 1


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _token_secret() -> bytes:
    secret = settings.company_admin_token_secret or settings.admin_api_key
    if not secret:
        raise RuntimeError(
            "COMPANY_ADMIN_TOKEN_SECRET or ADMIN_API_KEY must be configured for company admin sessions."
        )
    return secret.encode("utf-8")


def hash_company_access_key(company_access_key: str) -> str:
    """Derive a slow hash for a company access key."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        company_access_key.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
    )
    return f"{HASH_ITERATIONS}${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_company_access_key(company_access_key: str, stored_hash: str | None) -> bool:
    """Validate a company access key against the stored PBKDF2 hash."""
    if not stored_hash:
        return False

    try:
        iteration_text, salt_text, digest_text = stored_hash.split("$", 2)
        iterations = int(iteration_text)
        salt = _b64url_decode(salt_text)
        expected_digest = _b64url_decode(digest_text)
    except (TypeError, ValueError):
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        company_access_key.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def create_company_admin_token(company_id: str) -> str:
    """Issue a signed bearer token for one company workspace."""
    now = int(time.time())
    payload = {
        "v": TOKEN_VERSION,
        "company_id": company_id,
        "iat": now,
        "exp": now + max(settings.company_admin_session_hours, 1) * 3600,
    }
    payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_bytes = payload_text.encode("utf-8")
    signature = hmac.new(_token_secret(), payload_bytes, hashlib.sha256).digest()
    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(signature)}"


def verify_company_admin_token(token: str, company_id: str) -> bool:
    """Validate signature, expiry, and company scope for a bearer token."""
    try:
        payload_text, signature_text = token.split(".", 1)
        payload_bytes = _b64url_decode(payload_text)
        provided_signature = _b64url_decode(signature_text)
    except ValueError:
        return False

    expected_signature = hmac.new(_token_secret(), payload_bytes, hashlib.sha256).digest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        return False

    try:
        payload: dict[str, Any] = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False

    if payload.get("v") != TOKEN_VERSION:
        return False
    if payload.get("company_id") != company_id:
        return False
    if int(payload.get("exp", 0)) < int(time.time()):
        return False
    return True
