"""Small persistence layer for document metadata stored in local JSON.

This module intentionally stays simple so the rest of the app can swap to a
database later without changing API route logic.
"""

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from backend.app.core.config import DATA_DIR, settings

REGISTRY_PATH = DATA_DIR / "documents.json"


def _ensure_registry_file() -> None:
    """Create the registry file on first use."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.write_text("[]", encoding="utf-8")


def _read_registry() -> list[dict[str, Any]]:
    """Read registry contents defensively and recover from bad local state."""
    _ensure_registry_file()

    try:
        raw_value = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except JSONDecodeError:
        return []

    if not isinstance(raw_value, list):
        return []

    normalized_items: list[dict[str, Any]] = []
    for item in raw_value:
        if not isinstance(item, dict):
            continue
        if "company_id" not in item or not item.get("company_id"):
            item = {**item, "company_id": settings.default_company_id}
        normalized_items.append(item)

    return normalized_items


def load_documents() -> list[dict[str, Any]]:
    """Return document records newest-first for operator-facing views."""
    documents = _read_registry()
    return sorted(documents, key=lambda item: item.get("created_at", ""), reverse=True)


def save_documents(documents: list[dict[str, Any]]) -> None:
    """Persist the full registry atomically via a temp file swap."""
    _ensure_registry_file()
    temp_path = Path(f"{REGISTRY_PATH}.tmp")
    temp_path.write_text(
        json.dumps(documents, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    temp_path.replace(REGISTRY_PATH)


def add_document_record(record: dict[str, Any]) -> None:
    """Append a single document record to the registry."""
    documents = load_documents()
    documents.append(record)
    save_documents(documents)


def clear_documents() -> None:
    """Clear all stored document metadata."""
    save_documents([])


def delete_company_documents(company_id: str) -> list[dict[str, Any]]:
    """Delete and return all document records for a company."""
    documents = _read_registry()
    deleted_documents = [document for document in documents if document.get("company_id") == company_id]
    remaining_documents = [document for document in documents if document.get("company_id") != company_id]

    if deleted_documents:
        save_documents(remaining_documents)

    return deleted_documents


def delete_document_record(document_id: str, company_id: str | None = None) -> dict[str, Any] | None:
    """Delete and return the first matching record, optionally scoped to a company."""
    documents = _read_registry()
    remaining_documents = []
    deleted_document = None

    for document in documents:
        if (
            document.get("document_id") == document_id
            and deleted_document is None
            and (company_id is None or document.get("company_id") == company_id)
        ):
            deleted_document = document
            continue
        remaining_documents.append(document)

    if deleted_document is not None:
        save_documents(remaining_documents)

    return deleted_document
