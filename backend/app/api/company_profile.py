"""Company profile routes for per-tenant tone and branding controls."""

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import require_company_admin_access, resolve_company_id
from backend.app.models.schemas import CompanyProfile, CompanyProfileUpdateRequest
from backend.app.services.company_profile_service import get_company_profile, upsert_company_profile

router = APIRouter(
    prefix="/api/company-profile",
    tags=["company-profile"],
    dependencies=[Depends(require_company_admin_access)],
)


@router.get("", response_model=CompanyProfile)
def read_company_profile(company_id: str = Depends(resolve_company_id)):
    """Return the profile for the active tenant/company."""
    return get_company_profile(company_id)


@router.put("", response_model=CompanyProfile)
def update_company_profile(
    request: CompanyProfileUpdateRequest,
    company_id: str = Depends(resolve_company_id),
):
    """Update tone and branding settings for the active tenant/company."""
    return upsert_company_profile(company_id, request.model_dump())
