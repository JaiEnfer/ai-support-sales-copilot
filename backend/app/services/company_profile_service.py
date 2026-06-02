"""Simple per-company profile storage for answer tone and widget branding."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from backend.app.core.config import DATA_DIR, settings
from backend.app.models.schemas import CompanyProfile
from backend.app.services.company_admin_auth import hash_company_access_key

COMPANY_PROFILE_PATH = DATA_DIR / "company_profiles.json"


def _ensure_profile_store() -> None:
    COMPANY_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not COMPANY_PROFILE_PATH.exists():
        COMPANY_PROFILE_PATH.write_text("[]", encoding="utf-8")


def _read_profiles() -> list[dict[str, Any]]:
    _ensure_profile_store()
    try:
        raw_value = json.loads(COMPANY_PROFILE_PATH.read_text(encoding="utf-8"))
    except JSONDecodeError:
        return []

    if not isinstance(raw_value, list):
        return []

    return [item for item in raw_value if isinstance(item, dict)]


def _save_profiles(profiles: list[dict[str, Any]]) -> None:
    _ensure_profile_store()
    temp_path = Path(f"{COMPANY_PROFILE_PATH}.tmp")
    temp_path.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(COMPANY_PROFILE_PATH)


def get_company_profile(company_id: str) -> CompanyProfile:
    """Return a stored company profile or a sensible default profile."""
    for profile in _read_profiles():
        if profile.get("company_id") == company_id:
            return CompanyProfile(**profile)

    return CompanyProfile(
        company_id=company_id,
        display_name=company_id.replace("-", " ").title(),
        answer_mode=settings.default_answer_mode,
        chatbot_title="AI Assistant",
        chatbot_subtitle="Ask anything about this business.",
    )


def get_company_profile_record(company_id: str) -> dict[str, Any] | None:
    """Return the raw stored profile record for auth and provisioning flows."""
    for profile in _read_profiles():
        if profile.get("company_id") == company_id:
            return profile
    return None


def upsert_company_profile(company_id: str, updates: dict[str, Any]) -> CompanyProfile:
    """Create or update a company profile in the local JSON store."""
    current_profile = get_company_profile(company_id)
    updated_profile = current_profile.model_copy(
        update={key: value for key, value in updates.items() if value is not None}
    )

    profiles = _read_profiles()
    remaining = [profile for profile in profiles if profile.get("company_id") != company_id]
    remaining.append(updated_profile.model_dump())
    _save_profiles(remaining)
    return updated_profile


def set_company_access_key(
    company_id: str,
    company_access_key: str,
    updates: dict[str, Any] | None = None,
) -> CompanyProfile:
    """Provision or rotate the company access key alongside optional profile fields."""
    sanitized_updates = dict(updates or {})
    sanitized_updates["company_access_key_hash"] = hash_company_access_key(company_access_key)

    current_profile = get_company_profile(company_id)
    updated_profile = current_profile.model_copy(
        update={key: value for key, value in sanitized_updates.items() if value is not None}
    )

    profiles = _read_profiles()
    remaining = [profile for profile in profiles if profile.get("company_id") != company_id]
    raw_record = updated_profile.model_dump()
    raw_record["company_access_key_hash"] = sanitized_updates["company_access_key_hash"]
    remaining.append(raw_record)
    _save_profiles(remaining)
    return updated_profile
