import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.core.config import UPLOAD_DIR, settings
from backend.app.models.schemas import (
    UploadResponse,
    DeleteDocumentResponse,
    RetrieveRequest,
    RetrieveResponse,
    RetrievedChunk,
    DocumentListResponse,
    DocumentRecord,
)
from backend.app.services.document_parser import extract_text_from_pdf
from backend.app.services.chunking_service import split_text_into_chunks
from backend.app.services.vector_store import add_document_chunks, search_chunks, delete_document_chunks
from backend.app.services.document_registry import add_document_record, load_documents, delete_document_record

router = APIRouter(prefix="/api/documents", tags=["documents"])

SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    cleaned = SAFE_FILENAME_PATTERN.sub("-", Path(filename).name).strip(".-")
    return cleaned or "document.pdf"


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    file_extension = Path(file.filename).suffix.lower()
    if file_extension != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported right now.")

    uploaded_at = datetime.now(UTC).isoformat()
    safe_filename = sanitize_filename(file.filename)
    document_id = str(uuid4())
    saved_filename = f"{document_id}_{safe_filename}"
    saved_path = UPLOAD_DIR / saved_filename

    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File is too large. Maximum size is "
                f"{settings.max_upload_size_bytes // (1024 * 1024)} MB."
            ),
        )

    try:
        saved_path.write_bytes(file_bytes)
        extracted_text = extract_text_from_pdf(saved_path)
    except Exception as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Could not process PDF: {exc.__class__.__name__}.",
        ) from exc

    if not extracted_text.strip():
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="No extractable text found in PDF.")

    chunks = split_text_into_chunks(extracted_text)
    chunks_created = add_document_chunks(
        document_id=document_id,
        filename=safe_filename,
        chunks=chunks
    )

    add_document_record(
        {
            "document_id": document_id,
            "filename": safe_filename,
            "stored_filename": saved_filename,
            "chunks_created": chunks_created,
            "created_at": uploaded_at,
            "file_size_bytes": len(file_bytes),
            "status": "ready",
        }
    )

    return UploadResponse(
        filename=safe_filename,
        status="processed",
        message="Document uploaded, parsed, chunked, and stored successfully.",
        document_id=document_id,
        chunks_created=chunks_created,
        uploaded_at=uploaded_at,
        file_size_bytes=len(file_bytes),
    )


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_chunks(request: RetrieveRequest):
    raw_results = search_chunks(request.query, request.top_k)

    documents = raw_results.get("documents", [[]])[0]
    metadatas = raw_results.get("metadatas", [[]])[0]

    results = []
    for doc, metadata in zip(documents, metadatas):
        results.append(
            RetrievedChunk(
                content=doc,
                filename=metadata["filename"],
                chunk_index=metadata["chunk_index"]
            )
        )

    return RetrieveResponse(
        query=request.query,
        results=results,
        total_results=len(results),
    )


@router.get("", response_model=DocumentListResponse)
def list_documents():
    raw_documents = load_documents()
    documents = [DocumentRecord(**item) for item in raw_documents]
    return DocumentListResponse(documents=documents)


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(document_id: str):
    deleted_document = delete_document_record(document_id)
    if deleted_document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    stored_filename = deleted_document.get("stored_filename")
    if stored_filename:
        (UPLOAD_DIR / stored_filename).unlink(missing_ok=True)

    delete_document_chunks(document_id)

    return DeleteDocumentResponse(
        document_id=document_id,
        filename=deleted_document["filename"],
        status="deleted",
        message="Document removed from the knowledge base.",
    )
