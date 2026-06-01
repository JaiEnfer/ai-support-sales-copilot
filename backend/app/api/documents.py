"""Document management routes for ingestion, retrieval inspection, and cleanup."""

import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request

from backend.app.api.dependencies import (
    get_request_id,
    require_admin_api_key,
    resolve_company_id,
)
from backend.app.core.config import UPLOAD_DIR, settings
from backend.app.models.schemas import (
    UploadResponse,
    DeleteDocumentResponse,
    ClearTenantResponse,
    RetrieveRequest,
    RetrieveResponse,
    RetrievedChunk,
    DocumentListResponse,
    DocumentRecord,
    WebsiteScrapeRequest,
    WebsiteScrapeResponse,
)
from backend.app.services.document_parser import extract_text_from_pdf
from backend.app.services.chunking_service import split_text_into_chunks
from backend.app.services.vector_store import add_document_chunks, search_chunks, delete_document_chunks
from backend.app.services.document_registry import (
    add_document_record,
    delete_company_documents,
    delete_document_record,
    load_documents,
)
from backend.app.services.website_ingestion import build_website_summary, scrape_website_text

router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
    dependencies=[Depends(require_admin_api_key)],
)

SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    """Strip unsafe characters and keep only a simple storage-friendly name."""
    cleaned = SAFE_FILENAME_PATTERN.sub("-", Path(filename).name).strip(".-")
    return cleaned or "document.pdf"


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    company_id: str = Depends(resolve_company_id),
):
    """Upload a PDF, extract text, chunk it, and index it for retrieval."""
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

    # Chunking is separated so retrieval and answer generation can stay scoped.
    chunks = split_text_into_chunks(extracted_text)
    chunks_created = add_document_chunks(
        document_id=document_id,
        company_id=company_id,
        filename=safe_filename,
        chunks=chunks,
    )

    add_document_record(
        {
            "document_id": document_id,
            "company_id": company_id,
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
        company_id=company_id,
        document_id=document_id,
        chunks_created=chunks_created,
        uploaded_at=uploaded_at,
        file_size_bytes=len(file_bytes),
    )


@router.post("/scrape", response_model=WebsiteScrapeResponse)
async def scrape_website(
    request: WebsiteScrapeRequest,
    company_id: str = Depends(resolve_company_id),
):
    """Scrape a client website and index the extracted page content."""
    source_url = request.url.strip()
    if not source_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Website URL must start with http:// or https://.")

    try:
        pages = await scrape_website_text(
            source_url,
            max_pages=min(request.max_pages, settings.website_scrape_max_pages),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not scrape website: {exc.__class__.__name__}.",
        ) from exc

    if not pages:
        raise HTTPException(status_code=400, detail="No indexable HTML content found on the website.")

    uploaded_at = datetime.now(UTC).isoformat()
    document_id = str(uuid4())
    host = re.sub(r"[^A-Za-z0-9._-]+", "-", urlparse(source_url).netloc).strip(".-") or "website"
    filename = f"website-{host}.txt"
    summary_text = build_website_summary(pages)
    page_blocks = [summary_text] if summary_text else []
    page_blocks.extend(page["content"] for page in pages)
    extracted_text = "\n\n".join(page_blocks)
    chunks = split_text_into_chunks(extracted_text)
    chunks_created = add_document_chunks(
        document_id=document_id,
        company_id=company_id,
        filename=filename,
        chunks=chunks,
    )

    add_document_record(
        {
            "company_id": company_id,
            "document_id": document_id,
            "filename": filename,
            "stored_filename": None,
            "chunks_created": chunks_created,
            "created_at": uploaded_at,
            "file_size_bytes": len(extracted_text.encode("utf-8")),
            "status": "ready",
            "source_type": "website",
            "source_url": source_url,
            "pages_scraped": len(pages),
        }
    )

    return WebsiteScrapeResponse(
        document_id=document_id,
        company_id=company_id,
        status="processed",
        message="Website scraped, chunked, and stored successfully.",
        source_url=source_url,
        pages_scraped=len(pages),
        chunks_created=chunks_created,
    )


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_chunks(
    request: RetrieveRequest,
    http_request: Request,
    company_id: str = Depends(resolve_company_id),
):
    """Inspect retrieval results directly without invoking answer generation."""
    raw_results = search_chunks(request.query, request.top_k, company_id=company_id)

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
        request_id=get_request_id(http_request),
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(company_id: str = Depends(resolve_company_id)):
    """Return stored document metadata for the admin UI."""
    raw_documents = [
        document
        for document in load_documents()
        if document.get("company_id") == company_id
    ]
    documents = [DocumentRecord(**item) for item in raw_documents]
    return DocumentListResponse(documents=documents)


@router.delete("", response_model=ClearTenantResponse)
def clear_company_documents(company_id: str = Depends(resolve_company_id)):
    """Delete all documents and retrieval entries for the active tenant/company."""
    deleted_documents = delete_company_documents(company_id)

    for document in deleted_documents:
        stored_filename = document.get("stored_filename")
        if stored_filename:
            (UPLOAD_DIR / stored_filename).unlink(missing_ok=True)

        document_id = document.get("document_id")
        if document_id:
            delete_document_chunks(document_id, company_id=company_id)

    return ClearTenantResponse(
        company_id=company_id,
        deleted_documents=len(deleted_documents),
        status="cleared",
        message="All tenant documents were removed from the knowledge base.",
    )


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(document_id: str, company_id: str = Depends(resolve_company_id)):
    """Delete a document from metadata, file storage, and retrieval indexes."""
    deleted_document = delete_document_record(document_id, company_id=company_id)
    if deleted_document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    stored_filename = deleted_document.get("stored_filename")
    if stored_filename:
        (UPLOAD_DIR / stored_filename).unlink(missing_ok=True)

    delete_document_chunks(document_id, company_id=company_id)

    return DeleteDocumentResponse(
        company_id=company_id,
        document_id=document_id,
        filename=deleted_document["filename"],
        status="deleted",
        message="Document removed from the knowledge base.",
    )
