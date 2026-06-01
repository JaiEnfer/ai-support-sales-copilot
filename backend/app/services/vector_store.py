"""Retrieval storage helpers for both Chroma and the local fallback index.

The fallback path keeps local demos and tests usable even when embeddings or
the vector database are unavailable.
"""

from functools import lru_cache
import json
from json import JSONDecodeError
import re
from pathlib import Path
from typing import Any

from backend.app.core.config import CHROMA_DIR

COLLECTION_NAME = "documents"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
FALLBACK_INDEX_PATH = CHROMA_DIR.parent / "fallback_chunks.json"


def _empty_query_result() -> dict[str, list[list[Any]]]:
    """Mirror the Chroma query shape for callers that expect it."""
    return {"documents": [[]], "metadatas": [[]]}


def _ensure_fallback_index_exists() -> None:
    """Initialize the fallback JSON index lazily."""
    FALLBACK_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FALLBACK_INDEX_PATH.exists():
        FALLBACK_INDEX_PATH.write_text("[]", encoding="utf-8")


def _load_fallback_entries() -> list[dict[str, Any]]:
    """Load fallback entries defensively and ignore corrupted content."""
    _ensure_fallback_index_exists()
    try:
        raw_value = json.loads(FALLBACK_INDEX_PATH.read_text(encoding="utf-8"))
    except JSONDecodeError:
        return []

    if not isinstance(raw_value, list):
        return []

    return [entry for entry in raw_value if isinstance(entry, dict)]


def _save_fallback_entries(entries: list[dict[str, Any]]) -> None:
    """Persist fallback entries as readable JSON for easier debugging."""
    _ensure_fallback_index_exists()
    FALLBACK_INDEX_PATH.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _normalize_token(token: str) -> str:
    """Normalize tokens so keyword matching is deterministic."""
    return re.sub(r"[^a-z0-9]+", "", token.lower())


def _tokenize(text: str) -> list[str]:
    """Tokenize text using the same normalization as query matching."""
    return [
        normalized
        for normalized in (_normalize_token(token) for token in re.findall(r"[A-Za-z0-9]+", text))
        if normalized
    ]


def _score_entry(query_tokens: list[str], content: str, filename: str) -> int:
    """Score a fallback entry with a lightweight lexical heuristic."""
    haystack_tokens = _tokenize(f"{filename} {content}")
    if not haystack_tokens:
        return 0

    score = 0
    for token in query_tokens:
        if token in haystack_tokens:
            score += 6
            continue

        for haystack_token in haystack_tokens:
            if haystack_token.startswith(token) or token.startswith(haystack_token):
                score += 3
                break
            if len(token) >= 5 and token in haystack_token:
                score += 2
                break

    return score


def _fallback_add_document_chunks(
    document_id: str,
    company_id: str,
    filename: str,
    chunks: list[str],
) -> None:
    """Rewrite fallback entries for a document with its latest chunk set."""
    entries = [
        entry
        for entry in _load_fallback_entries()
        if entry.get("document_id") != document_id
    ]

    for index, chunk in enumerate(chunks):
        entries.append(
            {
                "document_id": document_id,
                "company_id": company_id,
                "filename": filename,
                "chunk_index": index,
                "content": chunk,
            }
        )

    _save_fallback_entries(entries)


def _fallback_delete_document_chunks(document_id: str, company_id: str | None = None) -> None:
    """Remove all fallback chunks for a document."""
    entries = [
        entry
        for entry in _load_fallback_entries()
        if not (
            entry.get("document_id") == document_id
            and (company_id is None or entry.get("company_id") == company_id)
        )
    ]
    _save_fallback_entries(entries)


def _fallback_reset_collection() -> None:
    """Reset only the fallback index state."""
    _save_fallback_entries([])


def _fallback_search_chunks(
    query: str,
    top_k: int,
    company_id: str | None = None,
) -> dict[str, list[list[Any]]]:
    """Run deterministic keyword retrieval when semantic search is unavailable."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return _empty_query_result()

    ranked_entries = sorted(
        (
            (_score_entry(query_tokens, entry["content"], entry["filename"]), entry)
            for entry in _load_fallback_entries()
            if company_id is None or entry.get("company_id") == company_id
        ),
        key=lambda item: item[0],
        reverse=True,
    )

    top_entries = [entry for score, entry in ranked_entries if score > 0][:top_k]
    if not top_entries:
        return _empty_query_result()

    return {
        "documents": [[entry["content"] for entry in top_entries]],
        "metadatas": [[
            {
                "document_id": entry["document_id"],
                "company_id": entry.get("company_id"),
                "filename": entry["filename"],
                "chunk_index": entry["chunk_index"],
            }
            for entry in top_entries
        ]],
    }


@lru_cache(maxsize=1)
def get_chroma_client():
    """Create the persistent Chroma client once per process."""
    import chromadb

    return chromadb.PersistentClient(path=str(CHROMA_DIR))


@lru_cache(maxsize=1)
def get_embedding_function():
    """Create the embedding function lazily to keep startup fast."""
    from chromadb.utils import embedding_functions

    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )


@lru_cache(maxsize=1)
def get_collection():
    """Get or create the primary semantic collection."""
    return get_chroma_client().get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )


def add_document_chunks(
    document_id: str,
    company_id: str,
    filename: str,
    chunks: list[str]
) -> int:
    """Store chunks in both fallback and semantic indexes when available."""
    ids = []
    documents = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        normalized_chunk = chunk.strip()
        if not normalized_chunk:
            continue
        ids.append(f"{document_id}-{index}")
        documents.append(normalized_chunk)
        metadatas.append({
            "document_id": document_id,
            "company_id": company_id,
            "filename": filename,
            "chunk_index": index,
        })

    if documents:
        # The fallback index is treated as the always-on local source of truth.
        _fallback_add_document_chunks(document_id, company_id, filename, chunks)

        try:
            get_collection().add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
        except Exception:
            pass

    return len(documents)


def reset_collection() -> None:
    """Clear retrieval state for tests or local resets."""
    _fallback_reset_collection()
    client = get_chroma_client()

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    get_collection.cache_clear()

    try:
        get_collection()
    except Exception:
        pass


def delete_document_chunks(document_id: str, company_id: str | None = None) -> None:
    """Delete a document from both retrieval backends."""
    _fallback_delete_document_chunks(document_id, company_id)

    try:
        where_filter: dict[str, Any] = {"document_id": document_id}
        if company_id is not None:
            where_filter["company_id"] = company_id
        get_collection().delete(where=where_filter)
    except Exception:
        return


def search_chunks(query: str, top_k: int = 4, company_id: str | None = None):
    """Search semantically first, then fall back to keyword retrieval."""
    normalized_query = query.strip()
    if not normalized_query:
        return _empty_query_result()

    top_k = max(1, top_k)

    try:
        query_payload: dict[str, Any] = {
            "query_texts": [normalized_query],
            "n_results": top_k,
        }
        if company_id is not None:
            query_payload["where"] = {"company_id": company_id}

        results = get_collection().query(**query_payload)
        if results.get("documents", [[]])[0]:
            return results
    except Exception:
        pass

    return _fallback_search_chunks(normalized_query, top_k, company_id=company_id)
