import json
from pathlib import Path
from typing import List, Dict, Any

from backend.app.core.config import DATA_DIR

REGISTRY_PATH = DATA_DIR / "documents.json"

if not REGISTRY_PATH.exists():
    REGISTRY_PATH.write_text("[]", encoding="utf-8")


def load_documents() -> List[Dict[str, Any]]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_documents(documents: List[Dict[str, Any]]) -> None:
    REGISTRY_PATH.write_text(
        json.dumps(documents, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def add_document_record(record: Dict[str, Any]) -> None:
    documents = load_documents()
    documents.append(record)
    save_documents(documents)