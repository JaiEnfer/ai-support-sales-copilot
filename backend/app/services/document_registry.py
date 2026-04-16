import json
from pathlib import Path
from typing import List, Dict, Any

from backend.app.core.config import DATA_DIR

REGISTRY_PATH = DATA_DIR / "documents.json"

if not REGISTRY_PATH.exists():
    REGISTRY_PATH.write_text("[]", encoding="utf-8")


def load_documents() -> List[Dict[str, Any]]:
    documents = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return sorted(documents, key=lambda item: item.get("created_at", ""), reverse=True)


def save_documents(documents: List[Dict[str, Any]]) -> None:
    temp_path = Path(f"{REGISTRY_PATH}.tmp")
    temp_path.write_text(
        json.dumps(documents, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    temp_path.replace(REGISTRY_PATH)


def add_document_record(record: Dict[str, Any]) -> None:
    documents = load_documents()
    documents.append(record)
    save_documents(documents)


def clear_documents() -> None:
    save_documents([])


def delete_document_record(document_id: str) -> Dict[str, Any] | None:
    documents = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    remaining_documents = []
    deleted_document = None

    for document in documents:
        if document.get("document_id") == document_id and deleted_document is None:
            deleted_document = document
            continue
        remaining_documents.append(document)

    if deleted_document is not None:
        save_documents(remaining_documents)

    return deleted_document
