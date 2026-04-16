import chromadb
from chromadb.utils import embedding_functions
from backend.app.core.config import CHROMA_DIR

COLLECTION_NAME = "documents"

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function
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
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    return len(documents)


def reset_collection() -> None:
    global collection

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )


def delete_document_chunks(document_id: str) -> None:
    collection.delete(where={"document_id": document_id})


def search_chunks(query: str, top_k: int = 4):
    if not query.strip():
        return {"documents": [[]], "metadatas": [[]]}

    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    return results
