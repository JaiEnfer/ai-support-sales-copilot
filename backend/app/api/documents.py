from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.core.config import UPLOAD_DIR
from backend.app.models.schemas import UploadResponse, RetrieveRequest, RetrieveResponse, RetrievedChunk
from backend.app.services.document_parser import extract_text_from_pdf
from backend.app.services.chunking_service import split_text_into_chunks
from backend.app.services.vector_store import add_document_chunks, search_chunks

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    file_extension = Path(file.filename).suffix.lower()
    if file_extension != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported right now.")

    document_id = str(uuid4())
    saved_filename = f"{document_id}_{file.filename}"
    saved_path = UPLOAD_DIR / saved_filename

    file_bytes = await file.read()
    saved_path.write_bytes(file_bytes)

    extracted_text = extract_text_from_pdf(saved_path)

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in PDF.")

    chunks = split_text_into_chunks(extracted_text)
    chunks_created = add_document_chunks(
        document_id=document_id,
        filename=file.filename,
        chunks=chunks
    )

    return UploadResponse(
        filename=file.filename,
        status="processed",
        message="Document uploaded, parsed, chunked, and stored successfully.",
        document_id=document_id,
        chunks_created=chunks_created
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
        results=results
    )