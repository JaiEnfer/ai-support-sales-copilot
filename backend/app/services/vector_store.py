from functools import lru_cache
import json
import re
from pathlib import Path
from typing import Any

from backend.app.core.config import CHROMA_DIR

COLLECTION_NAME = "documents"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
FALLBACK_INDEX_PATH = CHROMA_DIR.parent / "fallback_chunks.json"


def _empty_query_result() -> dict[str, list[list[Any]]]:
    return {"documents": [[]], "metadatas": [[]]}


def _ensure_fallback_index_exists() -> None:
    FALLBACK_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FALLBACK_INDEX_PATH.exists():
        FALLBACK_INDEX_PATH.write_text("[]", encoding="utf-8")


def _load_fallback_entries() -> list[dict[str, Any]]:
    _ensure_fallback_index_exists()
    return json.loads(FALLBACK_INDEX_PATH.read_text(encoding="utf-8"))


def _save_fallback_entries(entries: list[dict[str, Any]]) -> None:
    FALLBACK_INDEX_PATH.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _normalize_token(token: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", token.lower())


def _tokenize(text: str) -> list[str]:
    return [
        normalized
        for normalized in (_normalize_token(token) for token in re.findall(r"[A-Za-z0-9]+", text))
        if normalized
    ]


def _score_entry(query_tokens: list[str], content: str, filename: str) -> int:
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
    filename: str,
    chunks: list[str],
) -> None:
    entries = [
        entry
        for entry in _load_fallback_entries()
        if entry.get("document_id") != document_id
    ]

    for index, chunk in enumerate(chunks):
        entries.append(
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": index,
                "content": chunk,
            }
        )

    _save_fallback_entries(entries)


def _fallback_delete_document_chunks(document_id: str) -> None:
    entries = [
        entry
        for entry in _load_fallback_entries()
        if entry.get("document_id") != document_id
    ]
    _save_fallback_entries(entries)


def _fallback_reset_collection() -> None:
    _save_fallback_entries([])


def _fallback_search_chunks(query: str, top_k: int) -> dict[str, list[list[Any]]]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return _empty_query_result()

    ranked_entries = sorted(
        (
            (_score_entry(query_tokens, entry["content"], entry["filename"]), entry)
            for entry in _load_fallback_entries()
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
                "filename": entry["filename"],
                "chunk_index": entry["chunk_index"],
            }
            for entry in top_entries
        ]],
    }


@lru_cache(maxsize=1)
def get_chroma_client():
    import chromadb

    return chromadb.PersistentClient(path=str(CHROMA_DIR))


@lru_cache(maxsize=1)
def get_embedding_function():
    from chromadb.utils import embedding_functions

    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )


@lru_cache(maxsize=1)
def get_collection():
    return get_chroma_client().get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )


def add_document_chunks(
    document_id: str,
    filename: str,
    chunks: list[str]
) -> int:
    ids = []
    documents = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        ids.append(f"{document_id}-{index}")
        documents.append(chunk)
        metadatas.append({
            "document_id": document_id,
            "filename": filename,
            "chunk_index": index,
        })

    if documents:
        _fallback_add_document_chunks(document_id, filename, chunks)

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


def delete_document_chunks(document_id: str) -> None:
    _fallback_delete_document_chunks(document_id)

    try:
        get_collection().delete(where={"document_id": document_id})
    except Exception:
        return


def search_chunks(query: str, top_k: int = 4):
    if not query.strip():
        return _empty_query_result()

    try:
        results = get_collection().query(
            query_texts=[query],
            n_results=top_k
        )
        if results.get("documents", [[]])[0]:
            return results
    except Exception:
        pass

    return _fallback_search_chunks(query, top_k)
