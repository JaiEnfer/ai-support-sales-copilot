from fastapi import APIRouter, UploadFile, File
from backend.app.models.schemas import UploadResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    return UploadResponse(
        filename=file.filename,
        status="received",
        message="Upload endpoint is ready. File processing will be added in the next steps."
    )