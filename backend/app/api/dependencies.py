"""Reusable FastAPI dependencies for auth, tracing, and tenant context."""

from uuid import uuid4

from fastapi import Header, HTTPException, Request, status

from backend.app.core.config import settings

REQUEST_ID_HEADER = "X-Request-ID"
API_KEY_HEADER = "X-API-Key"
COMPANY_ID_HEADER = "X-Company-ID"


def get_request_id(request: Request) -> str:
    """Read the request ID assigned by middleware."""
    return getattr(request.state, "request_id", "")


def require_admin_api_key(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER)) -> None:
    """Protect admin/document routes when an admin key is configured."""
    expected_api_key = settings.admin_api_key
    if not expected_api_key:
        return
    if x_api_key == expected_api_key:
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key.",
    )


def require_chat_api_key(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER)) -> None:
    """Protect chat routes when a shared chat key is configured."""
    expected_api_key = settings.chat_api_key
    if not expected_api_key:
        return
    if x_api_key == expected_api_key:
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key.",
    )


def resolve_company_id(
    request: Request,
    x_company_id: str | None = Header(default=None, alias=COMPANY_ID_HEADER),
) -> str:
    """Resolve tenant context from headers first, then configured defaults."""
    company_id = x_company_id or getattr(request.state, "company_id", None) or settings.default_company_id
    if settings.require_company_id and not company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company ID is required.",
        )
    return company_id


def assign_request_id(request: Request) -> str:
    """Reuse a caller-supplied request ID or generate one for tracing."""
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
    request.state.request_id = request_id
    return request_id
