"""Company admin provisioning and login routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import require_admin_api_key
from backend.app.models.schemas import (
    CompanyAdminLoginRequest,
    CompanyAdminProvisionRequest,
    CompanyAdminSessionResponse,
)
from backend.app.core.config import settings
from backend.app.services.company_admin_auth import (
    create_company_admin_token,
    verify_company_access_key,
)
from backend.app.services.company_profile_service import (
    get_company_profile,
    get_company_profile_record,
    set_company_access_key,
)

router = APIRouter(
    prefix="/api/company-access",
    tags=["company-access"],
)


@router.post("/login", response_model=CompanyAdminSessionResponse)
def login_company_admin(request: CompanyAdminLoginRequest):
    """Authenticate a company admin and return a scoped session token."""
    record = get_company_profile_record(request.company_id)
    stored_hash = (
        record.get("company_access_key_hash") or record.get("admin_key_hash")
        if record
        else None
    )
    if not verify_company_access_key(request.company_access_key, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid company ID or access key.",
        )

    profile = get_company_profile(request.company_id)
    expires_in_seconds = max(settings.company_admin_session_hours, 1) * 3600
    try:
        access_token = create_company_admin_token(request.company_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return CompanyAdminSessionResponse(
        company_id=request.company_id,
        access_token=access_token,
        expires_in_seconds=expires_in_seconds,
        profile=profile,
    )


@router.put("", response_model=CompanyAdminSessionResponse, dependencies=[Depends(require_admin_api_key)])
def provision_company_admin(request: CompanyAdminProvisionRequest):
    """Create or rotate a company access key using the master admin credential."""
    profile = set_company_access_key(
        request.company_id,
        request.company_access_key,
        updates={
            "display_name": request.display_name,
            "answer_mode": request.answer_mode,
            "chatbot_title": request.chatbot_title,
            "chatbot_subtitle": request.chatbot_subtitle,
        },
    )

    try:
        access_token = create_company_admin_token(request.company_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return CompanyAdminSessionResponse(
        company_id=request.company_id,
        access_token=access_token,
        expires_in_seconds=max(settings.company_admin_session_hours, 1) * 3600,
        profile=profile,
    )
